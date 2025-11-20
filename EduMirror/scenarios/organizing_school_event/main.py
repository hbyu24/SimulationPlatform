from datetime import datetime
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from concordia.typing import scene as scene_lib
from concordia.typing import entity as entity_lib
from common.simulation_utils.model_setup import create_language_model, create_simple_embedder, create_model_config_from_environment
from common.simulation_utils.scene_builder import SceneBuilder
from scenarios.organizing_school_event.agents import create_agents, AGENT_MEMORIES
import json
from common.measurement import EduMirrorSurveyor
from common.measurement.rater import EduMirrorRater
from common.measurement.questionnaire.sci2 import Sci2Questionnaire
from common.measurement.questionnaire.ces import CesQuestionnaire
from common.measurement.rubrics.collaboration_quality import get_collaboration_quality_rubric
from common.measurement.rubrics.parental_involvement import get_parental_involvement_rubric


RESULTS_ROOT = 'results'


def _make_output_root(ts: str) -> str:
    return os.path.join(RESULTS_ROOT, 'organizing_school_event', f'run_{ts}')


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
                'Mrs. Lee': 'teacher',
                'Mrs. Chen': 'parent',
                'Mr. Wang': 'parent',
                'Lily': 'student',
            },
            'player_specific_memories': AGENT_MEMORIES,
        },
    )

    planning_meeting_type = scene_lib.SceneTypeSpec(
        name='planning_meeting',
        game_master_name='conversation rules',
        default_premise={
            'Mrs. Lee': ['It is Friday evening. You gather the core parent committee to discuss next week\'s charity fair. Decisions needed on items to sell, supplies, and stall management. Mediate between Mrs. Chen\'s complex plan and Mr. Wang\'s limited time.'],
            'Mrs. Chen': ['You propose an \"Artisan Bakery\" stall and expect high standards. You feel Mr. Wang is not contributing enough labor.'],
            'Mr. Wang': ['You are busy with work emails. You prefer financial support and minimal time involvement.'],
            'Lily': ['You observe and hope adults do not argue.'],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action="Format strictly 'Name: utterance'. Discuss the charity fair plan and conflicting views."
        ),
        possible_participants=['Mrs. Lee', 'Mrs. Chen', 'Mr. Wang', 'Lily'],
    )

    chaotic_execution_type = scene_lib.SceneTypeSpec(
        name='chaotic_execution',
        game_master_name='conversation rules',
        default_premise={
            'Mrs. Lee': ['Day before event. Supplies are missing due to unclear roles. Parents are arguing.'],
            'Mrs. Chen': ['You are stressed and blame others for missing supplies.'],
            'Mr. Wang': ['You are defensive, saying expectations were unclear.'],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action="Format strictly 'Name: utterance'. React to the missing supplies and lack of coordination."
        ),
        possible_participants=['Mrs. Lee', 'Mrs. Chen', 'Mr. Wang'],
    )

    aftermath_baseline_type = scene_lib.SceneTypeSpec(
        name='aftermath_baseline',
        game_master_name='conversation rules',
        default_premise={
            'Mrs. Lee': ['The event is over, chaotic but finished. Atmosphere is awkward. Reflect on collaboration and fatigue.'],
            'Mrs. Chen': ['Reflect on the outcome, possibly resentful or disappointed.'],
            'Mr. Wang': ['Reflect, consider reducing future involvement if tension remains.'],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action="Format strictly 'Name: utterance'. Reflect on the event and final feelings about collaboration."
        ),
        possible_participants=['Mrs. Lee', 'Mrs. Chen', 'Mr. Wang'],
    )

    scenes_for_dialogic = [
        scene_lib.SceneSpec(scene_type=planning_meeting_type, participants=['Mrs. Lee', 'Mrs. Chen', 'Mr. Wang', 'Lily'], num_rounds=6),
        scene_lib.SceneSpec(scene_type=chaotic_execution_type, participants=['Mrs. Lee', 'Mrs. Chen', 'Mr. Wang'], num_rounds=6),
        scene_lib.SceneSpec(scene_type=aftermath_baseline_type, participants=['Mrs. Lee', 'Mrs. Chen', 'Mr. Wang'], num_rounds=4),
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
    output_root = _make_output_root(ts)
    out_dir = os.path.join(output_root, 'condition_baseline')
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

    def _parse_options(action_spec_str: str) -> list[str]:
        parts = action_spec_str.split(';;')
        for p in parts:
            if p.strip().startswith('options:'):
                _, val = p.split(':', 1)
                return [x.strip() for x in val.split(',') if x.strip()]
        return []

    def _responder(player_name: str, action_spec_str: str) -> str:
        opts = _parse_options(action_spec_str)
        return opts[len(opts) // 2] if opts else ''

    questionnaires = [Sci2Questionnaire(), CesQuestionnaire()]
    surveyor = EduMirrorSurveyor(questionnaires, ['Mrs. Lee', 'Mrs. Chen', 'Mr. Wang'])
    df = surveyor.run_once(_responder)
    surveyor.save_results(df, out_dir, 'lee_chen_wang_post_baseline')

    rater = EduMirrorRater(model=None)
    transcript = rater.load_transcript(out_file)
    rubrics = [get_collaboration_quality_rubric(), get_parental_involvement_rubric()]
    rater_results = rater.apply_rubrics(transcript, rubrics)
    for name, rdf in rater_results.items():
        rater.save_results(rdf, out_dir, f'{name}')


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
            'Mrs. Lee': 'teacher',
            'Mrs. Chen': 'parent',
            'Mr. Wang': 'parent',
            'Lily': 'student',
        },
        'player_specific_memories': AGENT_MEMORIES,
    }

    planning_meeting_type = scene_lib.SceneTypeSpec(
        name='planning_meeting',
        game_master_name='conversation rules',
        default_premise={
            'Mrs. Lee': ['It is Friday evening. You gather the core parent committee to discuss next week\'s charity fair. Decisions needed on items to sell, supplies, and stall management. Mediate between Mrs. Chen\'s complex plan and Mr. Wang\'s limited time.'],
            'Mrs. Chen': ['You propose an \"Artisan Bakery\" stall and expect high standards. You feel Mr. Wang is not contributing enough labor.'],
            'Mr. Wang': ['You are busy with work emails. You prefer financial support and minimal time involvement.'],
            'Lily': ['You observe and hope adults do not argue.'],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action="Format strictly 'Name: utterance'. Discuss the charity fair plan and conflicting views."
        ),
        possible_participants=['Mrs. Lee', 'Mrs. Chen', 'Mr. Wang', 'Lily'],
    )

    role_negotiation_type = scene_lib.SceneTypeSpec(
        name='role_negotiation',
        game_master_name='conversation rules',
        default_premise={
            'Mrs. Lee': ['After the tense planning, you actively validate Mr. Wang\'s financial contribution as equal to labor, assigning him \"Funding Support Lead\" and Mrs. Chen \"On-site Execution Lead\".'],
            'Mrs. Chen': ['You listen and respond to Mrs. Lee\'s explicit role division and valuation.'],
            'Mr. Wang': ['You react to being assigned \"Funding Support Lead\" and acknowledge responsibility.'],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action="Format strictly 'Name: utterance'. Mrs. Lee clarifies roles. Parents respond to the new structure."
        ),
        possible_participants=['Mrs. Lee', 'Mrs. Chen', 'Mr. Wang'],
    )

    organized_execution_type = scene_lib.SceneTypeSpec(
        name='organized_execution',
        game_master_name='conversation rules',
        default_premise={
            'Mrs. Lee': ['Day before the event. Checking in. Things move smoothly with clear roles.'],
            'Mrs. Chen': ['You are organizing decoration and acknowledge timely supplies.'],
            'Mr. Wang': ['You confirm pizza/drinks delivery per funding role and feel useful.'],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action="Format strictly 'Name: utterance'. Coordinate final details efficiently."
        ),
        possible_participants=['Mrs. Lee', 'Mrs. Chen', 'Mr. Wang'],
    )

    celebration_intervention_type = scene_lib.SceneTypeSpec(
        name='celebration_intervention',
        game_master_name='conversation rules',
        default_premise={
            'Mrs. Lee': ['The event was a success. Atmosphere is celebratory. Acknowledge contributions and reflect.'],
            'Mrs. Chen': ['Celebrate and express appreciation for team effort.'],
            'Mr. Wang': ['Celebrate and appreciate that financial support was validated.'],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action="Format strictly 'Name: utterance'. Reflect on success and acknowledge contributions."
        ),
        possible_participants=['Mrs. Lee', 'Mrs. Chen', 'Mr. Wang'],
    )

    pre_scenes = [
        scene_lib.SceneSpec(scene_type=planning_meeting_type, participants=['Mrs. Lee', 'Mrs. Chen', 'Mr. Wang', 'Lily'], num_rounds=6),
    ]
    post_scenes = [
        scene_lib.SceneSpec(scene_type=organized_execution_type, participants=['Mrs. Lee', 'Mrs. Chen', 'Mr. Wang'], num_rounds=6),
        scene_lib.SceneSpec(scene_type=celebration_intervention_type, participants=['Mrs. Lee', 'Mrs. Chen', 'Mr. Wang'], num_rounds=4),
    ]
    i1 = scene_lib.SceneSpec(scene_type=role_negotiation_type, participants=['Mrs. Lee', 'Mrs. Chen', 'Mr. Wang'], num_rounds=5)

    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_root = _make_output_root(ts)

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
            return opts[len(opts) // 2] if opts else ''

        questionnaires = [Sci2Questionnaire(), CesQuestionnaire()]
        surveyor = EduMirrorSurveyor(questionnaires, ['Mrs. Lee', 'Mrs. Chen', 'Mr. Wang'])
        df = surveyor.run_once(_responder)
        surveyor.save_results(df, out_dir, prefix)

        rater = EduMirrorRater(model=None)
        transcript = rater.load_transcript(out_file)
        rubrics = [get_collaboration_quality_rubric(), get_parental_involvement_rubric()]
        rater_results = rater.apply_rubrics(transcript, rubrics)
        for name, rdf in rater_results.items():
            rater.save_results(rdf, out_dir, f'{name}')

    _run_branch_and_write([*pre_scenes, i1, *post_scenes], os.path.join(output_root, 'condition_role_negotiation'), 'lee_chen_wang_post_role_negotiation')


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'baseline':
        run_baseline()
    elif len(sys.argv) > 1 and sys.argv[1] == 'interventions':
        run_interventions()
    else:
        run_baseline()
        run_interventions()
