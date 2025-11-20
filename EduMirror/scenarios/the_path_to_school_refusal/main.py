from datetime import datetime
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from concordia.environment.engines.sequential import Sequential
from concordia.typing import scene as scene_lib
from concordia.typing import entity as entity_lib
from common.simulation_utils.model_setup import create_language_model, create_simple_embedder, create_model_config_from_environment
from common.simulation_utils.scene_builder import SceneBuilder
from scenarios.the_path_to_school_refusal.agents import create_agents, AGENT_MEMORIES
import json
from common.measurement.surveyor import EduMirrorSurveyor
from common.measurement.questionnaire.pss10 import PSS10Questionnaire
from common.measurement.questionnaire.dass21 import DASS21Questionnaire
from common.measurement.questionnaire.srasr import SRASRQuestionnaire


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
            'next_game_master_name': 'school_life_rules',
            'shared_memories': [
                'Lucas has been struggling with math recently.',
                'The mid-term exams were held yesterday.',
                'Leo sits behind Lucas in class.',
            ],
            'player_specific_context': {
                'Lucas': 'student',
                'Sarah': 'parent',
                'Mr. Thompson': 'teacher',
                'Leo': 'student',
            },
            'player_specific_memories': AGENT_MEMORIES,
        },
    )

    classroom_incident_type = scene_lib.SceneTypeSpec(
        name='classroom_incident',
        game_master_name='school_life_rules',
        default_premise={
            'Mr. Thompson': [
                'It is Friday afternoon. You are handing back graded math tests. Lucas failed again. You feel the need to remind him to work harder in front of the class.'
            ],
            'Lucas': [
                "It is Friday afternoon. You receive your failed math test. You feel humiliated and terrified of your mother's reaction. You just want to disappear."
            ],
            'Leo': [
                'You see Lucas got a bad grade. You find it funny and plan to make a sarcastic comment to make others laugh.'
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. The teacher hands back tests. React to the grades and the social situation. If the scene goal is achieved, append [END]."
            )
        ),
        possible_participants=['Mr. Thompson', 'Lucas', 'Leo'],
    )
    home_confrontation_type = scene_lib.SceneTypeSpec(
        name='home_confrontation',
        game_master_name='school_life_rules',
        default_premise={
            'Sarah': [
                "It is Friday evening. You saw Lucas's grade online. You are angry and worried about his future. You confront him when he comes out of his room."
            ],
            'Lucas': [
                "It is Friday evening. You are trying to get water from the kitchen, hoping to avoid your mother, but she is waiting for you."
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. Discuss the test results. Mother presses for improvement; Son reacts to the pressure. Append [END] when conversation concludes."
            )
        ),
        possible_participants=['Sarah', 'Lucas'],
    )
    morning_decision_type = scene_lib.SceneTypeSpec(
        name='morning_decision',
        game_master_name='school_life_rules',
        default_premise={
            'Sarah': [
                "It is Monday morning, 7:00 AM. You knock on Lucas's door to wake him up for school. You expect him to be ready."
            ],
            'Lucas': [
                'It is Monday morning, 7:00 AM. The alarm rings. The thought of going back to school makes your stomach hurt physically. You have to decide whether to get up or refuse.'
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. Morning routine interaction. Lucas decides whether to go to school or stay in bed. Append [END] after the final decision."
            )
        ),
        possible_participants=['Sarah', 'Lucas'],
    )

    scenes_baseline = [
        scene_lib.SceneSpec(scene_type=classroom_incident_type, participants=['Mr. Thompson', 'Lucas', 'Leo'], num_rounds=6),
        scene_lib.SceneSpec(scene_type=home_confrontation_type, participants=['Sarah', 'Lucas'], num_rounds=6),
        scene_lib.SceneSpec(scene_type=morning_decision_type, participants=['Sarah', 'Lucas'], num_rounds=6),
    ]
    dialogic_gm = builder.build_dialogic_and_dramaturgic_game_master(
        name='school_life_rules',
        entities=entities,
        scenes=scenes_baseline,
    )

    log = []
    total_rounds = sum(s.num_rounds for s in scenes_baseline)
    builder.run_with_sequential_engine(
        game_masters=[initializer, dialogic_gm],
        entities=entities,
        premise='The simulation tracks Lucas\'s path regarding school attendance.',
        max_steps=total_rounds,
        verbose=True,
        log=log,
    )

    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    out_dir = os.path.join('results', 'the_path_to_school_refusal', f'run_{ts}', 'condition_baseline')
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, 'simulation_events.jsonl')
    windows = []
    current = 1
    for s in scenes_baseline:
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
    print(f'Logs written to {out_file}')

    def _parse_options(action_spec_str: str) -> list[str]:
        parts = action_spec_str.split(';;')
        for p in parts:
            if p.strip().startswith('options:'):
                _, val = p.split(':', 1)
                return [x.strip() for x in val.split(',') if x.strip()]
        return []

    def _responder(player_name: str, action_spec_str: str) -> str:
        opts = _parse_options(action_spec_str)
        if opts:
            mid = len(opts) // 2
            return opts[mid]
        return ''

    questionnaires = [DASS21Questionnaire(), SRASRQuestionnaire(), PSS10Questionnaire()]
    surveyor = EduMirrorSurveyor(questionnaires, ['Lucas'])
    df = surveyor.run_once(_responder)
    surveyor.save_results(df, out_dir, 'lucas_post_baseline')


def run_interventions() -> None:
    model_config = create_model_config_from_environment('production', disable_language_model=True)
    model = create_language_model(model_config)
    embedder = create_simple_embedder()
    entities = create_agents(model, embedder)

    builder = SceneBuilder(model=model, embedder_model=embedder)

    initializer_params = {
        'next_game_master_name': 'school_life_rules',
        'shared_memories': [
            'Lucas has been struggling with math recently.',
            'The mid-term exams were held yesterday.',
            'Leo sits behind Lucas in class.',
        ],
        'player_specific_context': {
            'Lucas': 'student',
            'Sarah': 'parent',
            'Mr. Thompson': 'teacher',
            'Leo': 'student',
        },
        'player_specific_memories': AGENT_MEMORIES,
    }

    classroom_incident_type = scene_lib.SceneTypeSpec(
        name='classroom_incident',
        game_master_name='school_life_rules',
        default_premise={
            'Mr. Thompson': [
                'It is Friday afternoon. You are handing back graded math tests. Lucas failed again. You feel the need to remind him to work harder in front of the class.'
            ],
            'Lucas': [
                "It is Friday afternoon. You receive your failed math test. You feel humiliated and terrified of your mother's reaction. You just want to disappear."
            ],
            'Leo': [
                'You see Lucas got a bad grade. You find it funny and plan to make a sarcastic comment to make others laugh.'
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. The teacher hands back tests. React to the grades and the social situation. If the scene goal is achieved, append [END]."
            )
        ),
        possible_participants=['Mr. Thompson', 'Lucas', 'Leo'],
    )
    home_confrontation_type = scene_lib.SceneTypeSpec(
        name='home_confrontation',
        game_master_name='school_life_rules',
        default_premise={
            'Sarah': [
                "It is Friday evening. You saw Lucas's grade online. You are angry and worried about his future. You confront him when he comes out of his room."
            ],
            'Lucas': [
                "It is Friday evening. You are trying to get water from the kitchen, hoping to avoid your mother, but she is waiting for you."
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. Discuss the test results. Mother presses for improvement; Son reacts to the pressure. Append [END] when conversation concludes."
            )
        ),
        possible_participants=['Sarah', 'Lucas'],
    )
    morning_decision_type = scene_lib.SceneTypeSpec(
        name='morning_decision',
        game_master_name='school_life_rules',
        default_premise={
            'Sarah': [
                "It is Monday morning, 7:00 AM. You knock on Lucas's door to wake him up for school. You expect him to be ready."
            ],
            'Lucas': [
                'It is Monday morning, 7:00 AM. The alarm rings. The thought of going back to school makes your stomach hurt physically. You have to decide whether to get up or refuse.'
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. Morning routine interaction. Lucas decides whether to go to school or stay in bed. Append [END] after the final decision."
            )
        ),
        possible_participants=['Sarah', 'Lucas'],
    )

    teacher_mentoring_type = scene_lib.SceneTypeSpec(
        name='teacher_mentoring',
        game_master_name='school_life_rules',
        default_premise={
            'Mr. Thompson': [
                'It is Friday after class. You noticed Lucas looked devastated. Instead of scolding, you decide to ask him how he is feeling personally, validating his struggle.'
            ],
            'Lucas': [
                'Class is over. You are packing slowly, feeling hopeless. Mr. Thompson calls your name. You expect another lecture, but his tone seems different.'
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. A private conversation. Teacher offers emotional support; Student responds. Append [END] when the conversation closes."
            )
        ),
        possible_participants=['Mr. Thompson', 'Lucas'],
    )
    teacher_parent_call_type = scene_lib.SceneTypeSpec(
        name='teacher_parent_call',
        game_master_name='school_life_rules',
        default_premise={
            'Mr. Thompson': [
                "Call Sarah to discuss Lucas's needs and emphasize emotional support over grades."
            ],
            'Sarah': [
                'Share concerns and consider guidance on supporting Lucas without increasing pressure.'
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. On phone, discuss youth social needs and family stress in a supportive way. Append [END] when aligned."
            )
        ),
        possible_participants=['Sarah', 'Mr. Thompson'],
    )
    class_climate_intervention_type = scene_lib.SceneTypeSpec(
        name='class_climate_intervention',
        game_master_name='school_life_rules',
        default_premise={
            'Mr. Thompson': [
                'Organize a brief class meeting to emphasize respect and mutual help, discouraging ridicule.'
            ],
            'Lucas': [
                'Consider sharing views and listen to peers. Reflect on inclusive alternatives for activities.'
            ],
            'Leo': [
                'Reflect on behavior and consider more respectful interactions.'
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. In class meeting, discuss friendship meaning and inclusive ideas. Append [END] when consensus emerges."
            )
        ),
        possible_participants=['Lucas', 'Leo', 'Mr. Thompson'],
    )

    pre_scenes = [
        scene_lib.SceneSpec(scene_type=classroom_incident_type, participants=['Mr. Thompson', 'Lucas', 'Leo'], num_rounds=6),
    ]
    post_scenes = [
        scene_lib.SceneSpec(scene_type=home_confrontation_type, participants=['Sarah', 'Lucas'], num_rounds=6),
        scene_lib.SceneSpec(scene_type=morning_decision_type, participants=['Sarah', 'Lucas'], num_rounds=6),
    ]
    i1 = scene_lib.SceneSpec(scene_type=teacher_mentoring_type, participants=['Mr. Thompson', 'Lucas'], num_rounds=8)
    i2 = scene_lib.SceneSpec(scene_type=teacher_parent_call_type, participants=['Sarah', 'Mr. Thompson'], num_rounds=6)
    i3 = scene_lib.SceneSpec(scene_type=class_climate_intervention_type, participants=['Lucas', 'Leo', 'Mr. Thompson'], num_rounds=8)

    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_root = os.path.join('results', 'the_path_to_school_refusal', f'run_{ts}')

    def _run_branch_and_write(scenes: list[scene_lib.SceneSpec], out_dir: str, prefix: str) -> None:
        initializer = builder.build_initializer_game_master(
            name='initial setup rules',
            entities=entities,
            params=initializer_params,
        )
        gm = builder.build_dialogic_and_dramaturgic_game_master(
            name='school_life_rules',
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

        def _parse_options(action_spec_str: str) -> list[str]:
            parts = action_spec_str.split(';;')
            for p in parts:
                if p.strip().startswith('options:'):
                    _, val = p.split(':', 1)
                    return [x.strip() for x in val.split(',') if x.strip()]
            return []

        def _responder(player_name: str, action_spec_str: str) -> str:
            opts = _parse_options(action_spec_str)
            if opts:
                mid = len(opts) // 2
                return opts[mid]
            return ''

        questionnaires = [DASS21Questionnaire(), SRASRQuestionnaire(), PSS10Questionnaire()]
        surveyor = EduMirrorSurveyor(questionnaires, ['Lucas'])
        df = surveyor.run_once(_responder)
        surveyor.save_results(df, out_dir, prefix)

    _run_branch_and_write([*pre_scenes, i1, *post_scenes], os.path.join(output_root, 'condition_teacher_mentoring'), 'lucas_post_teacher_mentoring')
    _run_branch_and_write([*pre_scenes, i2, *post_scenes], os.path.join(output_root, 'condition_teacher_parent_call'), 'lucas_post_teacher_parent_call')
    _run_branch_and_write([*pre_scenes, i3, *post_scenes], os.path.join(output_root, 'condition_class_climate_intervention'), 'lucas_post_class_climate_intervention')


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'baseline':
        run_baseline()
    elif len(sys.argv) > 1 and sys.argv[1] == 'interventions':
        run_interventions()
    else:
        run_baseline()
        run_interventions()

