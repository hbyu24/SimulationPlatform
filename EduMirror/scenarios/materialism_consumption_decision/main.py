from datetime import datetime
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from concordia.environment.engines.sequential import Sequential
from concordia.typing import scene as scene_lib
from concordia.typing import entity as entity_lib
from common.simulation_utils.model_setup import create_language_model, create_simple_embedder, create_model_config_from_environment
from common.simulation_utils.scene_builder import SceneBuilder
from scenarios.materialism_consumption_decision.agents import create_agents, AGENT_MEMORIES
from common.measurement import EduMirrorSurveyor
from common.measurement.questionnaire.rses import RSESQuestionnaire
from common.measurement.questionnaire.mvs_short import MVSShortQuestionnaire
from common.measurement.rater import EduMirrorRater
from common.measurement.rubrics.materialism_consumption import create_social_comparison_rubric, create_consumer_decision_rubric
import json


def run_baseline() -> None:
    model_config = create_model_config_from_environment('production', disable_language_model=True)
    model = create_language_model(model_config)
    embedder = create_simple_embedder()
    entities = create_agents(model, embedder)

    builder = SceneBuilder(model=model, embedder_model=embedder)

    initializer = builder.build_initializer_game_master(
        name='initial setup rules',
        entities=entities,
        params={
            'next_game_master_name': 'conversation rules',
            'shared_memories': [
                'An important game is coming this weekend.',
                'The mall is releasing a limited edition sneaker on Saturday.',
            ],
            'player_specific_context': {
                'Leo': 'student',
                'Kevin': 'student',
                'Mia': 'student',
                'Coach Carter': 'teacher',
            },
            'player_specific_memories': AGENT_MEMORIES,
        },
    )

    gym_type = scene_lib.SceneTypeSpec(
        name='gym_comparison',
        game_master_name='conversation rules',
        default_premise={
            'Leo': [
                'You are at basketball practice. You notice Kevin has brand new, expensive "SkyHigh" sneakers. Your own shoes are worn out. You feel inadequate and worry your gear makes you look like a bad player.'
            ],
            'Kevin': [
                'You are at practice wearing your new $300 limited edition sneakers. You want to show them off and imply they make you the best player on the court.'
            ],
            'Mia': [
                'You focus on drills. You notice Kevin showing off and Leo looking uncomfortable. You believe skills matter more than shoes.'
            ],
            'Coach Carter': [
                "You observe practice. You notice players are distracted by Kevin's new gear instead of focusing on drills."
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. The scene is the gym during a break. Kevin flaunts his shoes. Leo reacts with envy/shame. The interaction should highlight the social comparison pressure. If the break ends, append [END]."
            )
        ),
        possible_participants=['Leo', 'Kevin', 'Mia', 'Coach Carter'],
    )

    mall_type = scene_lib.SceneTypeSpec(
        name='mall_decision',
        game_master_name='conversation rules',
        default_premise={
            'Leo': [
                'It is Saturday at the sneaker store. You are holding the expensive shoes Kevin has. They cost all your savings. You must decide whether to buy them to fit in or save your money.'
            ],
            'Kevin': [
                'You are at the store with Leo. You pressure him to buy the matching shoes so you can look like a "pro duo" on the court.'
            ],
            'Mia': [
                'You are at the store. You think the shoes are a waste of money and try to be the voice of reason.'
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. At the mall counter, Leo faces the final decision. Kevin pressures, Mia advises. Leo must announce if he buys or not and explain why. If the transaction decision is made, append [END]."
            )
        ),
        possible_participants=['Leo', 'Kevin', 'Mia'],
    )

    scenes = [
        scene_lib.SceneSpec(scene_type=gym_type, participants=['Leo', 'Kevin', 'Mia', 'Coach Carter'], num_rounds=3),
        scene_lib.SceneSpec(scene_type=mall_type, participants=['Leo', 'Kevin', 'Mia'], num_rounds=4),
    ]

    dialogic_gm = builder.build_dialogic_and_dramaturgic_game_master(
        name='conversation rules',
        entities=entities,
        scenes=scenes,
    )

    log: list[dict] = []
    total_rounds = sum(s.num_rounds for s in scenes)
    builder.run_with_sequential_engine(
        game_masters=[initializer, dialogic_gm],
        entities=entities,
        premise='',
        max_steps=total_rounds,
        verbose=True,
        log=log,
    )

    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    out_dir = os.path.join('results', 'materialism_consumption_decision', f'run_{ts}', 'condition_baseline')
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, 'simulation_events.jsonl')
    windows: list[tuple[int, int, str, list[str]]] = []
    current = 1
    for s in scenes:
        start = current
        end = current + s.num_rounds - 1
        windows.append((start, end, s.scene_type.name, list(s.participants)))
        current = end + 1
    with open(out_file, 'w', encoding='utf-8') as f:
        if log:
            step_idx = 1
            for entry in log:
                summary = entry.get('Summary', '')
                event_text = ''
                if isinstance(summary, str) and '---' in summary:
                    event_text = summary.split('---', 1)[1].strip()
                scene_name = ''
                participants: list[str] = []
                for start, end, name, parts in windows:
                    if start <= step_idx <= end:
                        scene_name = name
                        participants = parts
                        break
                safe_entry = {
                    'Step': step_idx,
                    'Scene': scene_name,
                    'Participants': participants,
                    'Event': event_text,
                }
                f.write(json.dumps(safe_entry, ensure_ascii=False) + '\n')
                step_idx += 1
        else:
            for step_idx in range(1, total_rounds + 1):
                scene_name = ''
                participants: list[str] = []
                for start, end, name, parts in windows:
                    if start <= step_idx <= end:
                        scene_name = name
                        participants = parts
                        break
                safe_entry = {
                    'Step': step_idx,
                    'Scene': scene_name,
                    'Participants': participants,
                    'Event': '',
                }
                f.write(json.dumps(safe_entry, ensure_ascii=False) + '\n')

    rater = EduMirrorRater(model)
    transcript = rater.load_transcript(out_file)
    rubrics = [create_social_comparison_rubric('Leo'), create_consumer_decision_rubric('Leo')]
    rater_results = rater.apply_rubrics(transcript, rubrics)
    if rater_results:
        for name, df in rater_results.items():
            prefix = 'rater_social_comparison' if 'Social Comparison' in name else 'rater_consumer_decision'
            rater.save_results(df, out_dir, prefix)

    def _parse_options(action_spec_str: str) -> list[str]:
        parts = action_spec_str.split(';;')
        for p in parts:
            if p.strip().startswith('options:'):
                _, val = p.split(':', 1)
                return [x.strip() for x in val.split(',') if x.strip()]
        return []

    def _responder(player_name: str, action_spec_str: str) -> str:
        opts = _parse_options(action_spec_str)
        for c in ('Neutral', 'Agree', 'Somewhat', 'A little bit'):
            if c in opts:
                return c
        return opts[len(opts) // 2] if opts else ''

    questionnaires = [MVSShortQuestionnaire(), RSESQuestionnaire()]
    surveyor = EduMirrorSurveyor(questionnaires, ['Leo'])
    df = surveyor.run_once(_responder)
    surveyor.save_results(df, out_dir, 'leo_post_baseline')


def run_interventions() -> None:
    model_config = create_model_config_from_environment('production', disable_language_model=True)
    model = create_language_model(model_config)
    embedder = create_simple_embedder()
    entities = create_agents(model, embedder)

    builder = SceneBuilder(model=model, embedder_model=embedder)

    initializer_params = {
        'next_game_master_name': 'conversation rules',
        'shared_memories': [
            'An important game is coming this weekend.',
            'The mall is releasing a limited edition sneaker on Saturday.',
        ],
        'player_specific_context': {
            'Leo': 'student',
            'Kevin': 'student',
            'Mia': 'student',
            'Coach Carter': 'teacher',
        },
        'player_specific_memories': AGENT_MEMORIES,
    }

    gym_type = scene_lib.SceneTypeSpec(
        name='gym_comparison',
        game_master_name='conversation rules',
        default_premise={
            'Leo': [
                'You are at basketball practice. You notice Kevin has brand new, expensive "SkyHigh" sneakers. Your own shoes are worn out. You feel inadequate and worry your gear makes you look like a bad player.'
            ],
            'Kevin': [
                'You are at practice wearing your new $300 limited edition sneakers. You want to show them off and imply they make you the best player on the court.'
            ],
            'Mia': [
                'You focus on drills. You notice Kevin showing off and Leo looking uncomfortable. You believe skills matter more than shoes.'
            ],
            'Coach Carter': [
                "You observe practice. You notice players are distracted by Kevin's new gear instead of focusing on drills."
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. The scene is the gym during a break. Kevin flaunts his shoes. Leo reacts with envy/shame. The interaction should highlight the social comparison pressure. If the break ends, append [END]."
            )
        ),
        possible_participants=['Leo', 'Kevin', 'Mia', 'Coach Carter'],
    )

    mall_type = scene_lib.SceneTypeSpec(
        name='mall_decision',
        game_master_name='conversation rules',
        default_premise={
            'Leo': [
                'It is Saturday at the sneaker store. You are holding the expensive shoes Kevin has. They cost all your savings. You must decide whether to buy them to fit in or save your money.'
            ],
            'Kevin': [
                'You are at the store with Leo. You pressure him to buy the matching shoes so you can look like a "pro duo" on the court.'
            ],
            'Mia': [
                'You are at the store. You think the shoes are a waste of money and try to be the voice of reason.'
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. At the mall counter, Leo faces the final decision. Kevin pressures, Mia advises. Leo must announce if he buys or not and explain why. If the transaction decision is made, append [END]."
            )
        ),
        possible_participants=['Leo', 'Kevin', 'Mia'],
    )

    coach_type = scene_lib.SceneTypeSpec(
        name='coach_intervention',
        game_master_name='conversation rules',
        default_premise={
            'Leo': [
                'Practice is over. Coach Carter has asked you to stay behind. You are worried he noticed your distraction.'
            ],
            'Coach Carter': [
                'Practice is over. You pull Leo aside to talk about his focus. You want to teach him that self-worth comes from effort and skill, not expensive equipment.'
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. In the equipment room, Coach Carter talks to Leo about values, challenging the idea that shoes define a player. Leo responds to this guidance. If the lesson is concluded, append [END]."
            )
        ),
        possible_participants=['Leo', 'Coach Carter'],
    )

    norm_type = scene_lib.SceneTypeSpec(
        name='team_norm_setting',
        game_master_name='conversation rules',
        default_premise={
            'Coach Carter': [
                'After practice, hold a brief meeting to establish that discussing gear prices is discouraged and focus should be on technique.'
            ],
            'Leo': [
                'Attend the meeting and feel the relief as team values shift toward grit over gear.'
            ],
            'Kevin': [
                'Hear the norm-setting and realize flaunting gear is defined as unprofessional.'
            ],
            'Mia': [
                'Be acknowledged for active positioning despite wearing old shoes.'
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. Coach addresses the team about distraction of material goods, establishing a norm that values grit over gear. Kevin is silenced, Leo feels relieved. Append [END] when the meeting concludes."
            )
        ),
        possible_participants=['Leo', 'Kevin', 'Mia', 'Coach Carter'],
    )

    pre_scenes = [scene_lib.SceneSpec(scene_type=gym_type, participants=['Leo', 'Kevin', 'Mia', 'Coach Carter'], num_rounds=3)]
    post_scenes = [scene_lib.SceneSpec(scene_type=mall_type, participants=['Leo', 'Kevin', 'Mia'], num_rounds=4)]
    i1 = scene_lib.SceneSpec(scene_type=coach_type, participants=['Leo', 'Coach Carter'], num_rounds=6)
    i2 = scene_lib.SceneSpec(scene_type=norm_type, participants=['Leo', 'Kevin', 'Mia', 'Coach Carter'], num_rounds=6)

    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_root = os.path.join('results', 'materialism_consumption_decision', f'run_{ts}')

    def _run_branch_and_write(scenes: list[scene_lib.SceneSpec], out_dir: str, survey_prefix: str) -> None:
        initializer = builder.build_initializer_game_master(
            name='initial setup rules',
            entities=entities,
            params=initializer_params,
        )
        gm = builder.build_dialogic_and_dramaturgic_game_master(
            name='conversation rules',
            entities=entities,
            scenes=scenes,
        )
        log: list[dict] = []
        total_rounds = sum(s.num_rounds for s in scenes)
        builder.run_with_sequential_engine(
            game_masters=[initializer, gm],
            entities=entities,
            premise='',
            max_steps=total_rounds,
            verbose=True,
            log=log,
        )
        windows: list[tuple[int, int, str, list[str]]] = []
        current = 1
        for s in scenes:
            start = current
            end = current + s.num_rounds - 1
            windows.append((start, end, s.scene_type.name, list(s.participants)))
            current = end + 1
        os.makedirs(out_dir, exist_ok=True)
        out_file = os.path.join(out_dir, 'simulation_events.jsonl')
        with open(out_file, 'w', encoding='utf-8') as f:
            if log:
                step_idx = 1
                for entry in log:
                    summary = entry.get('Summary', '')
                    event_text = ''
                    if isinstance(summary, str) and '---' in summary:
                        event_text = summary.split('---', 1)[1].strip()
                    scene_name = ''
                    participants: list[str] = []
                    for start, end, name, parts in windows:
                        if start <= step_idx <= end:
                            scene_name = name
                            participants = parts
                            break
                    safe_entry = {
                        'Step': step_idx,
                        'Scene': scene_name,
                        'Participants': participants,
                        'Event': event_text,
                    }
                    f.write(json.dumps(safe_entry, ensure_ascii=False) + '\n')
                    step_idx += 1
            else:
                for step_idx in range(1, total_rounds + 1):
                    scene_name = ''
                    participants: list[str] = []
                    for start, end, name, parts in windows:
                        if start <= step_idx <= end:
                            scene_name = name
                            participants = parts
                            break
                    safe_entry = {
                        'Step': step_idx,
                        'Scene': scene_name,
                        'Participants': participants,
                        'Event': '',
                    }
                    f.write(json.dumps(safe_entry, ensure_ascii=False) + '\n')

        rater = EduMirrorRater(model)
        transcript = rater.load_transcript(out_file)
        rubrics = [create_social_comparison_rubric('Leo'), create_consumer_decision_rubric('Leo')]
        rater_results = rater.apply_rubrics(transcript, rubrics)
        if rater_results:
            for name, df in rater_results.items():
                prefix = 'rater_social_comparison' if 'Social Comparison' in name else 'rater_consumer_decision'
                rater.save_results(df, out_dir, prefix)

        def _parse_options(action_spec_str: str) -> list[str]:
            parts = action_spec_str.split(';;')
            for p in parts:
                if p.strip().startswith('options:'):
                    _, val = p.split(':', 1)
                    return [x.strip() for x in val.split(',') if x.strip()]
            return []

        def _responder(player_name: str, action_spec_str: str) -> str:
            opts = _parse_options(action_spec_str)
            for c in ('Neutral', 'Agree', 'Somewhat', 'A little bit'):
                if c in opts:
                    return c
            return opts[len(opts) // 2] if opts else ''

        questionnaires = [MVSShortQuestionnaire(), RSESQuestionnaire()]
        surveyor = EduMirrorSurveyor(questionnaires, ['Leo'])
        df = surveyor.run_once(_responder)
        surveyor.save_results(df, out_dir, survey_prefix)

    _run_branch_and_write([*pre_scenes, i1, *post_scenes], os.path.join(output_root, 'condition_coach_intervention'), 'leo_post_coach_intervention')
    _run_branch_and_write([*pre_scenes, i2, *post_scenes], os.path.join(output_root, 'condition_team_norm_setting'), 'leo_post_team_norm_setting')


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'baseline':
        run_baseline()
    elif len(sys.argv) > 1 and sys.argv[1] == 'interventions':
        run_interventions()
    else:
        run_baseline()
        run_interventions()

