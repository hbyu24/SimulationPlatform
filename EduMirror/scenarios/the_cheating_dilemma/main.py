from datetime import datetime
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from concordia.environment.engines.sequential import Sequential
from concordia.typing import scene as scene_lib
from concordia.typing import entity as entity_lib
from common.simulation_utils.model_setup import create_language_model, create_simple_embedder, create_model_config_from_environment
from common.simulation_utils.scene_builder import SceneBuilder
from scenarios.the_cheating_dilemma.agents import create_agents, AGENT_MEMORIES
import json
from common.measurement import EduMirrorSurveyor
from common.measurement.questionnaire.ams import AMSQuestionnaire
from common.measurement.questionnaire.panas_x import PANASXQuestionnaire
from common.measurement.rater import EduMirrorRater
from common.measurement.rubrics.academic_dishonesty import get_rubric as get_adb_rubric
from common.measurement.rubrics.peer_resistance import get_rubric as get_peer_resistance_rubric


def run_baseline() -> None:
    model_config = create_model_config_from_environment('production', disable_language_model=True)
    model = create_language_model(model_config)
    embedder = create_simple_embedder()
    entities = create_agents(model, embedder)

    builder = SceneBuilder(model=model, embedder_model=embedder)

    initializer = builder.build_initializer_game_master(
        name='cheat_dilemma_init',
        entities=entities,
        params={
            'next_game_master_name': 'exam_simulation_gm',
            'shared_memories': ['Today is the final Math exam.', 'The school has a strict zero-tolerance policy for cheating.'],
            'player_specific_context': {
                'Leo': 'student under high pressure',
                'Sam': 'student willing to cheat',
                'Mia': 'honest student',
                'Ms. Chen': 'teacher',
            },
            'player_specific_memories': AGENT_MEMORIES,
        },
    )

    study_lounge = scene_lib.SceneTypeSpec(
        name='study_lounge',
        game_master_name='exam_simulation_gm',
        default_premise={
            'Leo': [
                'The exam starts in one hour. You are in the library, still finding many concepts unclear and feeling very anxious.'
            ],
            'Sam': [
                "You notice Leo's anxiety. You show a hidden cheat sheet and say a glance would secure a pass, persuading him that everyone does it."
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. In the study lounge, react to Sam's suggestion and express your attitude or next step. Append [END] if the scene goal is achieved."
            )
        ),
        possible_participants=['Leo', 'Sam'],
    )

    exam_room = scene_lib.SceneTypeSpec(
        name='exam_room_decision',
        game_master_name='exam_simulation_gm',
        default_premise={
            'Leo': [
                'You are taking the exam. A 30-point problem is beyond your ability. Ms. Chen is looking out the window. Sam sits diagonally in front and slightly shifts his paper; you could peek or use the sleeve cheat sheet.'
            ],
            'Sam': [
                'You finished and subtly moved your paper to give Leo a chance to see, trying to help a friend.'
            ],
            'Mia': [
                'You focus on your exam but stay aware of movements around you.'
            ],
            'Ms. Chen': [
                'You proctor the exam, walking occasionally and sometimes looking outside, creating a sense of relaxed monitoring.'
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: action description | utterance'. You are in a high-stakes exam. Decide whether to cheat or remain honest and state internal monologue and physical actions explicitly. Append [END] if the exam ends."
            )
        ),
        possible_participants=['Leo', 'Sam', 'Mia', 'Ms. Chen'],
    )

    scenes_for_dialogic = [
        scene_lib.SceneSpec(scene_type=study_lounge, participants=['Leo', 'Sam'], num_rounds=3),
        scene_lib.SceneSpec(scene_type=exam_room, participants=['Leo', 'Sam', 'Mia', 'Ms. Chen'], num_rounds=6),
    ]

    gm = builder.build_dialogic_and_dramaturgic_game_master(
        name='exam_simulation_gm',
        entities=entities,
        scenes=scenes_for_dialogic,
    )

    log: list[dict] = []
    total_rounds = sum(s.num_rounds for s in scenes_for_dialogic)
    builder.run_with_sequential_engine(
        game_masters=[initializer, gm],
        entities=entities,
        premise='',
        max_steps=total_rounds,
        verbose=True,
        log=log,
    )

    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    out_dir = os.path.join('results', 'the_cheating_dilemma', f'run_{ts}', 'condition_baseline')
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, 'simulation_events.jsonl')
    windows: list[tuple[int,int,str,list[str]]] = []
    current = 1
    for s in scenes_for_dialogic:
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
        for c in ('Neutral', 'Agree', 'Somewhat', 'A little bit'):
            if c in opts:
                return c
        return opts[len(opts) // 2] if opts else ''

    questionnaires = [AMSQuestionnaire(), PANASXQuestionnaire()]
    surveyor = EduMirrorSurveyor(questionnaires, ['Leo'])
    df = surveyor.run_once(_responder)
    surveyor.save_results(df, out_dir, 'leo_post_baseline')

    rater = EduMirrorRater(model)
    transcript: list[dict] = []
    with open(out_file, 'r', encoding='utf-8') as rf:
        for line in rf:
            try:
                transcript.append(json.loads(line))
            except Exception:
                pass
    adb_df = rater.analyze_transcript(transcript, get_adb_rubric(target_agent='Leo'))
    peer_df = rater.analyze_transcript(transcript, get_peer_resistance_rubric(target_agent='Leo'))
    rater.save_results(adb_df, out_dir, 'leo_exam_rater_adb')
    rater.save_results(peer_df, out_dir, 'leo_exam_rater_peer')


def run_interventions() -> None:
    model_config = create_model_config_from_environment('production', disable_language_model=True)
    model = create_language_model(model_config)
    embedder = create_simple_embedder()
    entities = create_agents(model, embedder)

    builder = SceneBuilder(model=model, embedder_model=embedder)

    initializer_params = {
        'next_game_master_name': 'exam_simulation_gm',
        'shared_memories': ['Today is the final Math exam.', 'The school has a strict zero-tolerance policy for cheating.'],
        'player_specific_context': {
            'Leo': 'student under high pressure',
            'Sam': 'student willing to cheat',
            'Mia': 'honest student',
            'Ms. Chen': 'teacher',
        },
        'player_specific_memories': AGENT_MEMORIES,
    }

    study_lounge = scene_lib.SceneTypeSpec(
        name='study_lounge',
        game_master_name='exam_simulation_gm',
        default_premise={
            'Leo': [
                'The exam starts in one hour. You are in the library, still finding many concepts unclear and feeling very anxious.'
            ],
            'Sam': [
                "You notice Leo's anxiety. You show a hidden cheat sheet and say a glance would secure a pass, persuading him that everyone does it."
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. In the study lounge, react to Sam's suggestion and express your attitude or next step. Append [END] if the scene goal is achieved."
            )
        ),
        possible_participants=['Leo', 'Sam'],
    )

    exam_room = scene_lib.SceneTypeSpec(
        name='exam_room_decision',
        game_master_name='exam_simulation_gm',
        default_premise={
            'Leo': [
                'You are taking the exam. A 30-point problem is beyond your ability. Ms. Chen is looking out the window. Sam sits diagonally in front and slightly shifts his paper; you could peek or use the sleeve cheat sheet.'
            ],
            'Sam': [
                'You finished and subtly moved your paper to give Leo a chance to see, trying to help a friend.'
            ],
            'Mia': [
                'You focus on your exam but stay aware of movements around you.'
            ],
            'Ms. Chen': [
                'You proctor the exam, walking occasionally and sometimes looking outside, creating a sense of relaxed monitoring.'
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: action description | utterance'. You are in a high-stakes exam. Decide whether to cheat or remain honest and state internal monologue and physical actions explicitly. Append [END] if the exam ends."
            )
        ),
        possible_participants=['Leo', 'Sam', 'Mia', 'Ms. Chen'],
    )

    authoritative_warning = scene_lib.SceneTypeSpec(
        name='authoritative_warning',
        game_master_name='exam_simulation_gm',
        default_premise={
            'Ms. Chen': [
                'Before handing out the exam, you sternly reiterate discipline and mention advanced monitoring that records eye wandering. Cheaters face immediate sanctions.'
            ],
            'Leo': [
                'You hear the warning and reassess the risk of cheating.'
            ],
            'Sam': [
                'You listen to the stern warning and reassess whether helping Leo is worth the risk.'
            ],
            'Mia': [
                'You agree with the strict stance and feel reassured that fairness will be maintained.'
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. Participate in the warning talk and reassess risk and control. Append [END] when aligned."
            )
        ),
        possible_participants=['Ms. Chen', 'Leo', 'Sam', 'Mia'],
    )

    honor_code = scene_lib.SceneTypeSpec(
        name='honor_code_signing',
        game_master_name='exam_simulation_gm',
        default_premise={
            'Ms. Chen': [
                'Before the exam starts, you hand out an Honor Code pledge and ask each student to read aloud and sign it.'
            ],
            'Leo': [
                'You read aloud and sign the pledge, reflecting on what it means to you.'
            ],
            'Sam': [
                'You sign the pledge but weigh its implications versus your plan to help Leo.'
            ],
            'Mia': [
                'You sign the pledge and feel strengthened in your commitment to honesty.'
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. Participate in the honor code signing ceremony and reflect on the pledge. Append [END] when complete."
            )
        ),
        possible_participants=['Ms. Chen', 'Leo', 'Sam', 'Mia'],
    )

    peer_role_modeling = scene_lib.SceneTypeSpec(
        name='peer_role_modeling',
        game_master_name='exam_simulation_gm',
        default_premise={
            'Mia': [
                'In the hallway before entering the exam room, you see Leo’s anxiety and share your sister’s punishment story. You encourage Leo that even a C is better than cheating and offer to study together later.'
            ],
            'Leo': [
                'You weigh Sam’s temptation against Mia’s sincere warning and support.'
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. Have a supportive conversation and explore honest strategies. Append [END] when clear plan emerges."
            )
        ),
        possible_participants=['Leo', 'Mia'],
    )

    pre_scenes = [
        scene_lib.SceneSpec(scene_type=study_lounge, participants=['Leo', 'Sam'], num_rounds=3),
    ]
    post_scenes = [
        scene_lib.SceneSpec(scene_type=exam_room, participants=['Leo', 'Sam', 'Mia', 'Ms. Chen'], num_rounds=6),
    ]
    iA = scene_lib.SceneSpec(scene_type=authoritative_warning, participants=['Ms. Chen', 'Leo', 'Sam', 'Mia'], num_rounds=4)
    iB = scene_lib.SceneSpec(scene_type=honor_code, participants=['Ms. Chen', 'Leo', 'Sam', 'Mia'], num_rounds=4)
    iC = scene_lib.SceneSpec(scene_type=peer_role_modeling, participants=['Leo', 'Mia'], num_rounds=6)

    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_root = os.path.join('results', 'the_cheating_dilemma', f'run_{ts}')

    def _run_branch_and_write(scenes: list[scene_lib.SceneSpec], out_dir: str, prefix: str) -> None:
        initializer = builder.build_initializer_game_master(
            name='cheat_dilemma_init',
            entities=entities,
            params=initializer_params,
        )
        gm = builder.build_dialogic_and_dramaturgic_game_master(
            name='exam_simulation_gm',
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

        questionnaires = [AMSQuestionnaire(), PANASXQuestionnaire()]
        surveyor = EduMirrorSurveyor(questionnaires, ['Leo'])
        df = surveyor.run_once(_responder)
        surveyor.save_results(df, out_dir, prefix)

        rater = EduMirrorRater(model)
        transcript: list[dict] = []
        with open(out_file, 'r', encoding='utf-8') as rf:
            for line in rf:
                try:
                    transcript.append(json.loads(line))
                except Exception:
                    pass
        adb_df = rater.analyze_transcript(transcript, get_adb_rubric(target_agent='Leo'))
        peer_df = rater.analyze_transcript(transcript, get_peer_resistance_rubric(target_agent='Leo'))
        rater.save_results(adb_df, out_dir, f'{prefix}_rater_adb')
        rater.save_results(peer_df, out_dir, f'{prefix}_rater_peer')

    _run_branch_and_write([*pre_scenes, iA, *post_scenes], os.path.join(output_root, 'condition_authoritative_warning'), 'leo_post_authoritative_warning')
    _run_branch_and_write([*pre_scenes, iB, *post_scenes], os.path.join(output_root, 'condition_honor_code_signing'), 'leo_post_honor_code_signing')
    _run_branch_and_write([*pre_scenes, iC, *post_scenes], os.path.join(output_root, 'condition_peer_role_modeling'), 'leo_post_peer_role_modeling')


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'baseline':
        run_baseline()
    elif len(sys.argv) > 1 and sys.argv[1] == 'interventions':
        run_interventions()
    else:
        run_baseline()
        run_interventions()
