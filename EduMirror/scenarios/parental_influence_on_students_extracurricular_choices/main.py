from datetime import datetime
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from concordia.environment.engines.sequential import Sequential
from concordia.typing import scene as scene_lib
from concordia.typing import entity as entity_lib
from common.simulation_utils.model_setup import create_language_model, create_simple_embedder, create_model_config_from_environment
from common.simulation_utils.scene_builder import SceneBuilder
from scenarios.parental_influence_on_students_extracurricular_choices.agents import create_agents, AGENT_MEMORIES
import json
from common.measurement import EduMirrorSurveyor
from common.measurement.rater import EduMirrorRater
from common.measurement.rubrics.communication_styles import build_communication_rubrics
from common.measurement.questionnaire.panas_c import PANASCQuestionnaire
from common.measurement.questionnaire.imi import IMIQuestionnaire
from common.measurement.questionnaire.bpnsfs_autonomy import BPNSFSAutonomyQuestionnaire


SCENARIO_NAME = 'parental_influence_on_students_extracurricular_choices'


def _results_root(ts: str, condition: str) -> str:
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'results', SCENARIO_NAME, f'run_{ts}', condition))
    os.makedirs(base, exist_ok=True)
    return base


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
                'Leo': 'student',
                'Margaret': 'parent',
                'Ms. Chen': 'teacher',
            },
            'player_specific_memories': AGENT_MEMORIES,
        },
    )

    recruitment_type = scene_lib.SceneTypeSpec(
        name='club_recruitment',
        game_master_name='conversation rules',
        default_premise={
            'Leo': [
                'You are at the Comic Club recruitment booth on Friday afternoon. You love drawing but fear Mom wants you to attend a coding boot camp. Ms. Chen is nearby.'
            ],
            'Ms. Chen': [
                'You manage the recruitment booth. You see Leo staring at the poster with longing but hesitation. You approach and encourage him to sign up.'
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. Discuss club details and Leo's hesitation. Append [END] if Leo takes an application form or walks away."
            )
        ),
        possible_participants=['Leo', 'Ms. Chen'],
    )
    family_type = scene_lib.SceneTypeSpec(
        name='family_negotiation',
        game_master_name='conversation rules',
        default_premise={
            'Leo': [
                'At dinner on Friday, you hold the application form and ask Mom to let you join the Comic Club instead of the coding camp.'
            ],
            'Margaret': [
                'At dinner on Friday, you want to confirm payment details for the coding camp. You believe this is the best path for Leo.'
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. Negotiate the extracurricular choice. Reach a conclusion or stalemate. Append [END] when the conversation concludes."
            )
        ),
        possible_participants=['Leo', 'Margaret'],
    )
    final_type = scene_lib.SceneTypeSpec(
        name='final_decision',
        game_master_name='conversation rules',
        default_premise={
            'Leo': [
                "On Monday at the office, you announce your final decision to Ms. Chen (join comic, join coding, or compromise)."
            ],
            'Ms. Chen': [
                "On Monday at the office, you await Leo's final decision and accept whatever decision he makes."
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. Announce and respond to the final decision. Append [END] after the decision."
            )
        ),
        possible_participants=['Leo', 'Ms. Chen'],
    )

    scenes = [
        scene_lib.SceneSpec(scene_type=recruitment_type, participants=['Leo', 'Ms. Chen'], num_rounds=6),
        scene_lib.SceneSpec(scene_type=family_type, participants=['Leo', 'Margaret'], num_rounds=8),
        scene_lib.SceneSpec(scene_type=final_type, participants=['Leo', 'Ms. Chen'], num_rounds=6),
    ]
    dialogic_gm = builder.build_dialogic_and_dramaturgic_game_master(
        name='conversation rules',
        entities=entities,
        scenes=scenes,
    )

    log = []
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
    out_dir = _results_root(ts, 'condition_baseline')
    out_file = os.path.join(out_dir, 'simulation_events.jsonl')
    windows = []
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
                participants = []
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
                participants = []
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

    def _survey_responder(player_name: str, action_spec_str: str) -> str:
        opts = _parse_options(action_spec_str)
        prefer = ['Neutral', 'Moderately']
        for c in prefer:
            if c in opts:
                return c
        return opts[len(opts) // 2] if opts else ''

    questionnaires = [IMIQuestionnaire(), BPNSFSAutonomyQuestionnaire(), PANASCQuestionnaire()]
    surveyor = EduMirrorSurveyor(questionnaires, ['Leo'])
    df = surveyor.run_once(_survey_responder)
    surveyor.save_results(df, out_dir, 'leo_post_baseline')

    rater = EduMirrorRater(model)
    transcript = rater.load_transcript(out_file)
    rubrics = build_communication_rubrics(target_agent=None)
    rater_results = rater.apply_rubrics(transcript, rubrics)
    for name, rdf in rater_results.items():
        rater.save_results(rdf, out_dir, f'leo_post_baseline_{name}')


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
            'Leo': 'student',
            'Margaret': 'parent',
            'Ms. Chen': 'teacher',
        },
        'player_specific_memories': AGENT_MEMORIES,
    }

    recruitment_type = scene_lib.SceneTypeSpec(
        name='club_recruitment',
        game_master_name='conversation rules',
        default_premise={
            'Leo': [
                'You are at the Comic Club recruitment booth on Friday afternoon. You love drawing but fear Mom wants you to attend a coding boot camp. Ms. Chen is nearby.'
            ],
            'Ms. Chen': [
                'You manage the recruitment booth. You see Leo staring at the poster with longing but hesitation. You approach and encourage him to sign up.'
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. Discuss club details and Leo's hesitation. Append [END] if Leo takes an application form or walks away."
            )
        ),
        possible_participants=['Leo', 'Ms. Chen'],
    )
    family_type = scene_lib.SceneTypeSpec(
        name='family_negotiation',
        game_master_name='conversation rules',
        default_premise={
            'Leo': [
                'At dinner on Friday, you hold the application form and ask Mom to let you join the Comic Club instead of the coding camp.'
            ],
            'Margaret': [
                'At dinner on Friday, you want to confirm payment details for the coding camp. You believe this is the best path for Leo.'
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. Negotiate the extracurricular choice. Reach a conclusion or stalemate. Append [END] when the conversation concludes."
            )
        ),
        possible_participants=['Leo', 'Margaret'],
    )
    final_type = scene_lib.SceneTypeSpec(
        name='final_decision',
        game_master_name='conversation rules',
        default_premise={
            'Leo': [
                "On Monday at the office, you announce your final decision to Ms. Chen (join comic, join coding, or compromise)."
            ],
            'Ms. Chen': [
                "On Monday at the office, you await Leo's final decision and accept whatever decision he makes."
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. Announce and respond to the final decision. Append [END] after the decision."
            )
        ),
        possible_participants=['Leo', 'Ms. Chen'],
    )

    empowerment_type = scene_lib.SceneTypeSpec(
        name='teacher_student_empowerment',
        game_master_name='conversation rules',
        default_premise={
            'Ms. Chen': [
                "Invite Leo to the office and teach Non-Violent Communication skills to express feelings and needs without escalating conflict."
            ],
            'Leo': [
                "You are nervous about talking to Mom. You listen to advice on how to explain why art matters to you and how to ask for autonomy support."
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. In office mentoring, co-create an honest communication plan. Append [END] when a clear plan emerges."
            )
        ),
        possible_participants=['Leo', 'Ms. Chen'],
    )
    teacher_parent_call_type = scene_lib.SceneTypeSpec(
        name='teacher_parent_call',
        game_master_name='conversation rules',
        default_premise={
            'Ms. Chen': [
                "Call Margaret to advocate for Leo's artistic potential and the benefits of autonomy and creative outlets for mental health and focus."
            ],
            'Margaret': [
                "Receive the teacher's call; listen with skepticism but respect. Share concerns about the future and consider the teacher's perspective."
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. On phone, discuss Leo's development and choices in a supportive way. Append [END] when aligned."
            )
        ),
        possible_participants=['Ms. Chen', 'Margaret'],
    )

    pre_scenes = [
        scene_lib.SceneSpec(scene_type=recruitment_type, participants=['Leo', 'Ms. Chen'], num_rounds=6),
    ]
    post_scenes = [
        scene_lib.SceneSpec(scene_type=family_type, participants=['Leo', 'Margaret'], num_rounds=8),
        scene_lib.SceneSpec(scene_type=final_type, participants=['Leo', 'Ms. Chen'], num_rounds=6),
    ]
    i1 = scene_lib.SceneSpec(scene_type=empowerment_type, participants=['Leo', 'Ms. Chen'], num_rounds=6)
    i2 = scene_lib.SceneSpec(scene_type=teacher_parent_call_type, participants=['Ms. Chen', 'Margaret'], num_rounds=6)

    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'results', SCENARIO_NAME, f'run_{ts}'))

    def _run_branch_and_write(scenes: list[scene_lib.SceneSpec], condition_name: str, prefix: str) -> None:
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
        out_dir = os.path.join(output_root, condition_name)
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
            prefer = ['Neutral', 'Moderately']
            for c in prefer:
                if c in opts:
                    return c
            return opts[len(opts) // 2] if opts else ''

        questionnaires = [IMIQuestionnaire(), BPNSFSAutonomyQuestionnaire(), PANASCQuestionnaire()]
        surveyor = EduMirrorSurveyor(questionnaires, ['Leo'])
        df = surveyor.run_once(_responder)
        surveyor.save_results(df, out_dir, prefix)

        rater = EduMirrorRater(model)
        transcript = rater.load_transcript(out_file)
        rubrics = build_communication_rubrics(target_agent=None)
        results = rater.apply_rubrics(transcript, rubrics)
        for name, rdf in results.items():
            rater.save_results(rdf, out_dir, f'{prefix}_{name}')

    _run_branch_and_write([*pre_scenes, *post_scenes], 'condition_baseline_repeat', 'leo_post_baseline_repeat')
    _run_branch_and_write([*pre_scenes, i1, *post_scenes], 'condition_teacher_student_empowerment', 'leo_post_teacher_student_empowerment')
    _run_branch_and_write([*pre_scenes, i2, *post_scenes], 'condition_teacher_parent_call', 'leo_post_teacher_parent_call')


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'baseline':
        run_baseline()
    elif len(sys.argv) > 1 and sys.argv[1] == 'interventions':
        run_interventions()
    else:
        run_baseline()
        run_interventions()
