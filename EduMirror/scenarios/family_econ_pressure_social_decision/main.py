from datetime import datetime, timedelta
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from concordia.environment.engines.sequential import Sequential
from concordia.typing import scene as scene_lib
from concordia.typing import entity as entity_lib
from common.simulation_utils.model_setup import create_language_model, create_simple_embedder, create_model_config_from_environment
from common.simulation_utils.scene_builder import SceneBuilder
from scenarios.family_econ_pressure_social_decision.agents import create_agents, AGENT_MEMORIES
import json
import os
from common.measurement import EduMirrorSurveyor
from common.measurement.questionnaire import IncomQuestionnaire, RSESQuestionnaire, SPINQuestionnaire
from common.simulation_utils import InterventionScenarioRunner, InterventionSpec


def run_baseline() -> None:
    model_config = create_model_config_from_environment('production')
    model = create_language_model(model_config)
    embedder = create_simple_embedder()
    entities = create_agents(model, embedder)
    name_to_entity = {e.name: e for e in entities}

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
                'Sam': 'parent',
                'Mr. Davis': 'teacher',
            },
            'player_specific_memories': AGENT_MEMORIES,
        },
    )

    cafeteria_type = scene_lib.SceneTypeSpec(
        name='cafeteria_invite',
        game_master_name='conversation rules',
        default_premise={
            'Alex': [
                'It is lunchtime at the school cafeteria. Chloe is excited and proposes a weekend trip with a budget of about 2000 per person. You feel interested but hesitant and consider discussing with your parent first.'
            ],
            'Ben': [
                'It is lunchtime at the school cafeteria. Chloe proposes a weekend trip with a budget of about 2000 per person. You immediately find the idea attractive and are inclined to join.'
            ],
            'Chloe': [
                'You enthusiastically propose a weekend trip plan to Alex and Ben, mentioning a budget around 2000 per person and asking if they want to join.'
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. At the cafeteria, respond to the weekend trip invitation and advance toward a decision or next detail. If the scene goal is achieved, append [END] at the end."
            )
        ),
        possible_participants=['Alex', 'Ben', 'Chloe'],
    )
    family_type = scene_lib.SceneTypeSpec(
        name='family_discussion',
        game_master_name='conversation rules',
        default_premise={
            'Alex': [
                'It is evening at home. You present the weekend trip plan and required expenses to your father Sam, explaining your wish to join and asking for guidance.'
            ],
            'Sam': [
                'Your child Alex asks about joining a weekend trip that costs money. You inquire details about time, place, and participants. You also consider the current financial stress and how to respond with care.'
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. At home in the evening, discuss the trip cost and provide a clear stance with reasoning. If the scene goal is achieved, append [END] at the end."
            )
        ),
        possible_participants=['Alex', 'Sam'],
    )
    classroom_type = scene_lib.SceneTypeSpec(
        name='classroom_decision',
        game_master_name='conversation rules',
        default_premise={
            'Alex': [
                'The next day in the classroom, Ben and Chloe ask about your final decision on the weekend trip. You need to give a clear answer and may choose to be honest about family financial stress or provide another reason.'
            ],
            'Ben': [
                'In the classroom, you ask Alex for a final decision about the weekend trip and respond with understanding to whatever Alex says.'
            ],
            'Chloe': [
                'In the classroom, you ask Alex for a final decision about the weekend trip and react to Alex’s response. Consider alternative plans if needed.'
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. In class next day, ask or respond with the final decision and, if needed, propose an alternative. If the scene goal is achieved, append [END] at the end."
            )
        ),
        possible_participants=['Alex', 'Ben', 'Chloe'],
    )
    scenes_for_dialogic = [
        scene_lib.SceneSpec(scene_type=cafeteria_type, participants=['Alex', 'Ben', 'Chloe'], num_rounds=3),
        scene_lib.SceneSpec(scene_type=family_type, participants=['Alex', 'Sam'], num_rounds=4),
        scene_lib.SceneSpec(scene_type=classroom_type, participants=['Alex', 'Ben', 'Chloe'], num_rounds=3),
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
    out_dir = os.path.join('results', 'family_econ_pressure_social_decision', f'run_{ts}', 'condition_baseline')
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, 'simulation_events.jsonl')
    scene_windows = [
        (1, scenes_for_dialogic[0].num_rounds, 'cafeteria_invite', ['Alex','Ben','Chloe']),
        (scenes_for_dialogic[0].num_rounds + 1,
         scenes_for_dialogic[0].num_rounds + scenes_for_dialogic[1].num_rounds,
         'family_discussion', ['Alex','Sam']),
        (scenes_for_dialogic[0].num_rounds + scenes_for_dialogic[1].num_rounds + 1,
         scenes_for_dialogic[0].num_rounds + scenes_for_dialogic[1].num_rounds + scenes_for_dialogic[2].num_rounds,
         'classroom_decision', ['Alex','Ben','Chloe']),
    ]
    with open(out_file, 'w', encoding='utf-8') as f:
        for entry in log:
            step = entry.get('Step')
            summary = entry.get('Summary','')
            event_text = ''
            if '---' in summary:
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
    print(f'Logs written to {out_file}')

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

    questionnaires = [IncomQuestionnaire(), RSESQuestionnaire(), SPINQuestionnaire()]
    surveyor = EduMirrorSurveyor(questionnaires, ['Alex'])
    results_df = surveyor.run_once(_measurement_responder)
    survey_out_dir = os.path.join('results', 'family_econ_pressure_social_decision', f'run_{ts}', 'condition_baseline')
    surveyor.save_results(results_df, survey_out_dir, 'alex_post_baseline')
    # Baseline ends here.


def run_interventions() -> None:
    model_config = create_model_config_from_environment('production', disable_language_model=False)
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
            'Sam': 'parent',
            'Mr. Davis': 'teacher',
        },
        'player_specific_memories': AGENT_MEMORIES,
    }

    cafeteria_type = scene_lib.SceneTypeSpec(
        name='cafeteria_invite',
        game_master_name='conversation rules',
        default_premise={
            'Alex': [
                'It is lunchtime at the school cafeteria. Chloe is excited and proposes a weekend trip with a budget of about 2000 per person. You feel interested but hesitant and consider discussing with your parent first.'
            ],
            'Ben': [
                'It is lunchtime at the school cafeteria. Chloe proposes a weekend trip with a budget of about 2000 per person. You immediately find the idea attractive and are inclined to join.'
            ],
            'Chloe': [
                'You enthusiastically propose a weekend trip plan to Alex and Ben, mentioning a budget around 2000 per person and asking if they want to join.'
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. At the cafeteria, respond to the weekend trip invitation and advance toward a decision or next detail. If the scene goal is achieved, append [END] at the end."
            )
        ),
        possible_participants=['Alex', 'Ben', 'Chloe'],
    )
    family_type = scene_lib.SceneTypeSpec(
        name='family_discussion',
        game_master_name='conversation rules',
        default_premise={
            'Alex': [
                'It is evening at home. You present the weekend trip plan and required expenses to your father Sam, explaining your wish to join and asking for guidance.'
            ],
            'Sam': [
                'Your child Alex asks about joining a weekend trip that costs money. You inquire details about time, place, and participants. You also consider the current financial stress and how to respond with care.'
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. At home in the evening, discuss the trip cost and provide a clear stance with reasoning. If the scene goal is achieved, append [END] at the end."
            )
        ),
        possible_participants=['Alex', 'Sam'],
    )
    classroom_type = scene_lib.SceneTypeSpec(
        name='classroom_decision',
        game_master_name='conversation rules',
        default_premise={
            'Alex': [
                'The next day in the classroom, Ben and Chloe ask about your final decision on the weekend trip. You need to give a clear answer and may choose to be honest about family financial stress or provide another reason.'
            ],
            'Ben': [
                'In the classroom, you ask Alex for a final decision about the weekend trip and respond with understanding to whatever Alex says.'
            ],
            'Chloe': [
                'In the classroom, you ask Alex for a final decision about the weekend trip and react to Alex’s response. Consider alternative plans if needed.'
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. In class next day, ask or respond with the final decision and, if needed, propose an alternative. If the scene goal is achieved, append [END] at the end."
            )
        ),
        possible_participants=['Alex', 'Ben', 'Chloe'],
    )

    teacher_student_talk_type = scene_lib.SceneTypeSpec(
        name='teacher_student_talk',
        game_master_name='conversation rules',
        default_premise={
            'Mr. Davis': [
                'Invite Alex to a private talk about friendship and financial stress. Encourage open communication and reassure him that true friends understand economic differences.'
            ],
            'Alex': [
                'Share your hesitation about the weekend trip and concerns about family finances. Consider how to communicate honestly with your friends.'
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. In the teacher office, have a supportive conversation and explore honest communication strategies. Append [END] when clear plan emerges."
            )
        ),
        possible_participants=['Alex', 'Mr. Davis'],
    )
    teacher_parent_call_type = scene_lib.SceneTypeSpec(
        name='teacher_parent_call',
        game_master_name='conversation rules',
        default_premise={
            'Mr. Davis': [
                'Call Sam to discuss Alex’s social needs and the importance of emotional support under financial pressure.'
            ],
            'Sam': [
                'Share current economic stress and concerns. Consider guidance on supporting Alex’s social life without increasing financial burden.'
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. On phone, discuss youth social needs and family stress in a supportive way. Append [END] when aligned."
            )
        ),
        possible_participants=['Sam', 'Mr. Davis'],
    )
    class_meeting_type = scene_lib.SceneTypeSpec(
        name='class_meeting',
        game_master_name='conversation rules',
        default_premise={
            'Mr. Davis': [
                'Organize a class meeting on meanings of friendship, highlighting respect and inclusion beyond consumption.'
            ],
            'Alex': [
                'Consider sharing views and listen to peers. Reflect on inclusive alternatives for social activities.'
            ],
            'Ben': [
                'Share experiences of low-cost activities and emphasize care for friends under financial stress.'
            ],
            'Chloe': [
                'Reflect on economic differences sensitively and propose inclusive ideas.'
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. In class meeting, discuss friendship meaning and inclusive activity ideas. Append [END] when consensus emerges."
            )
        ),
        possible_participants=['Alex', 'Ben', 'Chloe', 'Mr. Davis'],
    )

    pre_scenes = [
        scene_lib.SceneSpec(scene_type=cafeteria_type, participants=['Alex', 'Ben', 'Chloe'], num_rounds=3),
    ]
    post_scenes = [
        scene_lib.SceneSpec(scene_type=family_type, participants=['Alex', 'Sam'], num_rounds=4),
        scene_lib.SceneSpec(scene_type=classroom_type, participants=['Alex', 'Ben', 'Chloe'], num_rounds=3),
    ]
    i1 = scene_lib.SceneSpec(scene_type=teacher_student_talk_type, participants=['Alex', 'Mr. Davis'], num_rounds=6)
    i2 = scene_lib.SceneSpec(scene_type=teacher_parent_call_type, participants=['Sam', 'Mr. Davis'], num_rounds=6)
    i3 = scene_lib.SceneSpec(scene_type=class_meeting_type, participants=['Alex', 'Ben', 'Chloe', 'Mr. Davis'], num_rounds=8)

    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_root = os.path.join('results', 'family_econ_pressure_social_decision', f'run_{ts}')

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

        questionnaires = [IncomQuestionnaire(), RSESQuestionnaire(), SPINQuestionnaire()]
        surveyor = EduMirrorSurveyor(questionnaires, ['Alex'])
        df = surveyor.run_once(_responder)
        surveyor.save_results(df, out_dir, prefix)

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