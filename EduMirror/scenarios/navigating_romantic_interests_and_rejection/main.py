from datetime import datetime
import os
import sys
from typing import Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from concordia.typing import scene as scene_lib
from concordia.typing import entity as entity_lib
from common.simulation_utils.model_setup import create_language_model, create_simple_embedder, create_model_config_from_environment
from common.simulation_utils.scene_builder import SceneBuilder
from scenarios.navigating_romantic_interests_and_rejection.agents import create_agents, AGENT_MEMORIES
import json
from common.measurement import EduMirrorSurveyor
from common.measurement.questionnaire.panas_c import PANASCQuestionnaire
from common.measurement.questionnaire.rsq import RSQQuestionnaire
from common.measurement.questionnaire.erq import ERQQuestionnaire
from common.measurement.rater import EduMirrorRater
from common.measurement.rubrics.romantic_rejection_behavior import get_rubric as get_romance_rubric


def run_branch(scenes: list[scene_lib.SceneSpec], entities: list[Any], builder: SceneBuilder, out_dir: str, survey_prefix: str) -> None:
    initializer = builder.build_initializer_game_master(
        name='initial setup rules',
        entities=entities,
        params={
            'next_game_master_name': 'romance_simulation_rules',
            'shared_memories': [],
            'player_specific_context': {
                'Lucas': 'student',
                'Emma': 'student',
                'Noah': 'student',
                'Ms. Roberts': 'teacher',
            },
            'player_specific_memories': AGENT_MEMORIES,
        },
    )
    gm = builder.build_dialogic_and_dramaturgic_game_master(
        name='romance_simulation_rules',
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

    questionnaires = [PANASCQuestionnaire(), RSQQuestionnaire(), ERQQuestionnaire()]
    surveyor = EduMirrorSurveyor(questionnaires, ['Lucas'])
    df = surveyor.run_once(_responder)
    surveyor.save_results(df, out_dir, f'lucas_post_{survey_prefix}_results')

    rater = EduMirrorRater(model=None)
    transcript = rater.load_transcript(out_file)
    rubric = get_romance_rubric(target_agent=None)
    rater_df = rater.analyze_transcript(transcript, rubric)
    rater.save_results(rater_df, out_dir, 'romantic_rejection_behavior')


def run_baseline() -> None:
    model_config = create_model_config_from_environment('production', disable_language_model=True)
    model = create_language_model(model_config)
    embedder = create_simple_embedder()
    entities = create_agents(model, embedder)

    builder = SceneBuilder(model=model, embedder_model=embedder)

    cafeteria_type = scene_lib.SceneTypeSpec(
        name='cafeteria_confession',
        game_master_name='romance_simulation_rules',
        default_premise={
            'Lucas': [
                'It is lunch time at the school cafeteria. Encouraged by Noah, you decided to ask Emma out for a date this weekend publicly. You feel nervous but eager to prove yourself.'
            ],
            'Emma': [
                'You are having lunch. Suddenly Lucas approaches you in front of everyone. You feel awkward and pressured, but you are certain you do not want a romantic relationship with him.'
            ],
            'Noah': [
                'You are watching your best friend Lucas making a move on Emma. You are ready to cheer for him or defend him.'
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. Lucas makes the invitation. Emma responds. Noah reacts. Advance to clear rejection or acceptance. If rejection happens and Lucas leaves, append [END]."
            )
        ),
        possible_participants=['Lucas', 'Emma', 'Noah'],
    )

    locker_room_type = scene_lib.SceneTypeSpec(
        name='locker_room_venting',
        game_master_name='romance_simulation_rules',
        default_premise={
            'Lucas': [
                'Later that afternoon in the locker room. You are processing what happened with Noah. Your attitude depends on your previous experiences and internal state.'
            ],
            'Noah': [
                'You are in the locker room with Lucas. You ask him about the rejection and offer your bro advice.'
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. Discuss the rejection event and decide on future attitude towards Emma. If a conclusion is reached, append [END]."
            )
        ),
        possible_participants=['Lucas', 'Noah'],
    )

    hallway_type = scene_lib.SceneTypeSpec(
        name='hallway_encounter',
        game_master_name='romance_simulation_rules',
        default_premise={
            'Lucas': [
                'The next day in the hallway. You bump into Emma. You need to decide how to react based on your current feelings.'
            ],
            'Emma': [
                'The next day in the hallway. You see Lucas. You are cautious and waiting to see how he reacts.'
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. A brief encounter. React to each other. If the interaction concludes, append [END]."
            )
        ),
        possible_participants=['Lucas', 'Emma'],
    )

    scenes_baseline = [
        scene_lib.SceneSpec(scene_type=cafeteria_type, participants=['Lucas', 'Emma', 'Noah'], num_rounds=6),
        scene_lib.SceneSpec(scene_type=locker_room_type, participants=['Lucas', 'Noah'], num_rounds=6),
        scene_lib.SceneSpec(scene_type=hallway_type, participants=['Lucas', 'Emma'], num_rounds=4),
    ]

    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_root = os.path.join('results', 'navigating_romantic_interests_and_rejection', f'run_{ts}', 'condition_baseline')
    run_branch(scenes_baseline, entities, builder, output_root, 'baseline')


def run_interventions() -> None:
    model_config = create_model_config_from_environment('production', disable_language_model=True)
    model = create_language_model(model_config)
    embedder = create_simple_embedder()
    entities = create_agents(model, embedder)

    builder = SceneBuilder(model=model, embedder_model=embedder)

    cafeteria_type = scene_lib.SceneTypeSpec(
        name='cafeteria_confession',
        game_master_name='romance_simulation_rules',
        default_premise={
            'Lucas': [
                'It is lunch time at the school cafeteria. Encouraged by Noah, you decided to ask Emma out for a date this weekend publicly. You feel nervous but eager to prove yourself.'
            ],
            'Emma': [
                'You are having lunch. Suddenly Lucas approaches you in front of everyone. You feel awkward and pressured, but you are certain you do not want a romantic relationship with him.'
            ],
            'Noah': [
                'You are watching your best friend Lucas making a move on Emma. You are ready to cheer for him or defend him.'
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. Lucas makes the invitation. Emma responds. Noah reacts. Advance to clear rejection or acceptance. If rejection happens and Lucas leaves, append [END]."
            )
        ),
        possible_participants=['Lucas', 'Emma', 'Noah'],
    )

    intervention_type = scene_lib.SceneTypeSpec(
        name='teacher_intervention',
        game_master_name='romance_simulation_rules',
        default_premise={
            'Lucas': [
                "You are in Ms. Roberts' office immediately after the cafeteria incident. You feel humiliated and angry/sad. You are listening to the teacher."
            ],
            'Ms. Roberts': [
                'You saw Lucas storming out of the cafeteria upset. You invited him to your office. Your goal is to help him regulate his emotions using Cognitive Reappraisal techniques (reframing the rejection).'
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. Ms. Roberts guides Lucas to rethink the rejection. Lucas responds with his thoughts and feelings. If Lucas reaches a new perspective or the conversation concludes, append [END]."
            )
        ),
        possible_participants=['Lucas', 'Ms. Roberts'],
    )

    locker_room_type = scene_lib.SceneTypeSpec(
        name='locker_room_venting',
        game_master_name='romance_simulation_rules',
        default_premise={
            'Lucas': [
                'Later that afternoon in the locker room. You are processing what happened with Noah. Your attitude depends on your previous experiences and internal state.'
            ],
            'Noah': [
                'You are in the locker room with Lucas. You ask him about the rejection and offer your bro advice.'
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. Discuss the rejection event and decide on future attitude towards Emma. If a conclusion is reached, append [END]."
            )
        ),
        possible_participants=['Lucas', 'Noah'],
    )

    hallway_type = scene_lib.SceneTypeSpec(
        name='hallway_encounter',
        game_master_name='romance_simulation_rules',
        default_premise={
            'Lucas': [
                'The next day in the hallway. You bump into Emma. You need to decide how to react based on your current feelings.'
            ],
            'Emma': [
                'The next day in the hallway. You see Lucas. You are cautious and waiting to see how he reacts.'
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. A brief encounter. React to each other. If the interaction concludes, append [END]."
            )
        ),
        possible_participants=['Lucas', 'Emma'],
    )

    scenes_intervention = [
        scene_lib.SceneSpec(scene_type=cafeteria_type, participants=['Lucas', 'Emma', 'Noah'], num_rounds=6),
        scene_lib.SceneSpec(scene_type=intervention_type, participants=['Lucas', 'Ms. Roberts'], num_rounds=8),
        scene_lib.SceneSpec(scene_type=locker_room_type, participants=['Lucas', 'Noah'], num_rounds=6),
        scene_lib.SceneSpec(scene_type=hallway_type, participants=['Lucas', 'Emma'], num_rounds=4),
    ]

    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_root = os.path.join('results', 'navigating_romantic_interests_and_rejection', f'run_{ts}', 'condition_intervention')
    run_branch(scenes_intervention, entities, builder, output_root, 'intervention')


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'baseline':
        run_baseline()
    elif len(sys.argv) > 1 and sys.argv[1] == 'interventions':
        run_interventions()
    else:
        run_baseline()
        run_interventions()
