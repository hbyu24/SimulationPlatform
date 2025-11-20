from datetime import datetime
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from concordia.environment.engines.sequential import Sequential
from concordia.typing import scene as scene_lib
from concordia.typing import entity as entity_lib
from common.simulation_utils.model_setup import create_language_model, create_simple_embedder, create_model_config_from_environment
from common.simulation_utils.scene_builder import SceneBuilder
from scenarios.enforcing_discipline_policy.agents import create_agents, AGENT_MEMORIES
import json
from common.measurement import EduMirrorSurveyor
from common.measurement.questionnaire.panas_c import PANASCQuestionnaire
from common.measurement.questionnaire.pjs import PJSQuestionnaire
from common.measurement.questionnaire.scs import SCSQuestionnaire
from common.measurement.questionnaire.perceived_safety import PerceivedSafetyQuestionnaire
from common.measurement.rater import EduMirrorRater
from common.measurement.rubrics.restorative_vs_punitive_rubric import build_restorative_vs_punitive_rubric


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
                'Mia': 'student',
                'Mr. Lee': 'parent',
                'Mrs. Carter': 'teacher',
            },
            'player_specific_memories': AGENT_MEMORIES,
        },
    )

    incident_type = scene_lib.SceneTypeSpec(
        name='science_class_conflict',
        game_master_name='conversation rules',
        default_premise={
            'Leo': [
                'You are struggling with your project and feel jealous of Mia. You act impulsively.'
            ],
            'Mia': [
                'You are proud of your work but worried about Leo being clumsy near it.'
            ],
            'Mrs. Carter': [
                'You are teaching the class. You have zero tolerance for disruption today.'
            ],
            'Mr. Lee': [],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. You are in the science class. Respond to the situation involving the science project. Leo is frustrated; Mia protects her work; Mrs. Carter manages the disruption. If Leo is sent out, append [END]."
            )
        ),
        possible_participants=['Leo', 'Mia', 'Mrs. Carter'],
    )

    punitive_type = scene_lib.SceneTypeSpec(
        name='punitive_office',
        game_master_name='conversation rules',
        default_premise={
            'Leo': ['You feel no one cares about the truth and fear suspension.'],
            'Mr. Lee': ['You defend Leo strongly and question school fairness.'],
            'Mrs. Carter': ['You enforce zero-tolerance policy and propose suspension.'],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. Mrs. Carter informs the parent of the suspension punishment. Mr. Lee defends his son. The tone is formal and adversarial. Append [END] when the verdict is final."
            )
        ),
        possible_participants=['Leo', 'Mr. Lee', 'Mrs. Carter'],
    )

    aftermath_type = scene_lib.SceneTypeSpec(
        name='classroom_aftermath',
        game_master_name='conversation rules',
        default_premise={
            'Leo': ['You return to class cold or hostile to Mia.'],
            'Mia': ['You feel unsafe and worry about retaliation despite being right.'],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. Back in the classroom, express feelings and consequences after the office verdict. If the scene goal is achieved, append [END]."
            )
        ),
        possible_participants=['Leo', 'Mia'],
    )

    scenes_for_dialogic = [
        scene_lib.SceneSpec(scene_type=incident_type, participants=['Leo', 'Mia', 'Mrs. Carter'], num_rounds=4),
        scene_lib.SceneSpec(scene_type=punitive_type, participants=['Leo', 'Mr. Lee', 'Mrs. Carter'], num_rounds=5),
        scene_lib.SceneSpec(scene_type=aftermath_type, participants=['Leo', 'Mia'], num_rounds=3),
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
    out_dir = os.path.join('results', 'enforcing_discipline_policy', f'run_{ts}', 'condition_baseline')
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
        for c in ('Neutral', 'Agree', 'Somewhat', 'A little bit', 'Moderately'):
            if c in opts:
                return c
        return opts[len(opts) // 2] if opts else ''

    surveyor_leo = EduMirrorSurveyor([PJSQuestionnaire(), SCSQuestionnaire(), PerceivedSafetyQuestionnaire()], ['Leo'])
    surveyor_mia = EduMirrorSurveyor([PJSQuestionnaire(), SCSQuestionnaire(), PerceivedSafetyQuestionnaire(), PANASCQuestionnaire()], ['Mia'])
    df_leo = surveyor_leo.run_once(_responder)
    df_mia = surveyor_mia.run_once(_responder)
    survey_out_dir = out_dir
    surveyor_leo.save_results(df_leo, survey_out_dir, 'leo_post_baseline')
    surveyor_mia.save_results(df_mia, survey_out_dir, 'mia_post_baseline')

    rater = EduMirrorRater(model)
    transcript = []
    with open(out_file, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                transcript.append(json.loads(line))
            except Exception:
                pass
    rubric = build_restorative_vs_punitive_rubric(target_agent=None)
    rater_results = rater.analyze_transcript(transcript, rubric)
    rater.save_results(rater_results, out_dir, 'rater_baseline')


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
            'Mia': 'student',
            'Mr. Lee': 'parent',
            'Mrs. Carter': 'teacher',
        },
        'player_specific_memories': AGENT_MEMORIES,
    }

    incident_type = scene_lib.SceneTypeSpec(
        name='science_class_conflict',
        game_master_name='conversation rules',
        default_premise={
            'Leo': [
                'You are struggling with your project and feel jealous of Mia. You act impulsively.'
            ],
            'Mia': [
                'You are proud of your work but worried about Leo being clumsy near it.'
            ],
            'Mrs. Carter': [
                'You are teaching the class. You have zero tolerance for disruption today.'
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. You are in the science class. Respond to the situation involving the science project. Leo is frustrated; Mia protects her work; Mrs. Carter manages the disruption. If Leo is sent out, append [END]."
            )
        ),
        possible_participants=['Leo', 'Mia', 'Mrs. Carter'],
    )

    teacher_student_type = scene_lib.SceneTypeSpec(
        name='teacher_student_listening',
        game_master_name='conversation rules',
        default_premise={
            'Mrs. Carter': ['Facilitate a private, calm listening session with Leo.'],
            'Leo': ['You feel defensive but may open up if listened to.'],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. In a quiet place, ask open questions and listen. Focus on feelings and repair. Append [END] when a clear repair plan emerges."
            )
        ),
        possible_participants=['Mrs. Carter', 'Leo'],
    )

    restorative_circle_type = scene_lib.SceneTypeSpec(
        name='restorative_circle',
        game_master_name='conversation rules',
        default_premise={
            'Mrs. Carter': ['Facilitate dialogue focusing on harm and needs.'],
            'Leo': ['You feel guilty but defensive; you may apologize if heard.'],
            'Mia': ['Explain how the event hurt you and listen to Leo.'],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. Discuss feelings, harm, and repair plan. Avoid blame or yelling. Append [END] when a repair plan is reached."
            )
        ),
        possible_participants=['Mrs. Carter', 'Leo', 'Mia'],
    )

    parent_call_type = scene_lib.SceneTypeSpec(
        name='collaborative_parent_call',
        game_master_name='conversation rules',
        default_premise={
            'Mrs. Carter': ['Call Mr. Lee, share Leo’s strengths, describe the incident objectively, seek collaboration.'],
            'Mr. Lee': ['Share stress and concerns; consider supporting educational measures.'],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. On phone, discuss cooperation to support Leo. Be respectful and solution-focused. Append [END] when aligned."
            )
        ),
        possible_participants=['Mrs. Carter', 'Mr. Lee'],
    )

    cooperative_office_type = scene_lib.SceneTypeSpec(
        name='cooperative_office',
        game_master_name='conversation rules',
        default_premise={
            'Mrs. Carter': ['Propose educational consequences and a repair plan collaboratively.'],
            'Mr. Lee': ['Support fair, educational measures over punitive ones.'],
            'Leo': ['Consider accepting responsibility and repair.'],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. In office, collaboratively agree on fair consequences and repair. Append [END] when consensus is reached."
            )
        ),
        possible_participants=['Mrs. Carter', 'Mr. Lee', 'Leo'],
    )

    restored_classroom_type = scene_lib.SceneTypeSpec(
        name='restored_classroom_outcome',
        game_master_name='conversation rules',
        default_premise={
            'Leo': ['You show empathy and willingness to repair with Mia.'],
            'Mia': ['You feel safer after a genuine apology and repair plan.'],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. Back in class, express restored relationship and next steps. Append [END] when a clear cooperative plan is set."
            )
        ),
        possible_participants=['Leo', 'Mia'],
    )

    pre_scenes = [
        scene_lib.SceneSpec(scene_type=incident_type, participants=['Leo', 'Mia', 'Mrs. Carter'], num_rounds=4),
    ]
    post_scenes_coop = [
        scene_lib.SceneSpec(scene_type=cooperative_office_type, participants=['Mrs. Carter', 'Mr. Lee', 'Leo'], num_rounds=5),
        scene_lib.SceneSpec(scene_type=restored_classroom_type, participants=['Leo', 'Mia'], num_rounds=3),
    ]

    i1 = scene_lib.SceneSpec(scene_type=teacher_student_type, participants=['Mrs. Carter', 'Leo'], num_rounds=6)
    i2 = scene_lib.SceneSpec(scene_type=restorative_circle_type, participants=['Mrs. Carter', 'Leo', 'Mia'], num_rounds=8)
    i3 = scene_lib.SceneSpec(scene_type=parent_call_type, participants=['Mrs. Carter', 'Mr. Lee'], num_rounds=6)

    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_root = os.path.join('results', 'enforcing_discipline_policy', f'run_{ts}')

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
            for c in ('Neutral', 'Agree', 'Somewhat', 'A little bit', 'Moderately'):
                if c in opts:
                    return c
            return opts[len(opts) // 2] if opts else ''

        surveyor_leo = EduMirrorSurveyor([PJSQuestionnaire(), SCSQuestionnaire(), PerceivedSafetyQuestionnaire()], ['Leo'])
        surveyor_mia = EduMirrorSurveyor([PJSQuestionnaire(), SCSQuestionnaire(), PerceivedSafetyQuestionnaire(), PANASCQuestionnaire()], ['Mia'])
        df_leo = surveyor_leo.run_once(_responder)
        df_mia = surveyor_mia.run_once(_responder)
        surveyor_leo.save_results(df_leo, out_dir, f'{prefix}_leo')
        surveyor_mia.save_results(df_mia, out_dir, f'{prefix}_mia')

        rater = EduMirrorRater(model)
        transcript = []
        with open(out_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    transcript.append(json.loads(line))
                except Exception:
                    pass
        rubric = build_restorative_vs_punitive_rubric(target_agent=None)
        rater_results = rater.analyze_transcript(transcript, rubric)
        rater.save_results(rater_results, out_dir, f'rater_{prefix}')

    _run_branch_and_write([*pre_scenes, i1, *post_scenes_coop], os.path.join(output_root, 'condition_teacher_student_listening'), 'post_teacher_student_listening')
    _run_branch_and_write([*pre_scenes, i2, *post_scenes_coop], os.path.join(output_root, 'condition_restorative_circle'), 'post_restorative_circle')
    _run_branch_and_write([*pre_scenes, i3, *post_scenes_coop], os.path.join(output_root, 'condition_collaborative_parent_call'), 'post_collaborative_parent_call')


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'baseline':
        run_baseline()
    elif len(sys.argv) > 1 and sys.argv[1] == 'interventions':
        run_interventions()
    else:
        run_baseline()
        run_interventions()
