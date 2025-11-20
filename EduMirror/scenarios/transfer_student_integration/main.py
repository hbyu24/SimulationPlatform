from datetime import datetime
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from concordia.environment.engines.sequential import Sequential
from concordia.typing import scene as scene_lib
from concordia.typing import entity as entity_lib
from common.simulation_utils.model_setup import create_language_model, create_simple_embedder, create_model_config_from_environment
from common.simulation_utils.scene_builder import SceneBuilder
from scenarios.transfer_student_integration.agents import create_agents, AGENT_MEMORIES
import json
from common.measurement import EduMirrorSurveyor
from common.measurement.rater import EduMirrorRater
from common.measurement.questionnaire.pss10 import PSS10Questionnaire
from common.measurement.questionnaire.pssm_short import PSSMShortQuestionnaire
from common.measurement.rubrics.peer_social_acceptance import get_peer_social_acceptance_rubric
from common.measurement.rubrics.social_initiation import get_social_initiation_rubric


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
                'Max': 'student',
                'Tom': 'student',
                'Mr. Zhang': 'teacher',
            },
            'player_specific_memories': AGENT_MEMORIES,
        },
    )

    dorm_type = scene_lib.SceneTypeSpec(
        name='dormitory_night',
        game_master_name='conversation rules',
        default_premise={
            'Leo': [
                'It is your first night in the dorm. You are unpacking slowly. You hear Max and Tom laughing about something you do not understand. You feel awkward and want to join but are afraid of being ignored. You try to find a safe topic to start a conversation.'
            ],
            'Max': [
                "You are chatting with Tom about last week's match. You notice the new guy Leo listening. You decide to either ignore him to show who is boss or test him with a tricky question or joke."
            ],
            'Tom': [
                'You are chatting with Max. You see Leo alone. You feel a bit sorry for him but wait for Max’s lead.'
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. Interaction in the dorm before lights out. Respond to roommates' actions. Leo decides whether to speak up. Max decides whether to include Leo. If the lights-out bell rings or conversation ends naturally, append [END]."
            )
        ),
        possible_participants=['Leo', 'Max', 'Tom'],
    )

    cafeteria_type = scene_lib.SceneTypeSpec(
        name='cafeteria_lunch',
        game_master_name='conversation rules',
        default_premise={
            'Leo': [
                'It is lunch time. You enter the cafeteria holding your tray. You see Max and Tom sitting at a table. You need to decide whether to approach them and ask to sit, or find an empty table alone based on how you feel about last night.'
            ],
            'Max': [
                'You are eating with Tom. You see Leo looking for a seat. Based on your current attitude towards him, you either wave him over, ignore him, or tell him the seat is taken.'
            ],
            'Tom': [
                'You see Leo. You react based on Max’s reaction and your own feelings.'
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. Lunch time interaction. Leo chooses where to sit. Max and Tom react to his approach. The scene ends when Leo starts eating (either with the group or alone). Append [END] when done."
            )
        ),
        possible_participants=['Leo', 'Max', 'Tom'],
    )

    scenes_for_dialogic = [
        scene_lib.SceneSpec(scene_type=dorm_type, participants=['Leo', 'Max', 'Tom'], num_rounds=6),
        scene_lib.SceneSpec(scene_type=cafeteria_type, participants=['Leo', 'Max', 'Tom'], num_rounds=4),
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
    out_dir = os.path.join('results', 'transfer_student_integration', f'run_{ts}', 'condition_baseline')
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, 'simulation_events.jsonl')
    scene_windows = [
        (1, scenes_for_dialogic[0].num_rounds, 'dormitory_night', ['Leo','Max','Tom']),
        (scenes_for_dialogic[0].num_rounds + 1,
         scenes_for_dialogic[0].num_rounds + scenes_for_dialogic[1].num_rounds,
         'cafeteria_lunch', ['Leo','Max','Tom']),
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
        for candidate in ('Neutral',):
            if candidate in options:
                return candidate
        return options[len(options) // 2] if options else ''

    questionnaires = [PSSMShortQuestionnaire(), PSS10Questionnaire()]
    surveyor = EduMirrorSurveyor(questionnaires, ['Leo'])
    results_df = surveyor.run_once(_measurement_responder)
    surveyor.save_results(results_df, out_dir, 'leo_post_baseline')

    rater = EduMirrorRater(model)
    transcript = rater.load_transcript(out_file)
    df_accept_max = rater.analyze_transcript(transcript, get_peer_social_acceptance_rubric(target_agent='Max'))
    rater.save_results(df_accept_max, out_dir, 'rubric_peer_acceptance_max')
    df_accept_tom = rater.analyze_transcript(transcript, get_peer_social_acceptance_rubric(target_agent='Tom'))
    rater.save_results(df_accept_tom, out_dir, 'rubric_peer_acceptance_tom')
    df_initiation_leo = rater.analyze_transcript(transcript, get_social_initiation_rubric(target_agent='Leo'))
    rater.save_results(df_initiation_leo, out_dir, 'rubric_social_initiation_leo')


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
            'Max': 'student',
            'Tom': 'student',
            'Mr. Zhang': 'teacher',
        },
        'player_specific_memories': AGENT_MEMORIES,
    }

    dorm_type = scene_lib.SceneTypeSpec(
        name='dormitory_night',
        game_master_name='conversation rules',
        default_premise={
            'Leo': [
                'It is your first night in the dorm. You are unpacking slowly. You hear Max and Tom laughing about something you do not understand. You feel awkward and want to join but are afraid of being ignored. You try to find a safe topic to start a conversation.'
            ],
            'Max': [
                "You are chatting with Tom about last week's match. You notice the new guy Leo listening. You decide to either ignore him to show who is boss or test him with a tricky question or joke."
            ],
            'Tom': [
                'You are chatting with Max. You see Leo alone. You feel a bit sorry for him but wait for Max’s lead.'
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. Interaction in the dorm before lights out. Respond to roommates' actions. Leo decides whether to speak up. Max decides whether to include Leo. If the lights-out bell rings or conversation ends naturally, append [END]."
            )
        ),
        possible_participants=['Leo', 'Max', 'Tom'],
    )

    cafeteria_type = scene_lib.SceneTypeSpec(
        name='cafeteria_lunch',
        game_master_name='conversation rules',
        default_premise={
            'Leo': [
                'It is lunch time. You enter the cafeteria holding your tray. You see Max and Tom sitting at a table. You need to decide whether to approach them and ask to sit, or find an empty table alone based on how you feel about last night.'
            ],
            'Max': [
                'You are eating with Tom. You see Leo looking for a seat. Based on your current attitude towards him, you either wave him over, ignore him, or tell him the seat is taken.'
            ],
            'Tom': [
                'You see Leo. You react based on Max’s reaction and your own feelings.'
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. Lunch time interaction. Leo chooses where to sit. Max and Tom react to his approach. The scene ends when Leo starts eating (either with the group or alone). Append [END] when done."
            )
        ),
        possible_participants=['Leo', 'Max', 'Tom'],
    )

    teacher_student_talk_type = scene_lib.SceneTypeSpec(
        name='teacher_student_talk',
        game_master_name='conversation rules',
        default_premise={
            'Mr. Zhang': [
                'You call Leo out for a private chat. You noticed he looked isolated. Your goal is to validate his feelings, encourage him to share his guitar hobby as an icebreaker, and boost his confidence.'
            ],
            'Leo': [
                'The teacher calls you out. You feel nervous but also relieved to have someone to talk to. You share your worries about Max and the group.'
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. In a private talk, have a supportive conversation and explore confidence-building actions. Append [END] when a clear plan emerges."
            )
        ),
        possible_participants=['Leo', 'Mr. Zhang'],
    )

    peer_mediation_type = scene_lib.SceneTypeSpec(
        name='peer_mediation',
        game_master_name='conversation rules',
        default_premise={
            'Mr. Zhang': [
                "You speak to Max privately. You acknowledge his leadership in the dorm but assign him a 'responsibility': to help Leo get familiar with the dorm rules. You frame inclusivity as a sign of maturity."
            ],
            'Max': [
                "The teacher talks to you. You initially feel defensive but then feel a sense of responsibility and pride when given a 'mission' to lead the new guy."
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. In a private talk, discuss responsibility and inclusive leadership. Append [END] when aligned."
            )
        ),
        possible_participants=['Max', 'Mr. Zhang'],
    )

    structured_group_activity_type = scene_lib.SceneTypeSpec(
        name='structured_group_activity',
        game_master_name='conversation rules',
        default_premise={
            'Mr. Zhang': [
                "You organize a quick 'Dorm Night' activity where everyone must share one 'unpopular opinion' or a hobby. You ensure everyone gets equal speaking time."
            ],
            'Leo': [
                'Participate in the sharing circle. Listen to others.'
            ],
            'Max': [
                'Participate in the sharing circle. Listen to others.'
            ],
            'Tom': [
                'Participate in the sharing circle. Listen to others.'
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. In the structured activity, share and listen equally. Append [END] when the sharing finishes."
            )
        ),
        possible_participants=['Leo', 'Max', 'Tom', 'Mr. Zhang'],
    )

    pre_scenes = [
        scene_lib.SceneSpec(scene_type=dorm_type, participants=['Leo', 'Max', 'Tom'], num_rounds=6),
    ]
    post_scenes = [
        scene_lib.SceneSpec(scene_type=cafeteria_type, participants=['Leo', 'Max', 'Tom'], num_rounds=4),
    ]
    i1 = scene_lib.SceneSpec(scene_type=teacher_student_talk_type, participants=['Leo', 'Mr. Zhang'], num_rounds=6)
    i2 = scene_lib.SceneSpec(scene_type=peer_mediation_type, participants=['Max', 'Mr. Zhang'], num_rounds=6)
    i3 = scene_lib.SceneSpec(scene_type=structured_group_activity_type, participants=['Leo', 'Max', 'Tom', 'Mr. Zhang'], num_rounds=8)

    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_root = os.path.join('results', 'transfer_student_integration', f'run_{ts}')

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
            for c in ('Neutral',):
                if c in opts:
                    return c
            return opts[len(opts) // 2] if opts else ''

        questionnaires = [PSSMShortQuestionnaire(), PSS10Questionnaire()]
        surveyor = EduMirrorSurveyor(questionnaires, ['Leo'])
        df = surveyor.run_once(_responder)
        surveyor.save_results(df, out_dir, prefix)

        rater = EduMirrorRater(model)
        transcript = rater.load_transcript(out_file)
        df_accept_max = rater.analyze_transcript(transcript, get_peer_social_acceptance_rubric(target_agent='Max'))
        rater.save_results(df_accept_max, out_dir, f'{prefix}_rubric_peer_acceptance_max')
        df_accept_tom = rater.analyze_transcript(transcript, get_peer_social_acceptance_rubric(target_agent='Tom'))
        rater.save_results(df_accept_tom, out_dir, f'{prefix}_rubric_peer_acceptance_tom')
        df_initiation_leo = rater.analyze_transcript(transcript, get_social_initiation_rubric(target_agent='Leo'))
        rater.save_results(df_initiation_leo, out_dir, f'{prefix}_rubric_social_initiation_leo')

    _run_branch_and_write([*pre_scenes, *post_scenes], os.path.join(output_root, 'condition_baseline'), 'leo_post_baseline')
    _run_branch_and_write([*pre_scenes, i1, *post_scenes], os.path.join(output_root, 'condition_teacher_student_talk'), 'leo_post_teacher_student_talk')
    _run_branch_and_write([*pre_scenes, i2, *post_scenes], os.path.join(output_root, 'condition_peer_mediation'), 'leo_post_peer_mediation')
    _run_branch_and_write([*pre_scenes, i3, *post_scenes], os.path.join(output_root, 'condition_structured_group_activity'), 'leo_post_structured_group_activity')


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'baseline':
        run_baseline()
    elif len(sys.argv) > 1 and sys.argv[1] == 'interventions':
        run_interventions()
    else:
        run_baseline()
        run_interventions()
