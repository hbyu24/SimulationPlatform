from datetime import datetime
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from concordia.environment.engines.sequential import Sequential
from concordia.typing import scene as scene_lib
from concordia.typing import entity as entity_lib
from common.simulation_utils.model_setup import create_language_model, create_simple_embedder, create_model_config_from_environment
from common.simulation_utils.scene_builder import SceneBuilder
from scenarios.social_comparison_and_materialistic.agents import create_agents, AGENT_MEMORIES
import json
from common.measurement import EduMirrorSurveyor
from common.measurement.questionnaire import IncomQuestionnaire, RSESQuestionnaire
from common.measurement.questionnaire.yms import YMSQuestionnaire
from common.measurement.rater import EduMirrorRater
from common.measurement.rubrics.materialism_behaviors import get_rubric as get_materialism_rubric


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
            'shared_memories': [],
            'player_specific_context': {
                'Alex': 'student',
                'Ben': 'student',
                'Chloe': 'student',
                'Jordan': 'parent',
                'Mrs. Lee': 'teacher',
            },
            'player_specific_memories': AGENT_MEMORIES,
        },
    )

    breakroom_type = scene_lib.SceneTypeSpec(
        name='breakroom_showoff',
        game_master_name='conversation rules',
        default_premise={
            'Chloe': [
                'You brought the latest expensive smartphone to school and show it off to everyone to feel superior.'
            ],
            'Alex': [
                'You see Chloe holding the phone you have dreamed of and feel inferior, trying to hide your old phone.'
            ],
            'Ben': [
                'You notice Chloe showing off and think it is just a phone, while seeing Alex looks upset.'
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. It is break time. Chloe displays her new phone. React to this social signal and advance the interaction."
            )
        ),
        possible_participants=['Alex', 'Chloe', 'Ben'],
    )

    dinner_type = scene_lib.SceneTypeSpec(
        name='family_dinner_request',
        game_master_name='conversation rules',
        default_premise={
            'Alex': [
                'At dinner you ask your parent Jordan for the new phone, feeling without it you are a nobody at school.'
            ],
            'Jordan': [
                'You notice Alex is restless and you want to teach about saving and family values while considering budget.'
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. At dinner, Alex makes a request for an expensive item. Jordan responds based on family values. Keep the dialogue moving."
            )
        ),
        possible_participants=['Alex', 'Jordan'],
    )

    next_day_type = scene_lib.SceneTypeSpec(
        name='next_day_aftermath',
        game_master_name='conversation rules',
        default_premise={
            'Alex': [
                'Next day in class, Chloe asks whether you bought the new phone. You choose to lie, avoid, or be honest.'
            ],
            'Ben': [
                'You ask Alex for an update and respond with understanding.'
            ],
            'Chloe': [
                'You ask Alex whether the new phone was bought and react to the response.'
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. In class next day, ask or respond with the final decision and advance toward closure."
            )
        ),
        possible_participants=['Alex', 'Ben', 'Chloe'],
    )

    scenes_for_dialogic = [
        scene_lib.SceneSpec(scene_type=breakroom_type, participants=['Alex', 'Chloe', 'Ben'], num_rounds=3),
        scene_lib.SceneSpec(scene_type=dinner_type, participants=['Alex', 'Jordan'], num_rounds=4),
        scene_lib.SceneSpec(scene_type=next_day_type, participants=['Alex', 'Ben', 'Chloe'], num_rounds=3),
    ]

    dialogic_gm = builder.build_dialogic_and_dramaturgic_game_master(
        name='conversation rules',
        entities=entities,
        scenes=scenes_for_dialogic,
    )

    log = []
    total_rounds = sum(s.num_rounds for s in scenes_for_dialogic)
    builder.run_with_sequential_engine(
        game_masters=[initializer, dialogic_gm],
        entities=entities,
        premise='',
        max_steps=total_rounds,
        verbose=True,
        log=log,
    )

    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    out_dir = os.path.join('results', 'social_comparison_and_materialistic', f'run_{ts}', 'condition_baseline')
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, 'simulation_events.jsonl')
    scene_windows = [
        (1, scenes_for_dialogic[0].num_rounds, 'breakroom_showoff', ['Alex','Chloe','Ben']),
        (scenes_for_dialogic[0].num_rounds + 1,
         scenes_for_dialogic[0].num_rounds + scenes_for_dialogic[1].num_rounds,
         'family_dinner_request', ['Alex','Jordan']),
        (scenes_for_dialogic[0].num_rounds + scenes_for_dialogic[1].num_rounds + 1,
         scenes_for_dialogic[0].num_rounds + scenes_for_dialogic[1].num_rounds + scenes_for_dialogic[2].num_rounds,
         'next_day_aftermath', ['Alex','Ben','Chloe']),
    ]
    with open(out_file, 'w', encoding='utf-8') as f:
        if log:
            for entry in log:
                step = entry.get('Step')
                summary = entry.get('Summary','')
                event_text = ''
                if isinstance(summary, str) and '---' in summary:
                    event_text = summary.split('---',1)[1].strip()
                scene_name = ''
                participants = []
                if isinstance(step, int):
                    for start,end,name,parts in scene_windows:
                        if start <= step <= end:
                            scene_name = name
                            participants = parts
                            break
                safe_entry = {
                    'Step': step,
                    'Scene': scene_name,
                    'Participants': participants,
                    'Event': event_text,
                }
                f.write(json.dumps(safe_entry, ensure_ascii=False) + '\n')
        else:
            for step_idx in range(1, total_rounds + 1):
                scene_name = ''
                participants = []
                for start,end,name,parts in scene_windows:
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
    print(f'Baseline events written to {out_file}')

    def _measurement_responder(player_name: str, action_spec_str: str) -> str:
        parts = action_spec_str.split(';;')
        options = []
        for p in parts:
            if p.strip().startswith('options:'):
                _, val = p.split(':', 1)
                options = [x.strip() for x in val.split(',') if x.strip()]
                break
        for candidate in ('Neutral', 'Agree', 'Somewhat', 'A little bit'):
            if candidate in options:
                return candidate
        return options[len(options) // 2] if options else ''

    questionnaires = [IncomQuestionnaire(), RSESQuestionnaire(), YMSQuestionnaire()]
    surveyor = EduMirrorSurveyor(questionnaires, ['Alex'])
    results_df = surveyor.run_once(_measurement_responder)
    surveyor.save_results(results_df, out_dir, 'alex_post_baseline')
    print(f'Surveyor results saved under {out_dir}')

    rater = EduMirrorRater(model)
    transcript = rater.load_transcript(out_file)
    rubric_df = rater.analyze_transcript(transcript, get_materialism_rubric())
    rater.save_results(rubric_df, out_dir, 'materialism_rater_baseline')
    print(f'Rater results saved under {out_dir}')


def run_interventions() -> None:
    model_config = create_model_config_from_environment('production', disable_language_model=True)
    model = create_language_model(model_config)
    embedder = create_simple_embedder()
    entities = create_agents(model, embedder)

    builder = SceneBuilder(model=model, embedder_model=embedder)

    initializer_params = {
        'next_game_master_name': 'conversation rules',
        'shared_memories': [],
        'player_specific_context': {
            'Alex': 'student',
            'Ben': 'student',
            'Chloe': 'student',
            'Jordan': 'parent',
            'Mrs. Lee': 'teacher',
        },
        'player_specific_memories': AGENT_MEMORIES,
    }

    breakroom_type = scene_lib.SceneTypeSpec(
        name='breakroom_showoff',
        game_master_name='conversation rules',
        default_premise={
            'Chloe': [
                'You brought the latest expensive smartphone to school and show it off to everyone to feel superior.'
            ],
            'Alex': [
                'You see Chloe holding the phone you have dreamed of and feel inferior, trying to hide your old phone.'
            ],
            'Ben': [
                'You notice Chloe showing off and think it is just a phone, while seeing Alex looks upset.'
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. It is break time. Chloe displays her new phone. React to this social signal. If the interaction reaches a natural pause, append [END] at the end."
            )
        ),
        possible_participants=['Alex', 'Chloe', 'Ben'],
    )

    dinner_type = scene_lib.SceneTypeSpec(
        name='family_dinner_request',
        game_master_name='conversation rules',
        default_premise={
            'Alex': [
                'At dinner you ask your parent Jordan for the new phone, feeling without it you are a nobody at school.'
            ],
            'Jordan': [
                'You notice Alex is restless and you want to teach about saving and family values while considering budget.'
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. At dinner, Alex makes a request for an expensive item. Jordan responds based on family values. If the conversation concludes, append [END] at the end."
            )
        ),
        possible_participants=['Alex', 'Jordan'],
    )

    next_day_type = scene_lib.SceneTypeSpec(
        name='next_day_aftermath',
        game_master_name='conversation rules',
        default_premise={
            'Alex': [
                'Next day in class, Chloe asks whether you bought the new phone. You choose to lie, avoid, or be honest.'
            ],
            'Ben': [
                'You ask Alex for an update and respond with understanding.'
            ],
            'Chloe': [
                'You ask Alex whether the new phone was bought and react to the response.'
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. In class next day, ask or respond with the final decision. If the scene goal is achieved, append [END] at the end."
            )
        ),
        possible_participants=['Alex', 'Ben', 'Chloe'],
    )

    counseling_type = scene_lib.SceneTypeSpec(
        name='teacher_counseling',
        game_master_name='conversation rules',
        default_premise={
            'Mrs. Lee': [
                'Invite Alex to talk and help him understand that his worth is not defined by what he owns.'
            ],
            'Alex': [
                'You feel defensive yet sad about the phone situation and reflect on self-worth.'
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. In the office, Mrs. Lee guides Alex to reflect on self-worth. If the educational goal is met, append [END] at the end."
            )
        ),
        possible_participants=['Alex', 'Mrs. Lee'],
    )

    teacher_parent_call_type = scene_lib.SceneTypeSpec(
        name='teacher_parent_call',
        game_master_name='conversation rules',
        default_premise={
            'Mrs. Lee': [
                'Call Jordan to discuss class comparison climate and suggest empathetic yet firm responses at home.'
            ],
            'Jordan': [
                'Share concerns and consider guidance on supporting Alex with validation and limit setting.'
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. On phone, discuss youth comparison and family strategy supportively. Append [END] when aligned."
            )
        ),
        possible_participants=['Jordan', 'Mrs. Lee'],
    )

    class_meeting_type = scene_lib.SceneTypeSpec(
        name='class_meeting_value_shift',
        game_master_name='conversation rules',
        default_premise={
            'Mrs. Lee': [
                'Organize a class meeting on technology and real life, highlighting confidence beyond consumption.'
            ],
            'Alex': [
                'Share thoughts and listen to peers, reflect on value beyond possessions.'
            ],
            'Ben': [
                'Express view that items do not define coolness and propose inclusive alternatives.'
            ],
            'Chloe': [
                'Reflect on economic differences sensitively and propose inclusive ideas.'
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. In class meeting, discuss values beyond consumption. Append [END] when consensus emerges."
            )
        ),
        possible_participants=['Alex', 'Ben', 'Chloe', 'Mrs. Lee'],
    )

    pre_scenes = [
        scene_lib.SceneSpec(scene_type=breakroom_type, participants=['Alex', 'Chloe', 'Ben'], num_rounds=3),
    ]
    post_scenes = [
        scene_lib.SceneSpec(scene_type=dinner_type, participants=['Alex', 'Jordan'], num_rounds=4),
        scene_lib.SceneSpec(scene_type=next_day_type, participants=['Alex', 'Ben', 'Chloe'], num_rounds=3),
    ]
    i1 = scene_lib.SceneSpec(scene_type=counseling_type, participants=['Alex', 'Mrs. Lee'], num_rounds=6)
    i2 = scene_lib.SceneSpec(scene_type=teacher_parent_call_type, participants=['Jordan', 'Mrs. Lee'], num_rounds=6)
    i3 = scene_lib.SceneSpec(scene_type=class_meeting_type, participants=['Alex', 'Ben', 'Chloe', 'Mrs. Lee'], num_rounds=8)

    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_root = os.path.join('results', 'social_comparison_and_materialistic', f'run_{ts}')

    def _run_branch_and_write(scenes: list[scene_lib.SceneSpec], out_dir: str, prefix: str) -> None:
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
        windows: list[tuple[int,int,str,list[str]]] = []
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

        questionnaires = [IncomQuestionnaire(), RSESQuestionnaire(), YMSQuestionnaire()]
        surveyor = EduMirrorSurveyor(questionnaires, ['Alex'])
        df = surveyor.run_once(_responder)
        surveyor.save_results(df, out_dir, prefix)

        rater = EduMirrorRater(model)
        transcript = rater.load_transcript(out_file)
        rubric_df = rater.analyze_transcript(transcript, get_materialism_rubric())
        rater.save_results(rubric_df, out_dir, f'materialism_rater_{prefix}')

    _run_branch_and_write([*pre_scenes, i1, *post_scenes], os.path.join(output_root, 'condition_teacher_student_talk'), 'alex_post_teacher_student_talk')
    _run_branch_and_write([*pre_scenes, i2, *post_scenes], os.path.join(output_root, 'condition_teacher_parent_call'), 'alex_post_teacher_parent_call')
    _run_branch_and_write([*pre_scenes, i3, *post_scenes], os.path.join(output_root, 'condition_class_meeting'), 'alex_post_class_meeting')


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'baseline':
        run_baseline()
    elif len(sys.argv) > 1 and sys.argv[1] == 'interventions':
        run_interventions()
    else:
        run_baseline()
        run_interventions()
