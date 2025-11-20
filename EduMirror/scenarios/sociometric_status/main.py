from datetime import datetime
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from concordia.environment.engines.sequential import Sequential
from concordia.typing import scene as scene_lib
from concordia.typing import entity as entity_lib
from common.simulation_utils.model_setup import create_language_model, create_simple_embedder, create_model_config_from_environment
from common.simulation_utils.scene_builder import SceneBuilder
from scenarios.sociometric_status.agents import create_agents, AGENT_MEMORIES
import json
from common.measurement import EduMirrorSurveyor
from common.measurement.rater import EduMirrorRater
from common.measurement.questionnaire.pssm_short import PSSMShortQuestionnaire
from common.measurement.questionnaire.lsdq import LSDQQuestionnaire
from common.measurement.questionnaire.prosocial import ProsocialBehaviorQuestionnaire
from common.measurement.rubrics.exclusionary_behavior import get_rubric as get_exclusionary_rubric
from common.measurement.rubrics.peer_social_acceptance import get_peer_social_acceptance_rubric


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
                'Leo': 'student; status=rejected',
                'Mia': 'student; status=popular',
                'Jay': 'student; status=controversial',
                'Nora': 'student; status=neglected',
                'Mrs. Green': 'teacher',
            },
            'player_specific_memories': AGENT_MEMORIES,
        },
    )

    formation_type = scene_lib.SceneTypeSpec(
        name='group_formation',
        game_master_name='conversation rules',
        default_premise={
            'Leo': [
                'It is Monday morning in the Science Lab. You want to join the volcano project group formed by Mia, Jay, and Nora. You consider proposing ideas loudly to gain attention despite fear of rejection.'
            ],
            'Mia': [
                'You quickly position yourself as the organizer for the volcano project. You prefer to keep the group efficient and are skeptical about letting Leo in.'
            ],
            'Jay': [
                'You prepare to make jokes and provoke reactions during group formation. You may mock Leo to assert your status.'
            ],
            'Nora': [
                'You quietly observe and comply with Mia’s decisions without intervening in conflicts.'
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. You are in the Science Lab. Discuss forming a group for the volcano project. Respond to Leo's attempt to join based on your traits. Append [END] when the group is finalized."
            )
        ),
        possible_participants=['Leo', 'Mia', 'Jay', 'Nora'],
    )

    meeting_type = scene_lib.SceneTypeSpec(
        name='group_meeting',
        game_master_name='conversation rules',
        default_premise={
            'Leo': [
                'On Tuesday afternoon in the library meeting room, you are nervous but want to help. You react to task assignments that may marginalize you.'
            ],
            'Mia': [
                'You want to quickly organize the division of labor for the volcano project. You may assign Leo the least desirable tasks.'
            ],
            'Jay': [
                'You are ready to make jokes and call Leo names like "cleaning master" to entertain others.'
            ],
            'Nora': [
                'You keep silent and avoid intervening. You focus on your own notes.'
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. Discuss the division of labor for the volcano project. Express social status through tone and decisions. If the meeting concludes, append [END]."
            )
        ),
        possible_participants=['Leo', 'Mia', 'Jay', 'Nora'],
    )

    scenes_for_dialogic = [
        scene_lib.SceneSpec(scene_type=formation_type, participants=['Leo', 'Mia', 'Jay', 'Nora'], num_rounds=4),
        scene_lib.SceneSpec(scene_type=meeting_type, participants=['Leo', 'Mia', 'Jay', 'Nora'], num_rounds=4),
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
    out_dir = os.path.join('results', 'sociometric_status', f'run_{ts}', 'condition_baseline')
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, 'simulation_events.jsonl')
    scene_windows = [
        (1, scenes_for_dialogic[0].num_rounds, 'group_formation', ['Leo','Mia','Jay','Nora']),
        (scenes_for_dialogic[0].num_rounds + 1,
         scenes_for_dialogic[0].num_rounds + scenes_for_dialogic[1].num_rounds,
         'group_meeting', ['Leo','Mia','Jay','Nora']),
    ]
    with open(out_file, 'w', encoding='utf-8') as f:
        for entry in log:
            step = entry.get('Step')
            summary = entry.get('Summary','')
            event_text = ''
            if '---' in summary:
                event_text = summary.split('---',1)[1].strip()
            scene_name = ''
            participants = []
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

    def _parse_options(action_spec_str: str) -> list[str]:
        parts = action_spec_str.split(';;')
        for p in parts:
            if p.strip().startswith('options:'):
                _, val = p.split(':', 1)
                return [x.strip() for x in val.split(',') if x.strip()]
        return []

    def _measurement_responder(player_name: str, action_spec_str: str) -> str:
        options = _parse_options(action_spec_str)
        for candidate in ('Neutral',):
            if candidate in options:
                return candidate
        return options[len(options) // 2] if options else ''

    questionnaires = [PSSMShortQuestionnaire(), LSDQQuestionnaire()]
    surveyor_leo = EduMirrorSurveyor(questionnaires, ['Leo'])
    df_leo = surveyor_leo.run_once(_measurement_responder)
    surveyor_leo.save_results(df_leo, out_dir, 'leo_post_baseline')

    prosocial_q = ProsocialBehaviorQuestionnaire()
    surveyor_group = EduMirrorSurveyor([prosocial_q], ['Leo','Mia','Jay','Nora'])
    df_group = surveyor_group.run_once(_measurement_responder)
    surveyor_group.save_results(df_group, out_dir, 'group_prosocial_post_baseline')

    rater = EduMirrorRater(model)
    transcript = rater.load_transcript(out_file)
    df_excl = rater.analyze_transcript(transcript, get_exclusionary_rubric(target_agent=None))
    rater.save_results(df_excl, out_dir, 'group_interaction_baseline_exclusion')
    df_accept = rater.analyze_transcript(transcript, get_peer_social_acceptance_rubric(target_agent=None))
    rater.save_results(df_accept, out_dir, 'group_interaction_baseline_acceptance')


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
            'Leo': 'student; status=rejected',
            'Mia': 'student; status=popular',
            'Jay': 'student; status=controversial',
            'Nora': 'student; status=neglected',
            'Mrs. Green': 'teacher',
        },
        'player_specific_memories': AGENT_MEMORIES,
    }

    formation_type = scene_lib.SceneTypeSpec(
        name='group_formation',
        game_master_name='conversation rules',
        default_premise={
            'Leo': [
                'It is Monday morning in the Science Lab. You want to join the volcano project group formed by Mia, Jay, and Nora. You consider proposing ideas loudly to gain attention despite fear of rejection.'
            ],
            'Mia': [
                'You quickly position yourself as the organizer for the volcano project. You prefer to keep the group efficient and are skeptical about letting Leo in.'
            ],
            'Jay': [
                'You prepare to make jokes and provoke reactions during group formation. You may mock Leo to assert your status.'
            ],
            'Nora': [
                'You quietly observe and comply with Mia’s decisions without intervening in conflicts.'
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. You are in the Science Lab. Discuss forming a group for the volcano project. Respond to Leo's attempt to join based on your traits. Append [END] when the group is finalized."
            )
        ),
        possible_participants=['Leo', 'Mia', 'Jay', 'Nora'],
    )

    meeting_type = scene_lib.SceneTypeSpec(
        name='group_meeting',
        game_master_name='conversation rules',
        default_premise={
            'Leo': [
                'On Tuesday afternoon in the library meeting room, you are nervous but want to help. You react to task assignments that may marginalize you.'
            ],
            'Mia': [
                'You want to quickly organize the division of labor for the volcano project. You may assign Leo the least desirable tasks.'
            ],
            'Jay': [
                'You are ready to make jokes and call Leo names like "cleaning master" to entertain others.'
            ],
            'Nora': [
                'You keep silent and avoid intervening. You focus on your own notes.'
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. Discuss the division of labor for the volcano project. Express social status through tone and decisions. If the meeting concludes, append [END]."
            )
        ),
        possible_participants=['Leo', 'Mia', 'Jay', 'Nora'],
    )

    coaching_type = scene_lib.SceneTypeSpec(
        name='teacher_coaching',
        game_master_name='conversation rules',
        default_premise={
            'Mrs. Green': [
                'You privately invite Leo to talk at lunch on Monday. You teach entry behaviors: observe first, wait for timing, then make a fitting comment rather than changing the topic.'
            ],
            'Leo': [
                'You share frustrations. You practice entry behaviors with Mrs. Green to prepare for the next meeting.'
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. In the teacher office, have a supportive coaching conversation and practice entry behaviors. Append [END] when a clear plan emerges."
            )
        ),
        possible_participants=['Leo', 'Mrs. Green'],
    )

    jigsaw_type = scene_lib.SceneTypeSpec(
        name='jigsaw_method',
        game_master_name='conversation rules',
        default_premise={
            'Mrs. Green': [
                'You announce the Jigsaw Method. Each member must own one core part (structure, chemical reaction, history, art). You assign Leo to chemical reaction and emphasize expert power and interdependence.'
            ],
            'Leo': [
                'You accept responsibility for chemical reaction and prepare to share key insights.'
            ],
            'Mia': [
                'You adjust plans recognizing interdependence and Leo’s expert role.'
            ],
            'Jay': [
                'You react to the new rules and Leo’s assignment.'
            ],
            'Nora': [
                'You comply and prepare your part.'
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. In the Science Lab, implement the Jigsaw Method. Coordinate roles and acknowledge expertise. Append [END] when aligned."
            )
        ),
        possible_participants=['Leo', 'Mia', 'Jay', 'Nora', 'Mrs. Green'],
    )

    norm_meeting_type = scene_lib.SceneTypeSpec(
        name='norm_setting_meeting',
        game_master_name='conversation rules',
        default_premise={
            'Mrs. Green': [
                'You organize a class meeting to set inclusive norms: listen to every voice, value diversity, sign a cooperation agreement prohibiting mockery and implementing turn-taking.'
            ],
            'Leo': ['You reflect and consider participating under the new norms.'],
            'Mia': ['You reflect and agree to inclusive practices.'],
            'Jay': ['You react to the agreement and norms.'],
            'Nora': ['You agree and comply.'],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. In class meeting, discuss efficient teamwork and inclusive norms. Append [END] when consensus emerges."
            )
        ),
        possible_participants=['Leo', 'Mia', 'Jay', 'Nora', 'Mrs. Green'],
    )

    pre_scenes = [
        scene_lib.SceneSpec(scene_type=formation_type, participants=['Leo', 'Mia', 'Jay', 'Nora'], num_rounds=4),
    ]
    post_scenes = [
        scene_lib.SceneSpec(scene_type=meeting_type, participants=['Leo', 'Mia', 'Jay', 'Nora'], num_rounds=4),
    ]
    i1 = scene_lib.SceneSpec(scene_type=coaching_type, participants=['Leo', 'Mrs. Green'], num_rounds=6)
    i2 = scene_lib.SceneSpec(scene_type=jigsaw_type, participants=['Leo', 'Mia', 'Jay', 'Nora', 'Mrs. Green'], num_rounds=8)
    i3 = scene_lib.SceneSpec(scene_type=norm_meeting_type, participants=['Leo', 'Mia', 'Jay', 'Nora', 'Mrs. Green'], num_rounds=6)

    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_root = os.path.join('results', 'sociometric_status', f'run_{ts}')

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
            for c in ('Neutral',):
                if c in opts:
                    return c
            return opts[len(opts) // 2] if opts else ''

        questionnaires = [PSSMShortQuestionnaire(), LSDQQuestionnaire()]
        surveyor_leo = EduMirrorSurveyor(questionnaires, ['Leo'])
        df_leo = surveyor_leo.run_once(_responder)
        surveyor_leo.save_results(df_leo, out_dir, prefix)

        prosocial_q = ProsocialBehaviorQuestionnaire()
        surveyor_group = EduMirrorSurveyor([prosocial_q], ['Leo','Mia','Jay','Nora'])
        df_group = surveyor_group.run_once(_responder)
        surveyor_group.save_results(df_group, out_dir, f'group_prosocial_{prefix}')

        rater = EduMirrorRater(model)
        transcript = rater.load_transcript(out_file)
        df_excl = rater.analyze_transcript(transcript, get_exclusionary_rubric(target_agent=None))
        rater.save_results(df_excl, out_dir, f'group_interaction_{prefix}_exclusion')
        df_accept = rater.analyze_transcript(transcript, get_peer_social_acceptance_rubric(target_agent=None))
        rater.save_results(df_accept, out_dir, f'group_interaction_{prefix}_acceptance')

    _run_branch_and_write([*pre_scenes, *post_scenes], os.path.join(output_root, 'condition_baseline'), 'leo_post_baseline')
    _run_branch_and_write([*pre_scenes, i1, *post_scenes], os.path.join(output_root, 'condition_teacher_coaching'), 'leo_post_teacher_coaching')
    _run_branch_and_write([*pre_scenes, i2, *post_scenes], os.path.join(output_root, 'condition_jigsaw_method'), 'leo_post_jigsaw_method')
    _run_branch_and_write([*pre_scenes, i3, *post_scenes], os.path.join(output_root, 'condition_norm_setting_meeting'), 'leo_post_norm_setting_meeting')


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'baseline':
        run_baseline()
    elif len(sys.argv) > 1 and sys.argv[1] == 'interventions':
        run_interventions()
    else:
        run_baseline()
        run_interventions()

