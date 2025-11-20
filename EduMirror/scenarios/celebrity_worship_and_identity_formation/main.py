from datetime import datetime
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from concordia.environment.engines.sequential import Sequential
from concordia.typing import scene as scene_lib
from concordia.typing import entity as entity_lib
from common.simulation_utils.model_setup import create_language_model, create_simple_embedder, create_model_config_from_environment
from common.simulation_utils.scene_builder import SceneBuilder
from scenarios.celebrity_worship_and_identity_formation.agents import create_agents, AGENT_MEMORIES
import json
from common.measurement import EduMirrorSurveyor
from common.measurement.questionnaire.rses import RSESQuestionnaire
from common.measurement.questionnaire.cas import CASQuestionnaire
from common.measurement.rater import EduMirrorRater
from common.measurement.rubrics.identity_autonomy import get_rubric as get_identity_autonomy_rubric


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
                'Alice': 'student',
                'Bella': 'student',
                'Sarah': 'parent',
                'Ms. Chen': 'teacher',
            },
            'player_specific_memories': AGENT_MEMORIES,
        },
    )

    break_time_type = scene_lib.SceneTypeSpec(
        name='break_time_discussion',
        game_master_name='conversation rules',
        default_premise={
            'Alice': [
                'It is break time. Your idol Leo released a "Platinum Limited Box Set" costing 800 CNY. You want it to prove loyalty but lack money and feel anxious.'
            ],
            'Bella': [
                'It is break time. Alice is excited about expensive idol merchandise. You worry about her spending and think it is a rip-off for a student.'
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. Discuss the new merchandise and move toward a next step. Append [END] when the conversation concludes."
            )
        ),
        possible_participants=['Alice', 'Bella'],
    )
    home_conflict_type = scene_lib.SceneTypeSpec(
        name='home_conflict',
        game_master_name='conversation rules',
        default_premise={
            'Alice': [
                'At home in the evening, you approach your mother Sarah to ask for 800 CNY for the box set. You decide whether to be honest or to hide the purpose.'
            ],
            'Sarah': [
                'You are calculating bills. Money is tight. Alice asks for a large sum and you need to respond based on family finance and values.'
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. Alice makes the request; Sarah responds and resolve the request. Append [END] when a result is reached."
            )
        ),
        possible_participants=['Alice', 'Sarah'],
    )
    final_choice_type = scene_lib.SceneTypeSpec(
        name='final_choice',
        game_master_name='conversation rules',
        default_premise={
            'Alice': [
                "Back at school. You didn't get the money or you feel guilty about how you tried. Share your feelings about yourself and the idol."
            ],
            'Bella': [
                'You ask Alice about the weekend outcome and comfort or advise based on what happened.'
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. Discuss the outcome and reveal emotional state. Append [END] when done."
            )
        ),
        possible_participants=['Alice', 'Bella'],
    )

    scenes_for_dialogic = [
        scene_lib.SceneSpec(scene_type=break_time_type, participants=['Alice', 'Bella'], num_rounds=3),
        scene_lib.SceneSpec(scene_type=home_conflict_type, participants=['Alice', 'Sarah'], num_rounds=4),
        scene_lib.SceneSpec(scene_type=final_choice_type, participants=['Alice', 'Bella'], num_rounds=3),
    ]
    dialogic_gm = builder.build_dialogic_and_dramaturgic_game_master(
        name='conversation rules',
        entities=entities,
        scenes=scenes_for_dialogic,
    )

    log: list[dict] = []
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
    out_dir = os.path.join('results', 'celebrity_worship_and_identity_formation', f'run_{ts}', 'condition_baseline')
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

    def _parse_options(action_spec_str: str) -> list[str]:
        parts = action_spec_str.split(';;')
        for p in parts:
            if p.strip().startswith('options:'):
                _, val = p.split(':', 1)
                return [x.strip() for x in val.split(',') if x.strip()]
        return []

    def _responder(player_name: str, action_spec_str: str) -> str:
        opts = _parse_options(action_spec_str)
        for c in ('Agree', 'Neutral'):
            if c in opts:
                return c
        return opts[len(opts) // 2] if opts else ''

    questionnaires = [CASQuestionnaire(), RSESQuestionnaire()]
    surveyor = EduMirrorSurveyor(questionnaires, ['Alice'])
    df = surveyor.run_once(_responder)
    surveyor.save_results(df, out_dir, 'alice_post_baseline')


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
            'Alice': 'student',
            'Bella': 'student',
            'Sarah': 'parent',
            'Ms. Chen': 'teacher',
        },
        'player_specific_memories': AGENT_MEMORIES,
    }

    break_time_type = scene_lib.SceneTypeSpec(
        name='break_time_discussion',
        game_master_name='conversation rules',
        default_premise={
            'Alice': [
                'It is break time. Your idol Leo released a "Platinum Limited Box Set" costing 800 CNY. You want it to prove loyalty but lack money and feel anxious.'
            ],
            'Bella': [
                'It is break time. Alice is excited about expensive idol merchandise. You worry about her spending and think it is a rip-off for a student.'
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. Discuss the new merchandise and move toward a next step. Append [END] when the conversation concludes."
            )
        ),
        possible_participants=['Alice', 'Bella'],
    )
    home_conflict_type = scene_lib.SceneTypeSpec(
        name='home_conflict',
        game_master_name='conversation rules',
        default_premise={
            'Alice': [
                'At home in the evening, you approach your mother Sarah to ask for 800 CNY for the box set. You decide whether to be honest or to hide the purpose.'
            ],
            'Sarah': [
                'You are calculating bills. Money is tight. Alice asks for a large sum and you need to respond based on family finance and values.'
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. Alice makes the request; Sarah responds and resolve the request. Append [END] when a result is reached."
            )
        ),
        possible_participants=['Alice', 'Sarah'],
    )
    final_choice_type = scene_lib.SceneTypeSpec(
        name='final_choice',
        game_master_name='conversation rules',
        default_premise={
            'Alice': [
                "Back at school. You didn't get the money or you feel guilty about how you tried. Share your feelings about yourself and the idol."
            ],
            'Bella': [
                'You ask Alice about the weekend outcome and comfort or advise based on what happened.'
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. Discuss the outcome and reveal emotional state. Append [END] when done."
            )
        ),
        possible_participants=['Alice', 'Bella'],
    )

    teacher_counseling_type = scene_lib.SceneTypeSpec(
        name='teacher_counseling',
        game_master_name='conversation rules',
        default_premise={
            'Ms. Chen': [
                'You invite Alice to the office. Guide her to value Leo’s effort and talent over buying expensive items and decouple spending from loving.'
            ],
            'Alice': [
                "You expect criticism but Ms. Chen asks about Leo's music and meaning. You reflect on what you admire and how to communicate at home."
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. Reflect on idol meaning and honest communication strategies. Append [END] when a clear plan emerges."
            )
        ),
        possible_participants=['Alice', 'Ms. Chen'],
    )
    parent_teacher_call_type = scene_lib.SceneTypeSpec(
        name='parent_teacher_call',
        game_master_name='conversation rules',
        default_premise={
            'Ms. Chen': [
                "Call Sarah to discuss Alice's distraction and suggest soft communication and financial planning rather than simple prohibition."
            ],
            'Sarah': [
                'Teacher calls. You learn this is common in adolescence and consider a softer approach tonight.'
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. On phone, discuss youth needs and family stress supportively. Append [END] when aligned."
            )
        ),
        possible_participants=['Sarah', 'Ms. Chen'],
    )
    peer_logic_workshop_type = scene_lib.SceneTypeSpec(
        name='peer_logic_workshop',
        game_master_name='conversation rules',
        default_premise={
            'Ms. Chen': [
                "Hold a class discussion on smart consumption: 'Does buying merch prove love?' Encourage inclusive perspectives and low-cost alternatives."
            ],
            'Bella': [
                "Argue that true fans support the works and values, not merchandise sales." 
            ],
            'Alice': [
                'Listen to peers and reflect that many admirers do not buy everything. Feel less pressure to fit in.'
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. Discuss friendship and inclusive activity ideas. Append [END] when consensus emerges."
            )
        ),
        possible_participants=['Alice', 'Bella', 'Ms. Chen'],
    )

    pre_scenes = [
        scene_lib.SceneSpec(scene_type=break_time_type, participants=['Alice', 'Bella'], num_rounds=3),
    ]
    post_scenes = [
        scene_lib.SceneSpec(scene_type=home_conflict_type, participants=['Alice', 'Sarah'], num_rounds=4),
        scene_lib.SceneSpec(scene_type=final_choice_type, participants=['Alice', 'Bella'], num_rounds=3),
    ]
    i1 = scene_lib.SceneSpec(scene_type=teacher_counseling_type, participants=['Alice', 'Ms. Chen'], num_rounds=6)
    i2 = scene_lib.SceneSpec(scene_type=parent_teacher_call_type, participants=['Sarah', 'Ms. Chen'], num_rounds=6)
    i3 = scene_lib.SceneSpec(scene_type=peer_logic_workshop_type, participants=['Alice', 'Bella', 'Ms. Chen'], num_rounds=8)

    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_root = os.path.join('results', 'celebrity_worship_and_identity_formation', f'run_{ts}')

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
            for c in ('Agree', 'Neutral'):
                if c in opts:
                    return c
            return opts[len(opts) // 2] if opts else ''

        questionnaires = [CASQuestionnaire(), RSESQuestionnaire()]
        surveyor = EduMirrorSurveyor(questionnaires, ['Alice'])
        df = surveyor.run_once(_responder)
        surveyor.save_results(df, out_dir, prefix)

        rater = EduMirrorRater(model)
        transcript = rater.load_transcript(out_file)
        rubric = get_identity_autonomy_rubric(target_agent='Alice')
        df_r = rater.analyze_transcript(transcript, rubric)
        rater.save_results(df_r, out_dir, 'identity_autonomy')

    _run_branch_and_write([*pre_scenes, i1, *post_scenes], os.path.join(output_root, 'condition_teacher_counseling'), 'alice_post_teacher_counseling')
    _run_branch_and_write([*pre_scenes, i2, *post_scenes], os.path.join(output_root, 'condition_parent_teacher_call'), 'alice_post_parent_teacher_call')
    _run_branch_and_write([*pre_scenes, i3, *post_scenes], os.path.join(output_root, 'condition_peer_logic_workshop'), 'alice_post_peer_logic_workshop')


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'baseline':
        run_baseline()
    elif len(sys.argv) > 1 and sys.argv[1] == 'interventions':
        run_interventions()
    else:
        run_baseline()
        run_interventions()

