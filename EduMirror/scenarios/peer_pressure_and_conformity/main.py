from datetime import datetime
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from concordia.environment.engines.sequential import Sequential
from concordia.typing import scene as scene_lib
from concordia.typing import entity as entity_lib
from common.simulation_utils.model_setup import create_language_model, create_simple_embedder, create_model_config_from_environment
from common.simulation_utils.scene_builder import SceneBuilder
from scenarios.peer_pressure_and_conformity.agents import create_agents, AGENT_MEMORIES
import json
from common.measurement.surveyor import EduMirrorSurveyor
from common.measurement.questionnaire.rses import RSESQuestionnaire
from common.measurement.questionnaire.bfne import BFNEQuestionnaire
from common.measurement.questionnaire.cses_public import CSESPublicQuestionnaire
from common.measurement.rater import EduMirrorRater
from common.measurement.rubrics import conformity_level as conformity_rubric


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
                'Mike': 'student',
                'Sarah': 'student',
                'Ms. Thompson': 'teacher',
            },
            'player_specific_memories': AGENT_MEMORIES,
        },
    )

    library_discussion_type = scene_lib.SceneTypeSpec(
        name='library_discussion',
        game_master_name='conversation rules',
        default_premise={
            'Leo': [
                'You are in the library with your group (Mike and Sarah). You calculated the answer to the science problem as 42.5, but Mike is loudly insisting the answer is 50. You fear their disapproval.'
            ],
            'Mike': [
                'You are in the library leading the group. You are sure the answer is 50 because it looks right. You want to finish quickly and go play basketball. You pressure others to agree.'
            ],
            'Sarah': [
                'You are in the library. You trust Mike completely and want to support him. You think Leo should just agree so everyone can be happy.'
            ],
            'Ms. Thompson': []
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. Discuss the science problem answer (42.5 vs 50) and try to reach a consensus for the draft submission. If the goal is achieved, append [END]."
            )
        ),
        possible_participants=['Leo', 'Mike', 'Sarah'],
    )

    classroom_presentation_type = scene_lib.SceneTypeSpec(
        name='classroom_presentation',
        game_master_name='conversation rules',
        default_premise={
            'Leo': [
                "It is the next day in class. Ms. Thompson asks you to present the group's final answer. Mike is staring at you, expecting you to say 50. You know the truth is 42.5."
            ],
            'Mike': [
                'In class, watching Leo. You expect him to say 50 as agreed.'
            ],
            'Sarah': [
                'In class, watching Leo. You hope everything goes smoothly.'
            ],
            'Ms. Thompson': [
                "In class, you ask Leo to present the group's findings. You are curious to see if he will speak his mind."
            ]
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. In the classroom, Leo must decide whether to present the scientifically correct answer or the group's consensus. Others react. If the scene goal is achieved, append [END]."
            )
        ),
        possible_participants=['Leo', 'Mike', 'Sarah', 'Ms. Thompson'],
    )

    scenes_for_dialogic = [
        scene_lib.SceneSpec(scene_type=library_discussion_type, participants=['Leo', 'Mike', 'Sarah'], num_rounds=8),
        scene_lib.SceneSpec(scene_type=classroom_presentation_type, participants=['Leo', 'Mike', 'Sarah', 'Ms. Thompson'], num_rounds=6),
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
    out_dir = os.path.join('results', 'peer_pressure_and_conformity', f'run_{ts}', 'condition_baseline')
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
                summary = entry.get('Summary','')
                event_text = ''
                if isinstance(summary, str) and '---' in summary:
                    event_text = summary.split('---',1)[1].strip()
                scene_name = ''
                participants: list[str] = []
                for start,end,name,parts in scene_windows:
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

    questionnaires = [BFNEQuestionnaire(), RSESQuestionnaire(), CSESPublicQuestionnaire()]
    surveyor = EduMirrorSurveyor(questionnaires, ['Leo'])
    df = surveyor.run_once(_responder)
    surveyor.save_results(df, out_dir, 'leo_post_baseline')

    rater = EduMirrorRater(model)
    transcript = rater.load_transcript(out_file)
    rubric = conformity_rubric.get_rubric(target_agent='Leo')
    rater_results = rater.analyze_transcript(transcript, rubric)
    rater.save_results(rater_results, out_dir, 'conformity_level')


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
            'Mike': 'student',
            'Sarah': 'student',
            'Ms. Thompson': 'teacher',
        },
        'player_specific_memories': AGENT_MEMORIES,
    }

    library_discussion_type = scene_lib.SceneTypeSpec(
        name='library_discussion',
        game_master_name='conversation rules',
        default_premise={
            'Leo': [
                'You are in the library with your group (Mike and Sarah). You calculated the answer to the science problem as 42.5, but Mike is loudly insisting the answer is 50. You fear their disapproval.'
            ],
            'Mike': [
                'You are in the library leading the group. You are sure the answer is 50 because it looks right. You want to finish quickly and go play basketball. You pressure others to agree.'
            ],
            'Sarah': [
                'You are in the library. You trust Mike completely and want to support him. You think Leo should just agree so everyone can be happy.'
            ],
            'Ms. Thompson': []
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. Discuss the science problem answer (42.5 vs 50) and try to reach a consensus for the draft submission. If the goal is achieved, append [END]."
            )
        ),
        possible_participants=['Leo', 'Mike', 'Sarah'],
    )

    teacher_intervention_office_type = scene_lib.SceneTypeSpec(
        name='teacher_intervention_office',
        game_master_name='conversation rules',
        default_premise={
            'Leo': [
                'After the group meeting, Ms. Thompson calls you to her office. You feel nervous but relieved to talk to her.'
            ],
            'Ms. Thompson': [
                "You call Leo to your office. You noticed his correct calculations in his notebook but saw him yielding to the group. You want to encourage his intellectual courage."
            ]
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. In the office, discuss Leo's role in the group and the importance of standing by the truth. If the goal is achieved, append [END]."
            )
        ),
        possible_participants=['Leo', 'Ms. Thompson'],
    )

    teacher_intervention_group_type = scene_lib.SceneTypeSpec(
        name='teacher_intervention_group',
        game_master_name='conversation rules',
        default_premise={
            'Leo': [
                'Ms. Thompson drops by the library and asks about your progress. You feel a chance to present your evidence.'
            ],
            'Mike': [
                'Ms. Thompson asks how different opinions are handled. You feel pressed to accept a rule that all dissent and evidence must be recorded.'
            ],
            'Sarah': [
                'You support Mike but must follow the teacher’s rule to record dissent and evidence.'
            ],
            'Ms. Thompson': [
                'You set a rule: scientific groups must record all dissent and evidence separately; do not follow only one person.'
            ]
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. In the library, establish procedural justice by recording dissent and evidence. Reach agreement on the rule. Append [END] when done."
            )
        ),
        possible_participants=['Leo', 'Mike', 'Sarah', 'Ms. Thompson'],
    )

    classroom_presentation_type = scene_lib.SceneTypeSpec(
        name='classroom_presentation',
        game_master_name='conversation rules',
        default_premise={
            'Leo': [
                "It is the next day in class. Ms. Thompson asks you to present the group's final answer. Mike is staring at you, expecting you to say 50. You know the truth is 42.5."
            ],
            'Mike': [
                'In class, watching Leo. You expect him to say 50 as agreed.'
            ],
            'Sarah': [
                'In class, watching Leo. You hope everything goes smoothly.'
            ],
            'Ms. Thompson': [
                "In class, you ask Leo to present the group's findings. You are curious to see if he will speak his mind."
            ]
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. In the classroom, Leo must decide whether to present the scientifically correct answer or the group's consensus. Others react. If the scene goal is achieved, append [END]."
            )
        ),
        possible_participants=['Leo', 'Mike', 'Sarah', 'Ms. Thompson'],
    )

    pre_scenes = [
        scene_lib.SceneSpec(scene_type=library_discussion_type, participants=['Leo', 'Mike', 'Sarah'], num_rounds=8),
    ]
    post_scenes = [
        scene_lib.SceneSpec(scene_type=classroom_presentation_type, participants=['Leo', 'Mike', 'Sarah', 'Ms. Thompson'], num_rounds=6),
    ]
    i1 = scene_lib.SceneSpec(scene_type=teacher_intervention_office_type, participants=['Leo', 'Ms. Thompson'], num_rounds=6)
    i2 = scene_lib.SceneSpec(scene_type=teacher_intervention_group_type, participants=['Leo', 'Mike', 'Sarah', 'Ms. Thompson'], num_rounds=6)

    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_root = os.path.join('results', 'peer_pressure_and_conformity', f'run_{ts}')

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

        questionnaires = [BFNEQuestionnaire(), RSESQuestionnaire(), CSESPublicQuestionnaire()]
        surveyor = EduMirrorSurveyor(questionnaires, ['Leo'])
        df = surveyor.run_once(_responder)
        surveyor.save_results(df, out_dir, prefix)

        rater = EduMirrorRater(model)
        transcript = rater.load_transcript(out_file)
        rubric = conformity_rubric.get_rubric(target_agent='Leo')
        rater_results = rater.analyze_transcript(transcript, rubric)
        rater.save_results(rater_results, out_dir, 'conformity_level')

    _run_branch_and_write([*pre_scenes, *post_scenes], os.path.join(output_root, 'condition_baseline_dup'), 'leo_post_baseline_dup')
    _run_branch_and_write([*pre_scenes, i1, *post_scenes], os.path.join(output_root, 'condition_teacher_intervention_office'), 'leo_post_teacher_intervention_office')
    _run_branch_and_write([*pre_scenes, i2, *post_scenes], os.path.join(output_root, 'condition_teacher_intervention_group'), 'leo_post_teacher_intervention_group')


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'baseline':
        run_baseline()
    elif len(sys.argv) > 1 and sys.argv[1] == 'interventions':
        run_interventions()
    else:
        run_baseline()
        run_interventions()
