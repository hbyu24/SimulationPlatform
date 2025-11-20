from datetime import datetime
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from concordia.environment.engines.sequential import Sequential
from concordia.typing import scene as scene_lib
from concordia.typing import entity as entity_lib
from common.simulation_utils.model_setup import create_language_model, create_simple_embedder, create_model_config_from_environment
from common.simulation_utils.scene_builder import SceneBuilder
from scenarios.collaborative_iep_meeting.agents import create_agents, AGENT_MEMORIES
import json
from common.measurement import EduMirrorSurveyor
from common.measurement.questionnaire.pssm_short import PSSMShortQuestionnaire
from common.measurement.questionnaire.fsps import FSPSQuestionnaire

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
                'Sarah': 'parent',
                'Mrs. Thompson': 'teacher',
                'Mr. Baker': 'coordinator',
            },
            'player_specific_memories': AGENT_MEMORIES,
        },
    )

    pre_meeting_type = scene_lib.SceneTypeSpec(
        name='pre_meeting_tension',
        game_master_name='conversation rules',
        default_premise={
            'Mrs. Thompson': [
                "You are frustrated. Leo failed another math test and disrupted the class today. You expect the meeting with his mother Sarah to be another argument and want Mr. Baker to support stricter discipline."
            ],
            'Mr. Baker': [
                "You are reviewing Leo's file and see a gap between potential and performance. You want to prepare Mrs. Thompson for the meeting, but she seems defensive."
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. In the teacher office, discuss Leo's recent behavior and define your stance for the upcoming IEP meeting. Append [END] when readiness is established."
            )
        ),
        possible_participants=['Mrs. Thompson', 'Mr. Baker'],
    )
    iep_meeting_type = scene_lib.SceneTypeSpec(
        name='conflicted_iep_meeting',
        game_master_name='conversation rules',
        default_premise={
            'Sarah': [
                "You arrive anxious and defensive. You believe the teacher dislikes Leo and you are ready to fight against any suggestion that Leo is lazy or needs punishment."
            ],
            'Mrs. Thompson': [
                "You bring disciplinary records to prove Leo's behavior is unacceptable and needs home consequences."
            ],
            'Mr. Baker': [
                "You try to mediate, but tension is high from the start."
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. Conduct the IEP meeting, discuss issues, propose goals, and try to reach agreement. Append [END] when the meeting concludes (successful or not)."
            )
        ),
        possible_participants=['Sarah', 'Mrs. Thompson', 'Mr. Baker'],
    )
    home_fallout_type = scene_lib.SceneTypeSpec(
        name='home_fallout',
        game_master_name='conversation rules',
        default_premise={
            'Sarah': [
                "You are exhausted and angry after the meeting and feel helpless. You need to talk to Leo about what happened, likely conveying frustration with the school."
            ],
            'Leo': [
                "You wait anxiously to hear about the meeting and fear you are in trouble again."
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. At home, discuss the outcome of the school meeting and reveal impact on parent-child relationship and Leo's self-esteem. Append [END]."
            )
        ),
        possible_participants=['Sarah', 'Leo'],
    )

    scenes = [
        scene_lib.SceneSpec(scene_type=pre_meeting_type, participants=['Mrs. Thompson', 'Mr. Baker'], num_rounds=3),
        scene_lib.SceneSpec(scene_type=iep_meeting_type, participants=['Sarah', 'Mrs. Thompson', 'Mr. Baker'], num_rounds=6),
        scene_lib.SceneSpec(scene_type=home_fallout_type, participants=['Sarah', 'Leo'], num_rounds=4),
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
    out_dir = os.path.join('results', 'collaborative_iep_meeting', f'run_{ts}', 'condition_baseline')
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, 'simulation_events.jsonl')
    windows: list[tuple[int,int,str,list[str]]] = []
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

    def _parse_options(action_spec_str: str) -> list[str]:
        parts = action_spec_str.split(';;')
        for p in parts:
            if p.strip().startswith('options:'):
                _, val = p.split(':', 1)
                return [x.strip() for x in val.split(',') if x.strip()]
        return []

    def _measurement_responder(player_name: str, action_spec_str: str) -> str:
        opts = _parse_options(action_spec_str)
        for c in ('Neutral', 'Agree', 'Somewhat', 'A little bit'):
            if c in opts:
                return c
        return opts[len(opts) // 2] if opts else ''

    questionnaires_leo = [PSSMShortQuestionnaire()]
    questionnaires_sarah = [FSPSQuestionnaire()]
    surveyor_leo = EduMirrorSurveyor(questionnaires_leo, ['Leo'])
    surveyor_sarah = EduMirrorSurveyor(questionnaires_sarah, ['Sarah'])
    df_leo = surveyor_leo.run_once(_measurement_responder)
    df_sarah = surveyor_sarah.run_once(_measurement_responder)
    surveyor_leo.save_results(df_leo, out_dir, 'leo_post_baseline')
    surveyor_sarah.save_results(df_sarah, out_dir, 'sarah_post_baseline')

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
            'Sarah': 'parent',
            'Mrs. Thompson': 'teacher',
            'Mr. Baker': 'coordinator',
        },
        'player_specific_memories': AGENT_MEMORIES,
    }

    pre_meeting_type = scene_lib.SceneTypeSpec(
        name='pre_meeting_tension',
        game_master_name='conversation rules',
        default_premise={
            'Mrs. Thompson': [
                "You are frustrated. Leo failed another math test and disrupted the class today. You expect the meeting with his mother Sarah to be another argument and want Mr. Baker to support stricter discipline."
            ],
            'Mr. Baker': [
                "You are reviewing Leo's file and see a gap between potential and performance. You want to prepare Mrs. Thompson for the meeting, but she seems defensive."
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. In the teacher office, discuss Leo's recent behavior and define your stance for the upcoming IEP meeting. Append [END] when readiness is established."
            )
        ),
        possible_participants=['Mrs. Thompson', 'Mr. Baker'],
    )
    iep_meeting_type = scene_lib.SceneTypeSpec(
        name='conflicted_iep_meeting',
        game_master_name='conversation rules',
        default_premise={
            'Sarah': [
                "You arrive anxious and defensive. You believe the teacher dislikes Leo and you are ready to fight against any suggestion that Leo is lazy or needs punishment."
            ],
            'Mrs. Thompson': [
                "You bring disciplinary records to prove Leo's behavior is unacceptable and needs home consequences."
            ],
            'Mr. Baker': [
                "You try to mediate, but tension is high from the start."
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. Conduct the IEP meeting, discuss issues, propose goals, and try to reach agreement. Append [END] when the meeting concludes (successful or not)."
            )
        ),
        possible_participants=['Sarah', 'Mrs. Thompson', 'Mr. Baker'],
    )
    home_fallout_type = scene_lib.SceneTypeSpec(
        name='home_fallout',
        game_master_name='conversation rules',
        default_premise={
            'Sarah': [
                "You are exhausted and angry after the meeting and feel helpless. You need to talk to Leo about what happened, likely conveying frustration with the school."
            ],
            'Leo': [
                "You wait anxiously to hear about the meeting and fear you are in trouble again."
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. At home, discuss the outcome of the school meeting and reveal impact on parent-child relationship and Leo's self-esteem. Append [END]."
            )
        ),
        possible_participants=['Sarah', 'Leo'],
    )

    parent_call_type = scene_lib.SceneTypeSpec(
        name='parent_pre_meeting_call',
        game_master_name='conversation rules',
        default_premise={
            'Mr. Baker': [
                "Call Sarah to prepare for the IEP meeting, listen to her concerns, explain data, and assure the goal is support rather than judgment."
            ],
            'Sarah': [
                "Express fears and distrust, consider Mr. Baker's framing of a supportive meeting."
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. Mr. Baker calls Sarah to build trust and lower defensiveness. Append [END] when aligned."
            )
        ),
        possible_participants=['Mr. Baker', 'Sarah'],
    )
    student_voice_type = scene_lib.SceneTypeSpec(
        name='integrate_student_voice',
        game_master_name='conversation rules',
        default_premise={
            'Mr. Baker': [
                "Interview Leo about learning struggles and strengths, gather student voice quotes to bring into the meeting."
            ],
            'Leo': [
                "Share that you want to learn, attention is hard, and letters dance on the page; consider what helps you."
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. In hallway talk, collect student voice and form a clear plan. Append [END]."
            )
        ),
        possible_participants=['Mr. Baker', 'Leo'],
    )
    teacher_reframe_type = scene_lib.SceneTypeSpec(
        name='teacher_reframing',
        game_master_name='conversation rules',
        default_premise={
            'Mr. Baker': [
                "Discuss Leo's file with Mrs. Thompson, reframe behavior problems as skills deficits and unmet needs using data."
            ],
            'Mrs. Thompson': [
                "Consider support-oriented framing and reduce adversarial stance before the meeting."
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. Reframe the perspective from punishment to support strategies. Append [END] when readiness is established."
            )
        ),
        possible_participants=['Mr. Baker', 'Mrs. Thompson'],
    )

    pre_scenes = [
        scene_lib.SceneSpec(scene_type=pre_meeting_type, participants=['Mrs. Thompson', 'Mr. Baker'], num_rounds=3),
    ]
    post_scenes = [
        scene_lib.SceneSpec(scene_type=iep_meeting_type, participants=['Sarah', 'Mrs. Thompson', 'Mr. Baker'], num_rounds=6),
        scene_lib.SceneSpec(scene_type=home_fallout_type, participants=['Sarah', 'Leo'], num_rounds=4),
    ]

    i1 = scene_lib.SceneSpec(scene_type=parent_call_type, participants=['Mr. Baker', 'Sarah'], num_rounds=6)
    i2 = scene_lib.SceneSpec(scene_type=student_voice_type, participants=['Mr. Baker', 'Leo'], num_rounds=6)
    i3 = scene_lib.SceneSpec(scene_type=teacher_reframe_type, participants=['Mr. Baker', 'Mrs. Thompson'], num_rounds=6)

    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_root = os.path.join('results', 'collaborative_iep_meeting', f'run_{ts}')

    def _run_branch_and_write(scenes: list[scene_lib.SceneSpec], out_dir: str, prefix_leo: str, prefix_sarah: str) -> None:
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

        questionnaires_leo = [PSSMShortQuestionnaire()]
        questionnaires_sarah = [FSPSQuestionnaire()]
        surveyor_leo = EduMirrorSurveyor(questionnaires_leo, ['Leo'])
        surveyor_sarah = EduMirrorSurveyor(questionnaires_sarah, ['Sarah'])
        df_leo = surveyor_leo.run_once(_responder)
        df_sarah = surveyor_sarah.run_once(_responder)
        surveyor_leo.save_results(df_leo, out_dir, prefix_leo)
        surveyor_sarah.save_results(df_sarah, out_dir, prefix_sarah)

    _run_branch_and_write([*pre_scenes, i1, *post_scenes], os.path.join(output_root, 'condition_parent_pre_meeting_call'), 'leo_post_parent_call', 'sarah_post_parent_call')
    _run_branch_and_write([*pre_scenes, i2, *post_scenes], os.path.join(output_root, 'condition_integrate_student_voice'), 'leo_post_student_voice', 'sarah_post_student_voice')
    _run_branch_and_write([*pre_scenes, i3, *post_scenes], os.path.join(output_root, 'condition_teacher_reframing'), 'leo_post_teacher_reframing', 'sarah_post_teacher_reframing')

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'baseline':
        run_baseline()
    elif len(sys.argv) > 1 and sys.argv[1] == 'interventions':
        run_interventions()
    else:
        run_baseline()
        run_interventions()
