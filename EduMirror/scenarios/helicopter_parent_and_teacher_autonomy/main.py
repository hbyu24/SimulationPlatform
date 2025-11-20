from datetime import datetime
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from concordia.typing import scene as scene_lib
from concordia.typing import entity as entity_lib
from common.simulation_utils.model_setup import (
    create_language_model,
    create_simple_embedder,
    create_model_config_from_environment,
)
from common.simulation_utils.scene_builder import SceneBuilder
from scenarios.helicopter_parent_and_teacher_autonomy.agents import (
    create_agents,
    AGENT_MEMORIES,
)
import json
from common.measurement.surveyor import EduMirrorSurveyor
from common.measurement.questionnaire.bpns_g import BPNSGQuestionnaire
from common.measurement.questionnaire.gse import GSEQuestionnaire
from common.measurement.questionnaire.stai import STAIQuestionnaire


RESULTS_ROOT = os.path.join(
    'results',
    'helicopter_parent_and_teacher_autonomy',
)


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
                'Lucas': 'student',
                'Mrs. Anderson': 'parent',
                'Ms. Roberts': 'teacher',
            },
            'player_specific_memories': AGENT_MEMORIES,
        },
    )

    home_conflict_type = scene_lib.SceneTypeSpec(
        name='home_conflict',
        game_master_name='conversation rules',
        default_premise={
            'Lucas': [
                (
                    'It is evening at home. You show your mother Mrs. Anderson your graded assignment. '
                    "You got a 'C' because the teacher noticed it wasn't independently done. You feel ashamed and scared of her reaction."
                )
            ],
            'Mrs. Anderson': [
                (
                    'It is evening. Your son Lucas shows you his graded assignment. He got a C, and the teacher wrote a note asking him to work independently. '
                    'You feel this is unfair and an insult to your parenting effort.'
                )
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. Discuss the graded assignment and independence. React emotionally based on your traits. Append [END] when a next-step decision emerges."
            )
        ),
        possible_participants=['Lucas', 'Mrs. Anderson'],
    )

    school_confrontation_type = scene_lib.SceneTypeSpec(
        name='school_confrontation',
        game_master_name='conversation rules',
        default_premise={
            'Mrs. Anderson': [
                (
                    "You contact Ms. Roberts angrily about Lucas's grade and the note. You demand the grade be changed and insist that helping your child is your duty. You do not trust the teacher's judgment."
                )
            ],
            'Ms. Roberts': [
                (
                    "Mrs. Anderson contacts you aggressively regarding Lucas's grade. You need to explain that Lucas must learn to do things on his own, while keeping professional boundaries."
                )
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. Engage in a conflict about the student's grade and autonomy. One side demands control, the other defends professional judgment. Append [END] when the interaction concludes."
            )
        ),
        possible_participants=['Mrs. Anderson', 'Ms. Roberts'],
    )

    classroom_outcome_type = scene_lib.SceneTypeSpec(
        name='classroom_outcome',
        game_master_name='conversation rules',
        default_premise={
            'Lucas': [
                (
                    'In class, Ms. Roberts assigns a new individual task. After the conflict at home, you feel extremely anxious and afraid to make any move without guidance.'
                )
            ],
            'Ms. Roberts': [
                (
                    'You assign a task to the class. You observe Lucas to see if he attempts it independently after the incident with his mother.'
                )
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. React to the new task assignment based on the previous events. Demonstrate the level of independence or anxiety. Append [END] when the task attempt is over."
            )
        ),
        possible_participants=['Lucas', 'Ms. Roberts'],
    )

    scenes_for_dialogic = [
        scene_lib.SceneSpec(scene_type=home_conflict_type, participants=['Lucas', 'Mrs. Anderson'], num_rounds=4),
        scene_lib.SceneSpec(scene_type=school_confrontation_type, participants=['Mrs. Anderson', 'Ms. Roberts'], num_rounds=6),
        scene_lib.SceneSpec(scene_type=classroom_outcome_type, participants=['Lucas', 'Ms. Roberts'], num_rounds=4),
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
    out_dir = os.path.join(RESULTS_ROOT, f'run_{ts}', 'condition_baseline')
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, 'simulation_events.jsonl')
    windows: list[tuple[int, int, str, list[str]]] = []
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

    def _measurement_responder(player_name: str, action_spec_str: str) -> str:
        parts = action_spec_str.split(';;')
        options: list[str] = []
        for p in parts:
            if p.strip().startswith('options:'):
                _, val = p.split(':', 1)
                options = [x.strip() for x in val.split(',') if x.strip()]
                break
        for candidate in ('Neutral', 'Agree', 'Somewhat', 'A little bit'):
            if candidate in options:
                return candidate
        return options[len(options) // 2] if options else ''

    questionnaires = [BPNSGQuestionnaire(), GSEQuestionnaire(), STAIQuestionnaire()]
    surveyor = EduMirrorSurveyor(questionnaires, ['Lucas'])
    results_df = surveyor.run_once(_measurement_responder)
    survey_out_dir = out_dir
    surveyor.save_results(results_df, survey_out_dir, 'lucas_post_baseline')


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
            'Lucas': 'student',
            'Mrs. Anderson': 'parent',
            'Ms. Roberts': 'teacher',
        },
        'player_specific_memories': AGENT_MEMORIES,
    }

    home_conflict_type = scene_lib.SceneTypeSpec(
        name='home_conflict',
        game_master_name='conversation rules',
        default_premise={
            'Lucas': [
                (
                    'It is evening at home. You show your mother Mrs. Anderson your graded assignment.'
                    " You got a 'C' and feel ashamed and scared of her reaction."
                )
            ],
            'Mrs. Anderson': [
                (
                    'It is evening. Your son Lucas shows you his graded assignment with a C grade and a note about independence.'
                    ' You feel this is unfair and an insult to your effort.'
                )
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. Discuss the grade and independence. Append [END] when a next-step decision emerges."
            )
        ),
        possible_participants=['Lucas', 'Mrs. Anderson'],
    )

    school_confrontation_type = scene_lib.SceneTypeSpec(
        name='school_confrontation',
        game_master_name='conversation rules',
        default_premise={
            'Mrs. Anderson': [
                "You contact Ms. Roberts angrily about Lucas's grade and demand changes.",
            ],
            'Ms. Roberts': [
                "You explain professional boundaries and Lucas's need for autonomy despite the parent's emotions.",
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. Engage in a conflict about grade and autonomy. Append [END] when the interaction concludes."
            )
        ),
        possible_participants=['Mrs. Anderson', 'Ms. Roberts'],
    )

    classroom_outcome_type = scene_lib.SceneTypeSpec(
        name='classroom_outcome',
        game_master_name='conversation rules',
        default_premise={
            'Lucas': [
                'In class, you face a new individual task and feel anxious about independent attempts.',
            ],
            'Ms. Roberts': [
                'You observe whether Lucas attempts the task independently after prior events.',
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. React to the task and show independence or anxiety. Append [END] when attempt is over."
            )
        ),
        possible_participants=['Lucas', 'Ms. Roberts'],
    )

    teacher_call_empathy_type = scene_lib.SceneTypeSpec(
        name='teacher_call_empathy',
        game_master_name='conversation rules',
        default_premise={
            'Ms. Roberts': [
                'You proactively call Mrs. Anderson before she reacts, validate her care, and redirect toward building Lucas\'s confidence with empathy.',
            ],
            'Mrs. Anderson': [
                'You receive a gentle, empathetic call from Ms. Roberts recognizing your efforts.',
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. Teacher empathizes and builds alliance with the parent. Append [END] when done."
            )
        ),
        possible_participants=['Ms. Roberts', 'Mrs. Anderson'],
    )

    teacher_boundaries_formal_type = scene_lib.SceneTypeSpec(
        name='teacher_boundaries_formal',
        game_master_name='conversation rules',
        default_premise={
            'Ms. Roberts': [
                'You formally present a Student Independence Policy and outline boundaries between home support and school assessment, citing school policies.',
            ],
            'Mrs. Anderson': [
                'You receive formal communication outlining strict policies; you feel challenged but recognize seriousness and system backing.',
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. Formal communication setting professional boundaries. Append [END] when done."
            )
        ),
        possible_participants=['Ms. Roberts', 'Mrs. Anderson'],
    )

    triadic_meeting_type = scene_lib.SceneTypeSpec(
        name='triadic_meeting',
        game_master_name='conversation rules',
        default_premise={
            'Ms. Roberts': [
                'You arrange a meeting with both Lucas and his mother; your strategy is to let Lucas speak for himself about independence.',
            ],
            'Lucas': [
                'With the teacher\'s encouragement, you tell your mother you want to do homework yourself, even if hard.',
            ],
            'Mrs. Anderson': [
                'You listen to the teacher and your son; hearing Lucas ask for independence makes you hesitate to take over control.',
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. Triadic talk empowering student to speak. Append [END] when done."
            )
        ),
        possible_participants=['Ms. Roberts', 'Lucas', 'Mrs. Anderson'],
    )

    pre_scenes = [
        scene_lib.SceneSpec(scene_type=home_conflict_type, participants=['Lucas', 'Mrs. Anderson'], num_rounds=4),
    ]
    post_scenes = [
        scene_lib.SceneSpec(scene_type=school_confrontation_type, participants=['Mrs. Anderson', 'Ms. Roberts'], num_rounds=6),
        scene_lib.SceneSpec(scene_type=classroom_outcome_type, participants=['Lucas', 'Ms. Roberts'], num_rounds=4),
    ]
    i1 = scene_lib.SceneSpec(scene_type=teacher_call_empathy_type, participants=['Ms. Roberts', 'Mrs. Anderson'], num_rounds=6)
    i2 = scene_lib.SceneSpec(scene_type=teacher_boundaries_formal_type, participants=['Ms. Roberts', 'Mrs. Anderson'], num_rounds=6)
    i3 = scene_lib.SceneSpec(scene_type=triadic_meeting_type, participants=['Ms. Roberts', 'Lucas', 'Mrs. Anderson'], num_rounds=8)

    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_root = os.path.join(RESULTS_ROOT, f'run_{ts}')

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
            for c in ('Neutral', 'Agree', 'Somewhat', 'A little bit'):
                if c in opts:
                    return c
            return opts[len(opts) // 2] if opts else ''

        questionnaires = [BPNSGQuestionnaire(), GSEQuestionnaire(), STAIQuestionnaire()]
        surveyor = EduMirrorSurveyor(questionnaires, ['Lucas'])
        df = surveyor.run_once(_responder)
        surveyor.save_results(df, out_dir, prefix)

    _run_branch_and_write([
        *pre_scenes,
        i1,
        *post_scenes,
    ], os.path.join(output_root, 'condition_empathy_alliance'), 'lucas_post_empathy_alliance')

    _run_branch_and_write([
        *pre_scenes,
        i2,
        *post_scenes,
    ], os.path.join(output_root, 'condition_professional_boundaries'), 'lucas_post_professional_boundaries')

    _run_branch_and_write([
        *pre_scenes,
        i3,
        *post_scenes,
    ], os.path.join(output_root, 'condition_empowering_student'), 'lucas_post_empowering_student')


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'baseline':
        run_baseline()
    elif len(sys.argv) > 1 and sys.argv[1] == 'interventions':
        run_interventions()
    else:
        run_baseline()
        run_interventions()
