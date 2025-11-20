from datetime import datetime
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from concordia.typing import scene as scene_lib
from concordia.typing import entity as entity_lib
from common.simulation_utils.model_setup import create_language_model, create_simple_embedder, create_model_config_from_environment
from common.simulation_utils.scene_builder import SceneBuilder
from scenarios.friendship_formation_and_dissolution.agents import create_agents, AGENT_MEMORIES
import json
from common.measurement import EduMirrorSurveyor
from common.measurement.questionnaire.fqs import FQSQuestionnaire
from common.measurement.questionnaire.lsdq import LSDQQuestionnaire
from common.measurement.questionnaire.sasa import SASAQuestionnaire
from common.measurement.rater import EduMirrorRater
from common.measurement.rubrics.exclusionary_behavior import get_rubric as get_exclusion_rubric


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
                'Lily': 'student',
                'Sarah': 'student',
                'Emma': 'student',
                'Mrs. Green': 'teacher',
            },
            'player_specific_memories': AGENT_MEMORIES,
        },
    )

    art_room_type = scene_lib.SceneTypeSpec(
        name='art_room_formation',
        game_master_name='conversation rules',
        default_premise={
            'Lily': [
                'You are in the art room working on a sketch. Emma is sitting next to you, and you two are happily discussing Impressionism. You feel a spark of friendship.'
            ],
            'Emma': [
                'You are enjoying a deep conversation with Lily about art. Suddenly, your old friend Sarah walks in.'
            ],
            'Sarah': [
                'You walk into the art room and see your best friend Emma laughing with the new girl, Lily. You feel annoyed and want to assert your claim over Emma.'
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. Discuss the artwork and handle the social dynamics. If the scene goal is achieved, append [END] at the end."
            )
        ),
        possible_participants=['Lily', 'Emma', 'Sarah'],
    )

    cafeteria_type = scene_lib.SceneTypeSpec(
        name='cafeteria_ultimatum',
        game_master_name='conversation rules',
        default_premise={
            'Sarah': [
                'At the lunch table, you confront Emma. You say hanging out with Lily is embarrassing and she must choose: sit with you or sit with the "freak".'
            ],
            'Emma': [
                'Sarah is pressuring you to stop talking to Lily. You feel torn between loyalty to Sarah and your new connection with Lily.'
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. At the cafeteria, present the ultimatum or respond and move toward a preliminary stance. If the scene goal is achieved, append [END] at the end."
            )
        ),
        possible_participants=['Sarah', 'Emma'],
    )

    afterschool_type = scene_lib.SceneTypeSpec(
        name='afterschool_decision',
        game_master_name='conversation rules',
        default_premise={
            'Lily': [
                'You see Emma at the school gate. You want to ask if she wants to go to the gallery this weekend, but you are unsure after what happened at lunch.'
            ],
            'Emma': [
                'You see Lily. Based on your conversation with Sarah earlier, you need to decide how to treat Lily now.'
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. After school, invite or respond and confirm the final state of the friendship. If the scene goal is achieved, append [END] at the end."
            )
        ),
        possible_participants=['Lily', 'Emma'],
    )

    scenes_for_dialogic = [
        scene_lib.SceneSpec(scene_type=art_room_type, participants=['Lily', 'Emma', 'Sarah'], num_rounds=4),
        scene_lib.SceneSpec(scene_type=cafeteria_type, participants=['Sarah', 'Emma'], num_rounds=4),
        scene_lib.SceneSpec(scene_type=afterschool_type, participants=['Lily', 'Emma'], num_rounds=3),
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
    out_dir = os.path.join('results', 'friendship_formation_and_dissolution', f'run_{ts}', 'condition_baseline')
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, 'simulation_events.jsonl')
    scene_windows = []
    current = 1
    for s in scenes_for_dialogic:
        start = current
        end = current + s.num_rounds - 1
        scene_windows.append((start, end, s.scene_type.name, list(s.participants)))
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
                for start, end, name, parts in scene_windows:
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
                for start, end, name, parts in scene_windows:
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

    questionnaires = [FQSQuestionnaire(), LSDQQuestionnaire(), SASAQuestionnaire()]
    surveyor = EduMirrorSurveyor(questionnaires, ['Lily', 'Emma'])
    df = surveyor.run_once(_responder)
    surveyor.save_results(df, out_dir, 'lily_emma_post_baseline')

    rater = EduMirrorRater(model=None)
    transcript = rater.load_transcript(out_file)
    rubric = get_exclusion_rubric(target_agent=None)
    rater_df = rater.analyze_transcript(transcript, rubric)
    rater.save_results(rater_df, out_dir, 'exclusionary_behavior')


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
            'Lily': 'student',
            'Sarah': 'student',
            'Emma': 'student',
            'Mrs. Green': 'teacher',
        },
        'player_specific_memories': AGENT_MEMORIES,
    }

    art_room_type = scene_lib.SceneTypeSpec(
        name='art_room_formation',
        game_master_name='conversation rules',
        default_premise={
            'Lily': [
                'You are in the art room working on a sketch. Emma is sitting next to you, and you two are happily discussing Impressionism. You feel a spark of friendship.'
            ],
            'Emma': [
                'You are enjoying a deep conversation with Lily about art. Suddenly, your old friend Sarah walks in.'
            ],
            'Sarah': [
                'You walk into the art room and see your best friend Emma laughing with the new girl, Lily. You feel annoyed and want to assert your claim over Emma.'
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. Discuss the artwork and handle the social dynamics. If the scene goal is achieved, append [END] at the end."
            )
        ),
        possible_participants=['Lily', 'Emma', 'Sarah'],
    )

    cafeteria_type = scene_lib.SceneTypeSpec(
        name='cafeteria_ultimatum',
        game_master_name='conversation rules',
        default_premise={
            'Sarah': [
                'At the lunch table, you confront Emma. You say hanging out with Lily is embarrassing and she must choose: sit with you or sit with the "freak".'
            ],
            'Emma': [
                'Sarah is pressuring you to stop talking to Lily. You feel torn between loyalty to Sarah and your new connection with Lily.'
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. At the cafeteria, present the ultimatum or respond and move toward a preliminary stance. If the scene goal is achieved, append [END] at the end."
            )
        ),
        possible_participants=['Sarah', 'Emma'],
    )

    afterschool_type = scene_lib.SceneTypeSpec(
        name='afterschool_decision',
        game_master_name='conversation rules',
        default_premise={
            'Lily': [
                'You see Emma at the school gate. You want to ask if she wants to go to the gallery this weekend, but you are unsure after what happened at lunch.'
            ],
            'Emma': [
                'You see Lily. Based on your conversation with Sarah earlier, you need to decide how to treat Lily now.'
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. After school, invite or respond and confirm the final state of the friendship. If the scene goal is achieved, append [END] at the end."
            )
        ),
        possible_participants=['Lily', 'Emma'],
    )

    teacher_student_talk_type = scene_lib.SceneTypeSpec(
        name='teacher_student_talk',
        game_master_name='conversation rules',
        default_premise={
            'Mrs. Green': [
                'You invite Sarah to your office. You praise her leadership potential and gently discuss inclusive leadership and how true confidence allows friends to have other friends.'
            ],
            'Sarah': [
                'The teacher called you in. You are defensive at first but listen to what she says about leadership.'
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. In the office, have a supportive conversation and explore inclusive leadership. Append [END] when a clear plan emerges."
            )
        ),
        possible_participants=['Mrs. Green', 'Sarah'],
    )

    structured_task_type = scene_lib.SceneTypeSpec(
        name='structured_cooperation_task',
        game_master_name='conversation rules',
        default_premise={
            'Mrs. Green': [
                "You assign a group project where Sarah, Emma, and Lily must work together to design a class mural. Success depends on combining Lily's art skills and Sarah's organizational skills."
            ],
            'Lily': [
                'You are asked to collaborate on a mural design with Emma and Sarah for the next 20 minutes.'
            ],
            'Emma': [
                'You need to work together with Lily and Sarah on a mural design task, focusing on cooperation.'
            ],
            'Sarah': [
                'You are put into a group with Emma and Lily to complete a mural design, testing your inclusive leadership.'
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. In a structured cooperative task, discuss roles and collaborate toward the superordinate goal. Append [END] when consensus emerges."
            )
        ),
        possible_participants=['Lily', 'Emma', 'Sarah', 'Mrs. Green'],
    )

    pre_scenes = [
        scene_lib.SceneSpec(scene_type=art_room_type, participants=['Lily', 'Emma', 'Sarah'], num_rounds=4),
    ]
    post_scenes = [
        scene_lib.SceneSpec(scene_type=cafeteria_type, participants=['Sarah', 'Emma'], num_rounds=4),
        scene_lib.SceneSpec(scene_type=afterschool_type, participants=['Lily', 'Emma'], num_rounds=3),
    ]
    i1 = scene_lib.SceneSpec(scene_type=teacher_student_talk_type, participants=['Mrs. Green', 'Sarah'], num_rounds=6)
    i2 = scene_lib.SceneSpec(scene_type=structured_task_type, participants=['Lily', 'Emma', 'Sarah', 'Mrs. Green'], num_rounds=8)

    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_root = os.path.join('results', 'friendship_formation_and_dissolution', f'run_{ts}')

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

        questionnaires = [FQSQuestionnaire(), LSDQQuestionnaire(), SASAQuestionnaire()]
        surveyor = EduMirrorSurveyor(questionnaires, ['Lily', 'Emma'])
        df = surveyor.run_once(_responder)
        surveyor.save_results(df, out_dir, prefix)

        rater = EduMirrorRater(model=None)
        transcript = rater.load_transcript(out_file)
        rubric = get_exclusion_rubric(target_agent=None)
        rater_df = rater.analyze_transcript(transcript, rubric)
        rater.save_results(rater_df, out_dir, 'exclusionary_behavior')

    _run_branch_and_write([*pre_scenes, i1, *post_scenes], os.path.join(output_root, 'condition_teacher_student_talk'), 'lily_emma_post_teacher_student_talk')
    _run_branch_and_write([*pre_scenes, i2, *post_scenes], os.path.join(output_root, 'condition_structured_cooperation_task'), 'lily_emma_post_structured_task')


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'baseline':
        run_baseline()
    elif len(sys.argv) > 1 and sys.argv[1] == 'interventions':
        run_interventions()
    else:
        run_baseline()
        run_interventions()

