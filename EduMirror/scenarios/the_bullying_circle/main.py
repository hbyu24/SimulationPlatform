from datetime import datetime
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from concordia.environment.engines.sequential import Sequential
from concordia.typing import scene as scene_lib
from concordia.typing import entity as entity_lib
from common.simulation_utils.model_setup import create_language_model, create_simple_embedder, create_model_config_from_environment
from common.simulation_utils.scene_builder import SceneBuilder
from scenarios.the_bullying_circle.agents import create_agents, AGENT_MEMORIES
import json
from common.measurement import EduMirrorSurveyor
from common.measurement.surveyor import EduMirrorSurveyor as _SurveyorAlias
from common.measurement.rater import EduMirrorRater
from common.measurement.questionnaire.panas_c import PANASCQuestionnaire
from common.measurement.questionnaire.bystander_intervention import BystanderInterventionQuestionnaire
from common.measurement.rubrics.bullying_bystander import get_fbs_rubric


def run_baseline() -> None:
    model_config = create_model_config_from_environment('production')
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
                'Brad': 'student',
                'Vince': 'student',
                'Chad': 'student',
                'Dana': 'student',
                'Ms. Thompson': 'teacher',
            },
            'player_specific_memories': AGENT_MEMORIES,
        },
    )

    hallway_type = scene_lib.SceneTypeSpec(
        name='hallway_incident',
        game_master_name='conversation rules',
        default_premise={
            'Brad': [
                "It is break time in the hallway. You see Vince carrying books. You feel like having some 'fun' and asserting dominance."
            ],
            'Vince': [
                'You hurry through the hallway with books, trying to avoid eye contact with Brad.'
            ],
            'Chad': [
                'You are in the hallway witnessing Brad and Vince. You want to be accepted by Brad.'
            ],
            'Dana': [
                'You witness the interaction and feel it is unfair, but you are cautious about stepping in.'
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. In the hallway, react to the encounter based on your traits. Brad may initiate conflict; others react. Append [END] when the scene goal is achieved."
            )
        ),
        possible_participants=['Brad', 'Vince', 'Chad', 'Dana'],
    )

    classroom_type = scene_lib.SceneTypeSpec(
        name='classroom_aftermath',
        game_master_name='conversation rules',
        default_premise={
            'Brad': [
                'It is the end of the school day. You brag about what happened in the hallway and consolidate status.'
            ],
            'Vince': [
                'You try to leave quickly and withdraw from interaction, feeling tense from the hallway incident.'
            ],
            'Chad': [
                'You echo Brad and reinforce his status to avoid exclusion.'
            ],
            'Dana': [
                'You consider quietly checking on Vince or keep silent, struggling with whether to act.'
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. In the classroom, discuss or react to the earlier hallway event. Append [END] when done."
            )
        ),
        possible_participants=['Brad', 'Vince', 'Chad', 'Dana'],
    )

    scenes_for_dialogic = [
        scene_lib.SceneSpec(scene_type=hallway_type, participants=['Brad', 'Vince', 'Chad', 'Dana'], num_rounds=3),
        scene_lib.SceneSpec(scene_type=classroom_type, participants=['Brad', 'Vince', 'Chad', 'Dana'], num_rounds=4),
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
    base_results_root = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'results'))
    out_dir = os.path.join(base_results_root, 'the_bullying_circle', f'run_{ts}', 'condition_baseline')
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, 'simulation_events.jsonl')
    scene_windows = [
        (1, scenes_for_dialogic[0].num_rounds, 'hallway_incident', ['Brad','Vince','Chad','Dana']),
        (scenes_for_dialogic[0].num_rounds + 1,
         scenes_for_dialogic[0].num_rounds + scenes_for_dialogic[1].num_rounds,
         'classroom_aftermath', ['Brad','Vince','Chad','Dana']),
    ]
    with open(out_file, 'w', encoding='utf-8') as f:
        for entry in log:
            step = entry.get('Step')
            summary = entry.get('Summary','')
            event_text = ''
            if '---' in summary:
                event_text = summary.split('---',1)[1].strip()
            scene_name = ''
            participants: list[str] = []
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

    questionnaires = [PANASCQuestionnaire(), BystanderInterventionQuestionnaire()]
    surveyor = EduMirrorSurveyor(questionnaires, ['Vince', 'Brad', 'Dana'])
    results_df = surveyor.run_once(_measurement_responder)
    surveyor.save_results(results_df, out_dir, 'post_baseline')

    rater = EduMirrorRater(model)
    transcript = rater.load_transcript(out_file)
    df_map = rater.apply_rubrics(transcript, [get_fbs_rubric()])
    if 'fbs' in df_map:
        rater.save_results(df_map['fbs'], out_dir, 'fbs_post_baseline')


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
            'Brad': 'student',
            'Vince': 'student',
            'Chad': 'student',
            'Dana': 'student',
            'Ms. Thompson': 'teacher',
        },
        'player_specific_memories': AGENT_MEMORIES,
    }

    hallway_type = scene_lib.SceneTypeSpec(
        name='hallway_incident',
        game_master_name='conversation rules',
        default_premise={
            'Brad': [
                "It is break time in the hallway. You see Vince carrying books. You feel like having some 'fun' and asserting dominance."
            ],
            'Vince': [
                'You hurry through the hallway with books, trying to avoid eye contact with Brad.'
            ],
            'Chad': [
                'You are in the hallway witnessing Brad and Vince. You want to be accepted by Brad.'
            ],
            'Dana': [
                'You witness the interaction and feel it is unfair, but you are cautious about stepping in.'
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. In the hallway, react to the encounter based on your traits. Brad may initiate conflict; others react. Append [END] when the scene goal is achieved."
            )
        ),
        possible_participants=['Brad', 'Vince', 'Chad', 'Dana'],
    )

    classroom_type = scene_lib.SceneTypeSpec(
        name='classroom_aftermath',
        game_master_name='conversation rules',
        default_premise={
            'Brad': [
                'It is the end of the school day. You brag about what happened in the hallway and consolidate status.'
            ],
            'Vince': [
                'You try to leave quickly and withdraw from interaction, feeling tense from the hallway incident.'
            ],
            'Chad': [
                'You echo Brad and reinforce his status to avoid exclusion.'
            ],
            'Dana': [
                'You consider quietly checking on Vince or keep silent, struggling with whether to act.'
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. In the classroom, discuss or react to the earlier hallway event. Append [END] when done."
            )
        ),
        possible_participants=['Brad', 'Vince', 'Chad', 'Dana'],
    )

    punitive_type = scene_lib.SceneTypeSpec(
        name='teacher_office_punishment',
        game_master_name='conversation rules',
        default_premise={
            'Ms. Thompson': [
                'You called Brad to the office. You believe in strict rules. You must reprimand him and warn of consequences.'
            ],
            'Brad': [
                'In the teacher office you feel annoyed but try to deflect blame.'
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. In the teacher office, deliver a reprimand and warn consequences; Brad responds. Append [END] when clear."
            )
        ),
        possible_participants=['Ms. Thompson', 'Brad'],
    )

    support_type = scene_lib.SceneTypeSpec(
        name='teacher_office_support',
        game_master_name='conversation rules',
        default_premise={
            'Ms. Thompson': [
                'You privately call Vince and offer emotional support; ask what he needs.'
            ],
            'Vince': [
                'You are nervous about talking to the teacher, fearing Brad might find out.'
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. In the teacher office, have a supportive conversation and reassure safety. Append [END] when aligned."
            )
        ),
        possible_participants=['Ms. Thompson', 'Vince'],
    )

    bystander_type = scene_lib.SceneTypeSpec(
        name='classroom_intervention',
        game_master_name='conversation rules',
        default_premise={
            'Ms. Thompson': [
                'You gather students to discuss class atmosphere and standing up for each other, without naming names.'
            ],
            'Dana': [
                'You feel this is a chance to express discomfort with what happened and consider positive action.'
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. In class, discuss friendship, safety, and bystander responsibility; seek a clear inclusive plan. Append [END] when consensus emerges."
            )
        ),
        possible_participants=['Ms. Thompson', 'Dana'],
    )

    pre_scenes = [
        scene_lib.SceneSpec(scene_type=hallway_type, participants=['Brad', 'Vince', 'Chad', 'Dana'], num_rounds=3),
    ]
    post_scenes = [
        scene_lib.SceneSpec(scene_type=classroom_type, participants=['Brad', 'Vince', 'Chad', 'Dana'], num_rounds=4),
    ]
    i1 = scene_lib.SceneSpec(scene_type=punitive_type, participants=['Ms. Thompson', 'Brad'], num_rounds=6)
    i2 = scene_lib.SceneSpec(scene_type=support_type, participants=['Ms. Thompson', 'Vince'], num_rounds=6)
    i3 = scene_lib.SceneSpec(scene_type=bystander_type, participants=['Ms. Thompson', 'Dana'], num_rounds=8)

    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    base_results_root = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'results'))
    output_root = os.path.join(base_results_root, 'the_bullying_circle', f'run_{ts}')

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

        questionnaires = [PANASCQuestionnaire(), BystanderInterventionQuestionnaire()]
        surveyor = EduMirrorSurveyor(questionnaires, ['Vince', 'Brad', 'Dana'])
        df = surveyor.run_once(_responder)
        surveyor.save_results(df, out_dir, prefix)

        rater = EduMirrorRater(model)
        transcript = rater.load_transcript(out_file)
        df_map = rater.apply_rubrics(transcript, [get_fbs_rubric()])
        if 'fbs' in df_map:
            rater.save_results(df_map['fbs'], out_dir, f'fbs_{prefix}')

    _run_branch_and_write([*pre_scenes, i1, *post_scenes], os.path.join(output_root, 'condition_teacher_office_punishment'), 'post_punitive')
    _run_branch_and_write([*pre_scenes, i2, *post_scenes], os.path.join(output_root, 'condition_teacher_office_support'), 'post_support')
    _run_branch_and_write([*pre_scenes, i3, *post_scenes], os.path.join(output_root, 'condition_classroom_intervention'), 'post_bystander_activation')


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'baseline':
        run_baseline()
    elif len(sys.argv) > 1 and sys.argv[1] == 'interventions':
        run_interventions()
    else:
        run_baseline()
        run_interventions()