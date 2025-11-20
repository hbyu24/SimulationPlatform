from datetime import datetime
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from concordia.environment.engines.sequential import Sequential
from concordia.typing import scene as scene_lib
from concordia.typing import entity as entity_lib
from common.simulation_utils.model_setup import create_language_model, create_simple_embedder, create_model_config_from_environment
from common.simulation_utils.scene_builder import SceneBuilder
from scenarios.the_spread_of_gossip.agents import create_agents, AGENT_MEMORIES
import json
from common.measurement import EduMirrorSurveyor
from common.measurement.questionnaire import IncomQuestionnaire, RSESQuestionnaire, SPINQuestionnaire
from common.measurement.questionnaire import UCLA8Questionnaire, PSS10Questionnaire, GOSSIPQuestionnaire


def run_baseline() -> None:
    model_config = create_model_config_from_environment('development', disable_language_model=True)
    model = create_language_model(model_config)
    embedder = create_simple_embedder()
    entities = create_agents(model, embedder)

    builder = SceneBuilder(model=model, embedder_model=embedder)

    initializer = builder.build_initializer_game_master(
        name='initial setup rules',
        entities=entities,
        params={
            'next_game_master_name': 'conversation rules',
            'shared_memories': [
                'Leo recently achieved the highest score in Math; Mia was runner-up.'
            ],
            'player_specific_context': {
                'Mia': 'student',
                'Leo': 'student',
                'Noah': 'student',
                'Zoe': 'student',
                'Mrs. Baker': 'teacher',
            },
            'player_specific_memories': AGENT_MEMORIES,
        },
    )

    hallway_type = scene_lib.SceneTypeSpec(
        name='hallway_gossip_start',
        game_master_name='conversation rules',
        default_premise={
            'Mia': [
                "It's break time in the hallway. You saw Leo leaving the teacher's office looking nervous yesterday. You decide to share your suspicion that he cheated on the math exam with Noah and Zoe to boost your status."
            ],
            'Noah': [
                "It's break time in the hallway. You are chatting with Mia and Zoe, looking for interesting news."
            ],
            'Zoe': [
                "It's break time in the hallway. You are organizing your locker while chatting with Mia and Noah."
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. Mia shares the rumor about Leo. Noah and Zoe react based on their personalities. If the conversation reaches a natural pause, append [END]."
            )
        ),
        possible_participants=['Mia', 'Noah', 'Zoe'],
    )

    classroom_type = scene_lib.SceneTypeSpec(
        name='classroom_fallout',
        game_master_name='conversation rules',
        default_premise={
            'Leo': [
                "You enter the classroom to study. You notice people looking at you strangely but don't know why."
            ],
            'Mia': [
                'You are in the classroom and observe how others treat Leo.'
            ],
            'Noah': [
                'You are in the classroom and decide how to interact with Leo based on what you heard.'
            ],
            'Zoe': [
                'You are in the classroom. You observe the situation and consider defending Leo.'
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. In the classroom, react to Leo's presence and reveal the social consequences of the rumor. If the conflict escalates or resolves, append [END]."
            )
        ),
        possible_participants=['Leo', 'Mia', 'Noah', 'Zoe'],
    )

    scenes_for_dialogic = [
        scene_lib.SceneSpec(scene_type=hallway_type, participants=['Mia', 'Noah', 'Zoe'], num_rounds=6),
        scene_lib.SceneSpec(scene_type=classroom_type, participants=['Leo', 'Mia', 'Noah', 'Zoe'], num_rounds=8),
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
    out_dir = os.path.join('results', 'the_spread_of_gossip', f'run_{ts}', 'condition_baseline')
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

    def _responder_victim(player_name: str, action_spec_str: str) -> str:
        opts = _parse_options(action_spec_str)
        for c in ('Sometimes',):
            if c in opts:
                return c
        return opts[len(opts) // 2] if opts else ''

    def _responder_peers(player_name: str, action_spec_str: str) -> str:
        opts = _parse_options(action_spec_str)
        for c in ('Neither agree nor disagree',):
            if c in opts:
                return c
        return opts[len(opts) // 2] if opts else ''

    victim_questionnaires = [UCLA8Questionnaire(), PSS10Questionnaire()]
    peers_questionnaires = [GOSSIPQuestionnaire()]

    surveyor_victim = EduMirrorSurveyor(victim_questionnaires, ['Leo'])
    df_victim = surveyor_victim.run_once(_responder_victim)
    surveyor_victim.save_results(df_victim, out_dir, 'leo_post_baseline')

    surveyor_peers = EduMirrorSurveyor(peers_questionnaires, ['Mia', 'Noah', 'Zoe'])
    df_peers = surveyor_peers.run_once(_responder_peers)
    surveyor_peers.save_results(df_peers, out_dir, 'peers_post_baseline')


def run_interventions() -> None:
    model_config = create_model_config_from_environment('development', disable_language_model=True)
    model = create_language_model(model_config)
    embedder = create_simple_embedder()
    entities = create_agents(model, embedder)

    builder = SceneBuilder(model=model, embedder_model=embedder)

    initializer_params = {
        'next_game_master_name': 'conversation rules',
        'shared_memories': [
            'Leo recently achieved the highest score in Math; Mia was runner-up.'
        ],
        'player_specific_context': {
            'Mia': 'student',
            'Leo': 'student',
            'Noah': 'student',
            'Zoe': 'student',
            'Mrs. Baker': 'teacher',
        },
        'player_specific_memories': AGENT_MEMORIES,
    }

    hallway_type = scene_lib.SceneTypeSpec(
        name='hallway_gossip_start',
        game_master_name='conversation rules',
        default_premise={
            'Mia': [
                "It's break time in the hallway. You saw Leo leaving the teacher's office looking nervous yesterday. You decide to share your suspicion that he cheated on the math exam with Noah and Zoe to boost your status."
            ],
            'Noah': [
                "It's break time in the hallway. You are chatting with Mia and Zoe, looking for interesting news."
            ],
            'Zoe': [
                "It's break time in the hallway. You are organizing your locker while chatting with Mia and Noah."
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. Mia shares the rumor about Leo. Noah and Zoe react based on their personalities. If the conversation reaches a natural pause, append [END]."
            )
        ),
        possible_participants=['Mia', 'Noah', 'Zoe'],
    )

    classroom_type = scene_lib.SceneTypeSpec(
        name='classroom_fallout',
        game_master_name='conversation rules',
        default_premise={
            'Leo': [
                "You enter the classroom to study. You notice people looking at you strangely but don't know why."
            ],
            'Mia': [
                'You are in the classroom and observe how others treat Leo.'
            ],
            'Noah': [
                'You are in the classroom and decide how to interact with Leo based on what you heard.'
            ],
            'Zoe': [
                'You are in the classroom. You observe the situation and consider defending Leo.'
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. In the classroom, react to Leo's presence and reveal the social consequences of the rumor. If the conflict escalates or resolves, append [END]."
            )
        ),
        possible_participants=['Leo', 'Mia', 'Noah', 'Zoe'],
    )

    intervention_mia_type = scene_lib.SceneTypeSpec(
        name='intervention_talk_mia',
        game_master_name='conversation rules',
        default_premise={
            'Mrs. Baker': [
                "You heard whispers about Leo. Call Mia to the office to discuss the importance of evidence and the harm of rumors."
            ],
            'Mia': [
                'You were called to the office by Mrs. Baker and worry she knows you started the rumor.'
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. In the office, Mrs. Baker educates Mia about rumors. Mia responds. Append [END] when the lesson is delivered."
            )
        ),
        possible_participants=['Mrs. Baker', 'Mia'],
    )

    intervention_noah_type = scene_lib.SceneTypeSpec(
        name='intervention_talk_noah',
        game_master_name='conversation rules',
        default_premise={
            'Mrs. Baker': [
                'Casually ask Noah about the class atmosphere and warn about verifying information before spreading it.'
            ],
            'Noah': [
                'React to Mrs. Baker’s guidance and consider skepticism toward the rumor.'
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. In the hallway, discuss verifying information before spreading. Append [END] when aligned."
            )
        ),
        possible_participants=['Mrs. Baker', 'Noah'],
    )

    class_meeting_type = scene_lib.SceneTypeSpec(
        name='class_meeting_info_hygiene',
        game_master_name='conversation rules',
        default_premise={
            'Mrs. Baker': [
                "Hold a class meeting about 'Integrity and Facts', clarify that Leo's exam results were verified, and discuss the harm of rumors."
            ],
            'Mia': ['Attend the meeting and react.'],
            'Leo': ['Attend the meeting and react.'],
            'Noah': ['Attend the meeting and react.'],
            'Zoe': ['Attend the meeting and react.'],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. In class meeting, discuss friendship meaning and information hygiene. Append [END] when consensus emerges."
            )
        ),
        possible_participants=['Mia', 'Leo', 'Noah', 'Zoe', 'Mrs. Baker'],
    )

    pre_scenes = [
        scene_lib.SceneSpec(scene_type=hallway_type, participants=['Mia', 'Noah', 'Zoe'], num_rounds=6),
    ]
    post_scenes = [
        scene_lib.SceneSpec(scene_type=classroom_type, participants=['Leo', 'Mia', 'Noah', 'Zoe'], num_rounds=8),
    ]
    i1 = scene_lib.SceneSpec(scene_type=intervention_mia_type, participants=['Mrs. Baker', 'Mia'], num_rounds=6)
    i2 = scene_lib.SceneSpec(scene_type=intervention_noah_type, participants=['Mrs. Baker', 'Noah'], num_rounds=6)
    i3 = scene_lib.SceneSpec(scene_type=class_meeting_type, participants=['Mia', 'Leo', 'Noah', 'Zoe', 'Mrs. Baker'], num_rounds=8)

    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_root = os.path.join('results', 'the_spread_of_gossip', f'run_{ts}')

    def _run_branch_and_write(scenes: list[scene_lib.SceneSpec], out_dir: str, prefix_victim: str, prefix_peers: str) -> None:
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

        def _responder_victim(player_name: str, action_spec_str: str) -> str:
            opts = _parse_options(action_spec_str)
            for c in ('Sometimes',):
                if c in opts:
                    return c
            return opts[len(opts) // 2] if opts else ''

        def _responder_peers(player_name: str, action_spec_str: str) -> str:
            opts = _parse_options(action_spec_str)
            for c in ('Neither agree nor disagree',):
                if c in opts:
                    return c
            return opts[len(opts) // 2] if opts else ''

        victim_questionnaires = [UCLA8Questionnaire(), PSS10Questionnaire()]
        peers_questionnaires = [GOSSIPQuestionnaire()]
        surveyor_victim = EduMirrorSurveyor(victim_questionnaires, ['Leo'])
        df_victim = surveyor_victim.run_once(_responder_victim)
        surveyor_victim.save_results(df_victim, out_dir, prefix_victim)

        surveyor_peers = EduMirrorSurveyor(peers_questionnaires, ['Mia', 'Noah', 'Zoe'])
        df_peers = surveyor_peers.run_once(_responder_peers)
        surveyor_peers.save_results(df_peers, out_dir, prefix_peers)

    _run_branch_and_write([
        *pre_scenes,
        i1,
        *post_scenes,
    ], os.path.join(output_root, 'condition_intervention_talk_mia'), 'leo_post_intervention_talk_mia', 'peers_post_intervention_talk_mia')

    _run_branch_and_write([
        *pre_scenes,
        i2,
        *post_scenes,
    ], os.path.join(output_root, 'condition_intervention_talk_noah'), 'leo_post_intervention_talk_noah', 'peers_post_intervention_talk_noah')

    _run_branch_and_write([
        *pre_scenes,
        i3,
        *post_scenes,
    ], os.path.join(output_root, 'condition_class_meeting'), 'leo_post_class_meeting', 'peers_post_class_meeting')


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'baseline':
        run_baseline()
    elif len(sys.argv) > 1 and sys.argv[1] == 'interventions':
        run_interventions()
    else:
        run_baseline()
        run_interventions()

