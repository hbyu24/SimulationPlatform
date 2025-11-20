from datetime import datetime
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from concordia.environment.engines.sequential import Sequential
from concordia.typing import scene as scene_lib
from concordia.typing import entity as entity_lib
from common.simulation_utils.model_setup import create_language_model, create_simple_embedder, create_model_config_from_environment
from common.simulation_utils.scene_builder import SceneBuilder
from scenarios.navigating_discrimination.agents import create_agents, AGENT_MEMORIES
import json
from common.measurement import EduMirrorSurveyor
from common.measurement.questionnaire.geds import GEDSQuestionnaireBrief
from common.measurement.questionnaire.sobi_ps import SOBIPsychologicalStateQuestionnaire
from common.measurement.rater import EduMirrorRater
from common.measurement.rubrics.bystander_intervention import get_rubric as get_bystander_intervention_rubric
from common.measurement.rubrics.intergroup_contact_quality import get_rubric as get_intergroup_contact_quality_rubric


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
                'Maya': 'student',
                'Liam': 'student',
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
            'Maya': [
                'You are in the school library working on the "Global Culture Fair" project.',
                'You want to propose a board about your traditional cultural festival because it is unique and meaningful to you.',
                "You feel a bit nervous about Liam's reaction but you want to try.",
            ],
            'Liam': [
                'You are in the school library leading the "Global Culture Fair" project discussion.',
                'You want to secure a high score by choosing a "safe" and impressive topic, like European Renaissance art.',
                'You think traditional folk festivals are too niche and unprofessional.',
            ],
            'Sarah': [
                'You are in the school library for the group project.',
                'You want everyone to get along and avoid conflict.',
                'You like Maya\'s idea but you are afraid of opposing Liam.',
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. You are discussing the 'Global Culture Fair' project in the library. Respond to the proposals based on your cultural views and goals. If the discussion concludes or reaches an impasse, append [END]."
            )
        ),
        possible_participants=['Maya', 'Liam', 'Sarah'],
    )

    cafeteria_lunch_type = scene_lib.SceneTypeSpec(
        name='cafeteria_lunch',
        game_master_name='conversation rules',
        default_premise={
            'Maya': [
                'It is lunch time. You are eating alone or with Sarah.',
                'Reflect on the project meeting and decide whether to continue pushing for your idea or give up.',
            ],
            'Sarah': [
                'It is lunch time. You approach Maya to check on her.',
                'You feel guilty about the tension but want to keep the peace.',
                'You try to comfort Maya, but maybe suggest compromise to avoid fighting Liam.',
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. At lunch, discuss the previous day's conflict. Express your true feelings about the group dynamics. If the conversation ends, append [END]."
            )
        ),
        possible_participants=['Maya', 'Sarah'],
    )

    classroom_presentation_type = scene_lib.SceneTypeSpec(
        name='classroom_presentation',
        game_master_name='conversation rules',
        default_premise={
            'Maya': [
                'It is presentation day. You stand with your group.',
                'Decide how much you will participate based on previous interactions.',
            ],
            'Liam': [
                'It is presentation day. You are leading the presentation.',
                'You want to show the teacher how well the group worked together.',
            ],
            'Sarah': [
                'It is presentation day. You hope everything goes smoothly.',
            ],
            'Ms. Thompson': [
                'You are watching the group presentation.',
                'Ask questions about their process to see if the inclusion issues were resolved.',
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. Present your project to the class. Respond to the teacher's questions about your collaboration. If the scene goal is achieved, append [END]."
            )
        ),
        possible_participants=['Maya', 'Liam', 'Sarah', 'Ms. Thompson'],
    )

    scenes_for_dialogic = [
        scene_lib.SceneSpec(scene_type=library_discussion_type, participants=['Maya', 'Liam', 'Sarah'], num_rounds=5),
        scene_lib.SceneSpec(scene_type=cafeteria_lunch_type, participants=['Maya', 'Sarah'], num_rounds=3),
        scene_lib.SceneSpec(scene_type=classroom_presentation_type, participants=['Maya', 'Liam', 'Sarah', 'Ms. Thompson'], num_rounds=4),
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
    out_dir = os.path.join('results', 'navigating_discrimination', f'run_{ts}', 'condition_baseline')
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

    def _responder(player_name: str, action_spec_str: str) -> str:
        opts = _parse_options(action_spec_str)
        for c in ('Agree', 'Neutral'):
            if c in opts:
                return c
        return opts[len(opts) // 2] if opts else ''

    questionnaires = [GEDSQuestionnaireBrief(), SOBIPsychologicalStateQuestionnaire()]
    surveyor = EduMirrorSurveyor(questionnaires, ['Maya'])
    df = surveyor.run_once(_responder)
    surveyor.save_results(df, out_dir, 'maya_post_baseline')

    rater = EduMirrorRater(model)
    transcript = rater.load_transcript(out_file)
    df_b = rater.analyze_transcript(transcript, get_bystander_intervention_rubric(target_agent='Sarah'))
    rater.save_results(df_b, out_dir, 'bystander_intervention')
    df_c = rater.analyze_transcript(transcript, get_intergroup_contact_quality_rubric(target_agent='Liam'))
    rater.save_results(df_c, out_dir, 'intergroup_contact_quality')


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
            'Maya': 'student',
            'Liam': 'student',
            'Sarah': 'student',
            'Ms. Thompson': 'teacher',
        },
        'player_specific_memories': AGENT_MEMORIES,
    }

    library_discussion_type = scene_lib.SceneTypeSpec(
        name='library_discussion',
        game_master_name='conversation rules',
        default_premise={
            'Maya': [
                'You are in the school library working on the "Global Culture Fair" project.',
                'You want to propose a board about your traditional cultural festival because it is unique and meaningful to you.',
                "You feel a bit nervous about Liam's reaction but you want to try.",
            ],
            'Liam': [
                'You are in the school library leading the "Global Culture Fair" project discussion.',
                'You want to secure a high score by choosing a "safe" and impressive topic, like European Renaissance art.',
                'You think traditional folk festivals are too niche and unprofessional.',
            ],
            'Sarah': [
                'You are in the school library for the group project.',
                'You want everyone to get along and avoid conflict.',
                'You like Maya\'s idea but you are afraid of opposing Liam.',
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. Discuss the project topic. Respond to proposals based on your goal. If the discussion reaches a conclusion or impasse, append [END] at the end."
            )
        ),
        possible_participants=['Maya', 'Liam', 'Sarah'],
    )

    cafeteria_lunch_type = scene_lib.SceneTypeSpec(
        name='cafeteria_lunch',
        game_master_name='conversation rules',
        default_premise={
            'Maya': [
                'It is lunch time. You are eating alone or with Sarah.',
                'Reflect on the project meeting and decide whether to continue pushing for your idea or give up.',
            ],
            'Sarah': [
                'It is lunch time. You approach Maya to check on her.',
                'You feel guilty about the tension but want to keep the peace.',
                'You try to comfort Maya, but maybe suggest compromise to avoid fighting Liam.',
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. Discuss the conflict from the library. Express true feelings or offer advice. If the conversation ends, append [END] at the end."
            )
        ),
        possible_participants=['Maya', 'Sarah'],
    )

    classroom_presentation_type = scene_lib.SceneTypeSpec(
        name='classroom_presentation',
        game_master_name='conversation rules',
        default_premise={
            'Maya': [
                'It is presentation day. You stand with your group.',
                'Decide how much you will participate based on previous interactions.',
            ],
            'Liam': [
                'It is presentation day. You are leading the presentation.',
                'You want to show the teacher how well the group worked together.',
            ],
            'Sarah': [
                'It is presentation day. You hope everything goes smoothly.',
            ],
            'Ms. Thompson': [
                'You are watching the group presentation.',
                'Ask questions about their process to see if the inclusion issues were resolved.',
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. Present the project and answer teacher's questions. If the scene goal is achieved, append [END] at the end."
            )
        ),
        possible_participants=['Maya', 'Liam', 'Sarah', 'Ms. Thompson'],
    )

    teacher_office_type = scene_lib.SceneTypeSpec(
        name='teacher_office_empowerment',
        game_master_name='conversation rules',
        default_premise={
            'Maya': [
                "You are in Ms. Thompson's office.",
                'You feel discouraged after the library meeting.',
                'You respect Ms. Thompson and trust her judgment.',
            ],
            'Ms. Thompson': [
                'You invited Maya to your office after noticing her withdrawal in the library.',
                'Your goal is to validate her feelings, explain that exclusion is not okay, and empower her to value her cultural voice.',
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. Discuss the feelings about the group work. Provide or receive support/guidance. If the conversation ends, append [END] at the end."
            )
        ),
        possible_participants=['Maya', 'Ms. Thompson'],
    )

    teacher_correction_type = scene_lib.SceneTypeSpec(
        name='teacher_perpetrator_correction',
        game_master_name='conversation rules',
        default_premise={
            'Ms. Thompson': [
                'You call Liam privately and explain the impact of microaggressions and inclusive leadership.',
            ],
            'Liam': [
                'You are initially defensive but consider whether your behavior is truly respectful.',
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. Discuss respect and inclusion in group leadership. If the conversation aligns on next steps, append [END]."
            )
        ),
        possible_participants=['Ms. Thompson', 'Liam'],
    )

    norms_setting_type = scene_lib.SceneTypeSpec(
        name='classroom_norms_setting',
        game_master_name='conversation rules',
        default_premise={
            'Ms. Thompson': [
                'Pause regular class to discuss cultural intelligence, stereotypes, and respectful listening.',
            ],
            'Maya': [
                'Share a perspective on the value of unique cultural views in innovation.',
            ],
            'Liam': [
                'Reflect on inclusive teamwork and consider the benefits of diverse ideas.',
            ],
            'Sarah': [
                'Recognize the importance of speaking up as a bystander.',
            ],
        },
        action_spec=entity_lib.free_action_spec(
            call_to_action=(
                "Format strictly 'Name: utterance'. Discuss cultural intelligence and inclusive norms. If consensus emerges, append [END]."
            )
        ),
        possible_participants=['Maya', 'Liam', 'Sarah', 'Ms. Thompson'],
    )

    pre_scenes = [
        scene_lib.SceneSpec(scene_type=library_discussion_type, participants=['Maya', 'Liam', 'Sarah'], num_rounds=5),
    ]
    post_scenes = [
        scene_lib.SceneSpec(scene_type=cafeteria_lunch_type, participants=['Maya', 'Sarah'], num_rounds=3),
        scene_lib.SceneSpec(scene_type=classroom_presentation_type, participants=['Maya', 'Liam', 'Sarah', 'Ms. Thompson'], num_rounds=4),
    ]
    i1 = scene_lib.SceneSpec(scene_type=teacher_office_type, participants=['Maya', 'Ms. Thompson'], num_rounds=6)
    i2 = scene_lib.SceneSpec(scene_type=teacher_correction_type, participants=['Ms. Thompson', 'Liam'], num_rounds=6)
    i3 = scene_lib.SceneSpec(scene_type=norms_setting_type, participants=['Maya', 'Liam', 'Sarah', 'Ms. Thompson'], num_rounds=8)

    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_root = os.path.join('results', 'navigating_discrimination', f'run_{ts}')

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
            for c in ('Agree', 'Neutral'):
                if c in opts:
                    return c
            return opts[len(opts) // 2] if opts else ''

        questionnaires = [GEDSQuestionnaireBrief(), SOBIPsychologicalStateQuestionnaire()]
        surveyor = EduMirrorSurveyor(questionnaires, ['Maya'])
        df = surveyor.run_once(_responder)
        surveyor.save_results(df, out_dir, prefix)

        rater = EduMirrorRater(model)
        transcript = rater.load_transcript(out_file)
        df_b = rater.analyze_transcript(transcript, get_bystander_intervention_rubric(target_agent='Sarah'))
        rater.save_results(df_b, out_dir, 'bystander_intervention')
        df_c = rater.analyze_transcript(transcript, get_intergroup_contact_quality_rubric(target_agent='Liam'))
        rater.save_results(df_c, out_dir, 'intergroup_contact_quality')

    _run_branch_and_write([*pre_scenes, i1, *post_scenes], os.path.join(output_root, 'condition_teacher_empowerment'), 'maya_post_teacher_empowerment')
    _run_branch_and_write([*pre_scenes, i2, *post_scenes], os.path.join(output_root, 'condition_teacher_correction'), 'maya_post_teacher_correction')
    _run_branch_and_write([*pre_scenes, i3, *post_scenes], os.path.join(output_root, 'condition_class_norms'), 'maya_post_class_norms')


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'baseline':
        run_baseline()
    elif len(sys.argv) > 1 and sys.argv[1] == 'interventions':
        run_interventions()
    else:
        run_baseline()
        run_interventions()

