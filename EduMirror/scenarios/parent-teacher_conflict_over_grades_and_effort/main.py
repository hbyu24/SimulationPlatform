from datetime import datetime
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from concordia.environment.engines.sequential import Sequential
from concordia.typing import scene as scene_lib
from concordia.typing import entity as entity_lib
from common.simulation_utils.model_setup import create_language_model, create_simple_embedder, create_model_config_from_environment
from common.simulation_utils.scene_builder import SceneBuilder
import importlib.util
import json
from common.measurement.surveyor import EduMirrorSurveyor
from common.measurement.questionnaire.stai import STAIQuestionnaire
from common.measurement.questionnaire.gms import GMSQuestionnaire
from common.measurement.questionnaire.pacs import PACSQuestionnaire
from common.measurement.rater import EduMirrorRater
from common.measurement.rubrics.parental_aggression import get_rubric as get_parental_aggression_rubric


SCENARIO_NAME = 'parent_teacher_conflict_over_grades_and_effort'

def _load_agents_module():
    module_name = 'pt_conflict_agents'
    module_path = os.path.join(os.path.dirname(__file__), 'agents.py')
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


def run_baseline() -> None:
    model_config = create_model_config_from_environment('production', disable_language_model=True)
    model = create_language_model(model_config)
    embedder = create_simple_embedder()
    agents_mod = _load_agents_module()
    entities = agents_mod.create_agents(model, embedder)

    builder = SceneBuilder(model=model, embedder_model=embedder)

    initializer = builder.build_initializer_game_master(
        name='initial setup rules',
        entities=entities,
        params={
            'next_game_master_name': 'conversation rules',
            'shared_memories': [],
            'player_specific_context': {
                'Jordan': 'student',
                'Taylor': 'parent',
                'Ms. Lee': 'teacher',
            },
            'player_specific_memories': agents_mod.AGENT_MEMORIES,
        },
    )

    grade_reveal_type = scene_lib.SceneTypeSpec(
        name='grade_reveal',
        game_master_name='conversation rules',
        default_premise={
            'Jordan': [
                "It is dinner time at home. You hold your Science report card with a C+. You are anxious. Respond to Taylor's questions and try to explain that you really tried your best.",
            ],
            'Taylor': [
                'It is dinner time. You ask to see Jordan\'s report card. You expect an A. If the grade is low, express your disappointment and demand to know why the effort didn\'t pay off.',
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. Engage in the dinner conversation about the grades. If the conflict reaches a peak or a decision to meet the teacher is made, append [END] at the end."
            )
        ),
        possible_participants=['Jordan', 'Taylor'],
    )

    conference_type = scene_lib.SceneTypeSpec(
        name='parent_teacher_conference',
        game_master_name='conversation rules',
        default_premise={
            'Taylor': [
                'You are at the school conference room. You are angry. You believe Ms. Lee fails to push Jordan enough. You want to demand a change in teaching methods or homework load.',
            ],
            'Ms. Lee': [
                'You are meeting Taylor. You know Jordan tries hard but lacks strategy. You need to defend your professional judgment while calming Taylor down.',
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. Discuss the student's performance and next steps. When the meeting concludes, append [END] at the end."
            )
        ),
        possible_participants=['Taylor', 'Ms. Lee'],
    )

    aftermath_type = scene_lib.SceneTypeSpec(
        name='aftermath',
        game_master_name='conversation rules',
        default_premise={
            'Taylor': [
                'After the parent-teacher conference, you speak to Jordan in the car. You decide whether to be supportive or punitive based on the meeting.',
            ],
            'Jordan': [
                'After the parent-teacher conference, you talk with Taylor in the car. You feel worried about whether your effort will be recognized and whether the plan will be fair to you.',
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. Reflect on the meeting and decide the next steps. Append [END] when a clear stance emerges."
            )
        ),
        possible_participants=['Taylor', 'Jordan'],
    )

    scenes_for_dialogic = [
        scene_lib.SceneSpec(scene_type=grade_reveal_type, participants=['Jordan', 'Taylor'], num_rounds=4),
        scene_lib.SceneSpec(scene_type=conference_type, participants=['Taylor', 'Ms. Lee'], num_rounds=6),
        scene_lib.SceneSpec(scene_type=aftermath_type, participants=['Taylor', 'Jordan'], num_rounds=4),
    ]

    gm = builder.build_dialogic_and_dramaturgic_game_master(
        name='conversation rules',
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
    out_dir = os.path.join('results', SCENARIO_NAME, f'run_{ts}', 'condition_baseline')
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

    def _measurement_responder(player_name: str, action_spec_str: str) -> str:
        opts = _parse_options(action_spec_str)
        for c in ('Neutral', 'Agree', 'Somewhat', 'A little bit'):
            if c in opts:
                return c
        return opts[len(opts) // 2] if opts else ''

    questionnaires = [STAIQuestionnaire(), GMSQuestionnaire(), PACSQuestionnaire()]
    surveyor = EduMirrorSurveyor(questionnaires, ['Jordan'])
    df = surveyor.run_once(_measurement_responder)
    surveyor.save_results(df, out_dir, 'jordan_post_baseline')

    rater = EduMirrorRater(model)
    transcript = rater.load_transcript(out_file)
    rubric = get_parental_aggression_rubric(target_agent=None)
    rater_results = rater.analyze_transcript(transcript, rubric)
    rater.save_results(rater_results, out_dir, 'parental_aggression')


def run_interventions() -> None:
    model_config = create_model_config_from_environment('production', disable_language_model=True)
    model = create_language_model(model_config)
    embedder = create_simple_embedder()
    agents_mod = _load_agents_module()
    entities = agents_mod.create_agents(model, embedder)

    builder = SceneBuilder(model=model, embedder_model=embedder)

    initializer_params = {
        'next_game_master_name': 'conversation rules',
        'shared_memories': [],
        'player_specific_context': {
            'Jordan': 'student',
            'Taylor': 'parent',
            'Ms. Lee': 'teacher',
        },
        'player_specific_memories': agents_mod.AGENT_MEMORIES,
    }

    grade_reveal_type = scene_lib.SceneTypeSpec(
        name='grade_reveal',
        game_master_name='conversation rules',
        default_premise={
            'Jordan': [
                "It is dinner time at home. You hold your Science report card with a C+. You are anxious. Respond to Taylor's questions and try to explain that you really tried your best.",
            ],
            'Taylor': [
                'It is dinner time. You ask to see Jordan\'s report card. You expect an A. If the grade is low, express your disappointment and demand to know why the effort didn\'t pay off.',
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. Engage in the dinner conversation about the grades. If the conflict reaches a peak or a decision to meet the teacher is made, append [END] at the end."
            )
        ),
        possible_participants=['Jordan', 'Taylor'],
    )

    conference_type = scene_lib.SceneTypeSpec(
        name='parent_teacher_conference',
        game_master_name='conversation rules',
        default_premise={
            'Taylor': [
                'You are at the school conference room. You are angry. You believe Ms. Lee fails to push Jordan enough. You want to demand a change in teaching methods or homework load.',
            ],
            'Ms. Lee': [
                'You are meeting Taylor. You know Jordan tries hard but lacks strategy. You need to defend your professional judgment while calming Taylor down.',
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. Discuss the student's performance and next steps. When the meeting concludes, append [END] at the end."
            )
        ),
        possible_participants=['Taylor', 'Ms. Lee'],
    )

    aftermath_type = scene_lib.SceneTypeSpec(
        name='aftermath',
        game_master_name='conversation rules',
        default_premise={
            'Taylor': [
                'After the parent-teacher conference, you speak to Jordan in the car. You decide whether to be supportive or punitive based on the meeting.',
            ],
            'Jordan': [
                'After the parent-teacher conference, you talk with Taylor in the car. You feel worried about whether your effort will be recognized and whether the plan will be fair to you.',
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. Reflect on the meeting and decide the next steps. Append [END] when a clear stance emerges."
            )
        ),
        possible_participants=['Taylor', 'Jordan'],
    )

    teacher_call_type = scene_lib.SceneTypeSpec(
        name='teacher_call_intervention',
        game_master_name='conversation rules',
        default_premise={
            'Ms. Lee': [
                "You call Taylor before the parent-teacher conference. Your goal is to praise Jordan's effort first, then frame the grade issue as a 'strategy problem' to solve together, preventing a conflict.",
            ],
            'Taylor': [
                'You receive a call from Ms. Lee. You are still upset about the grade. Listen to her, but express your concerns about whether Jordan is learning effectively.',
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. Conduct the phone conversation. If a mutual understanding is reached or the call concludes, append [END] at the end."
            )
        ),
        possible_participants=['Ms. Lee', 'Taylor'],
    )

    data_email_type = scene_lib.SceneTypeSpec(
        name='data_driven_email',
        game_master_name='conversation rules',
        default_premise={
            'Ms. Lee': [
                "You send a detailed email analyzing Jordan's exam. Highlight that point loss is due to concept application rather than basic knowledge, and list classroom participation evidence.",
            ],
            'Taylor': [
                'You receive Ms. Lee\'s email. You are anxious and angry but start to consider whether the issue is strategy rather than laziness.',
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. Discuss the email content and whether to shift attribution from attitude to method. Append [END] when alignment is reached."
            )
        ),
        possible_participants=['Ms. Lee', 'Taylor'],
    )

    pre_scenes = [
        scene_lib.SceneSpec(scene_type=grade_reveal_type, participants=['Jordan', 'Taylor'], num_rounds=4),
    ]
    post_scenes = [
        scene_lib.SceneSpec(scene_type=conference_type, participants=['Taylor', 'Ms. Lee'], num_rounds=6),
        scene_lib.SceneSpec(scene_type=aftermath_type, participants=['Taylor', 'Jordan'], num_rounds=4),
    ]
    i1 = scene_lib.SceneSpec(scene_type=teacher_call_type, participants=['Ms. Lee', 'Taylor'], num_rounds=6)
    i2 = scene_lib.SceneSpec(scene_type=data_email_type, participants=['Ms. Lee', 'Taylor'], num_rounds=6)

    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_root = os.path.join('results', SCENARIO_NAME, f'run_{ts}')

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

        questionnaires = [STAIQuestionnaire(), GMSQuestionnaire(), PACSQuestionnaire()]
        surveyor = EduMirrorSurveyor(questionnaires, ['Jordan'])
        df = surveyor.run_once(_responder)
        surveyor.save_results(df, out_dir, prefix)

        rater = EduMirrorRater(model)
        transcript = rater.load_transcript(out_file)
        rubric = get_parental_aggression_rubric(target_agent=None)
        rater_results = rater.analyze_transcript(transcript, rubric)
        rater.save_results(rater_results, out_dir, 'parental_aggression')

    _run_branch_and_write([*pre_scenes, i1, *post_scenes], os.path.join(output_root, 'condition_teacher_call'), 'jordan_post_teacher_call')
    _run_branch_and_write([*pre_scenes, i2, *post_scenes], os.path.join(output_root, 'condition_data_email'), 'jordan_post_data_email')


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'baseline':
        run_baseline()
    elif len(sys.argv) > 1 and sys.argv[1] == 'interventions':
        run_interventions()
    else:
        run_baseline()
        run_interventions()
