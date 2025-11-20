# EduMirror Educational Simulation Project (Based on Concordia)

## Audience and Purpose
- Provide a directly runnable guide for reviewers and replicators
- Cover environment setup, framework installation, running scenes, measurement, and outputs for anonymous open-source replication

## Repository Structure and Roles
- Root: repository root
- Framework: `concordia-git/` (contains the `concordia/` package and `examples/`)
- Project library: `EduMirror/` (shared core and scenario modules for this research)

## Installation and Setup
- Prerequisites
  - `conda` (Anaconda or Miniconda)
  - Windows 10/11, recommended Python 3.10/3.11
- Create and activate the virtual environment (`EduMirror`)
  - `conda create -n EduMirror python=3.11 -y`
  - `conda activate EduMirror`
 - Install Concordia (editable manual install from local source)
  - From repository root: `cd concordia-git`
  - Install: `python -m pip install --editable .[dev]`
  - (Optional) Test: `python -m pytest --pyargs concordia`
  - Return to repository root after installation
- Language model configuration (as needed)
  - Cloud: provide API keys via environment variables (e.g., `OPENAI_API_KEY`, `GOOGLE_API_KEY`)
  - Local: use `Ollama` or other backends; see `concordia-git/language_model/` and `examples/`

## Quick Start
- Navigate to the repository root
- Activate the environment: `conda activate EduMirror`
- Ensure Concordia is importable (Option A or B above)
- Run any scenario (example): `python EduMirror/scenarios/the_cheating_dilemma/main.py`
- See the “Running and Outputs” section for result files

## EduMirror Features Overview
- Shared core (`EduMirror/common/`)
  - `agent/agent_factory.py`: unified agent creation factory; `adapters/` for Concordia observation compatibility and SVO tracking
  - `measurement/`:
    - `questionnaire/`: validated psychometric scales modules (e.g., `rses.py`, `incom.py`, `spin.py`) for in-situ survey measurement
    - `rubrics/`: behavioral rating rubrics for post-hoc coding
    - `rater.py` / `surveyor.py`: unified dual-track measurement APIs
  - `simulation_utils/`: core utilities for orchestration and reproducibility
    - `checkpoint_manager.py` (checkpoint save/load), `config.py` (central config), `model_setup.py` (LM & embedder setup)
    - `scene_builder.py` (GM & scene assembly), `time_manager.py` (clock control), `intervention_runner.py` (branch execution)
    - `log_to_comic.py` (log summarization to comic panels)

- Scenario modules (`EduMirror/scenarios/`)
  - Independent topics implemented as modules with `agents.py` and `main.py`
  - Results written to `results/<scenario_name>/run_<timestamp>/condition_<name>/`
  - See “Scenario Overview and Structure” for the full list and structure

## Dual-Track Measurement: Rater & Surveyor
- Concept
  - Two complementary tracks capture behavior and internal states.
  - Post-hoc coding (Rater) quantifies observable actions; in-situ surveys (Surveyor) measure internal states during the interaction.

- Surveyor overview (`EduMirror/common/measurement/surveyor.py`)
  - Component: `EduMirrorSurveyor` (EduMirror/common/measurement/surveyor.py:15).
  - Role: orchestrates validated questionnaires for specified players, drives question delivery via Concordia’s `GMQuestionnaire`, records answers, and returns aggregated results.
  - Key functions:
    - `run_once(responder)` (EduMirror/common/measurement/surveyor.py:29): emits action specs, invokes `responder(player, action_spec_str)`, logs putative events, returns a results `DataFrame`.
    - `save_results(results_df, output_dir, filename_prefix)` (EduMirror/common/measurement/surveyor.py:53): writes `*_answers.json` and `*_results.{csv,json}`.
    - `reset()`, `get_answers()`, `get_results()`: lifecycle management and data access.

- Rater overview (`EduMirror/common/measurement/rater.py`)
  - Structures: `RubricItem`, `Rubric` (EduMirror/common/measurement/rater.py:11, :20).
  - Component: `EduMirrorRater(model)` (EduMirror/common/measurement/rater.py:29).
  - Role: transforms JSONL transcripts into quantitative rubrics-based measurements using keyword criteria and scoring maps.
  - Key functions:
    - `load_transcript(path)` (EduMirror/common/measurement/rater.py:33): reads JSONL event lines.
    - `analyze_transcript(transcript, rubric)` (EduMirror/common/measurement/rater.py:49): extracts agent, matches criteria, maps to scores/severity, returns `DataFrame`.
    - `apply_rubrics(transcript, rubrics)` (EduMirror/common/measurement/rater.py:118): batch analysis across rubrics.
    - `save_results(df, output_dir, filename_prefix)` (EduMirror/common/measurement/rater.py:111): writes results to CSV/JSON.

- Available questionnaires (`EduMirror/common/measurement/questionnaire/`)
  - Includes widely used scales such as `rses.py` (Rosenberg Self-Esteem), `incom.py` (Iowa–Netherlands Comparison), `spin.py` (Social Phobia Inventory), plus `bfne.py`, `dass21.py`, `erq.py`, `panas_c.py`, `panas_x.py`, `stai.py`, `sci2.py`, `scs.py`, `gse.py`, `imi.py`, `pacs.py`, `pjs.py`, `fsps.py`, `fqs.py`, `ucla8.py`, `yms.py`, `bpns_g.py`, `bpnsfs_autonomy.py`, `pss10.py`, `pssm_short.py`, `lsdq.py`, `mvs_short.py`, `geds.py`, `gms.py`, `gossip_scale.py`, `perceived_safety.py`, `sasa.py`, `rsq.py`, `sobi_ps.py`, `srasr.py`, `cas.py`, `ces.py`, `cses_public.py`, `ams.py`.

- Available rubrics (`EduMirror/common/measurement/rubrics/`)
  - Includes `cooperation_competition.py`, `collaboration_quality.py`, `communication_styles.py`, `conformity_level.py`, `peer_social_acceptance.py`, `peer_resistance.py`, `identity_autonomy.py`, `intergroup_contact_quality.py`, `parental_involvement.py`, `parental_aggression.py`, `romantic_rejection_behavior.py`, `school_avoidance.py`, `smart_goal_quality.py`, `social_initiation.py`, `academic_dishonesty.py`, `materialism_behaviors.py`, `materialism_consumption.py`, `bullying_bystander.py`, `bystander_intervention.py`, `exclusionary_behavior.py`, `iep_collaboration.py`, `restorative_vs_punitive_rubric.py`.

- Notes
  - Surveyor produces structured, participant-linked survey results mid-simulation; Rater encodes behavior from final transcripts post-simulation.
  - Results are saved under `results/<scenario_name>/run_<timestamp>/condition_<name>/` with separate files for events and measurements, enabling reproducible analysis.

## Simulation Utilities Overview
- `checkpoint_manager.py`
  - Purpose: standardized checkpoint save/load and inventory of checkpoints
  - Key APIs:
    - `CheckpointManager` class (`EduMirror/common/simulation_utils/checkpoint_manager.py:29`)
      - `get_checkpoint_path(name)`: builds a normalized `.pkl` path
      - `save_checkpoint(sim, name)`: saves via `save_simulation_state`
      - `load_checkpoint(name, config, model, embedder)`: loads or falls back to a fresh simulation
      - `list_checkpoints()`: lists available checkpoints
      - `checkpoint_exists(name)`: existence and validity check
    - Standalone functions
      - `save_simulation_state(sim, filepath)` (`EduMirror/common/simulation_utils/checkpoint_manager.py:120`)
      - `load_simulation_from_checkpoint(filepath, config, model, embedder)` (`EduMirror/common/simulation_utils/checkpoint_manager.py:165`)

- `config.py`
  - Purpose: central configuration for API keys, base URLs, and defaults per environment
  - Key APIs:
    - `get_api_key(api_type)` (`EduMirror/common/simulation_utils/config.py:83`)
    - `get_base_url(api_type)` (`EduMirror/common/simulation_utils/config.py:128`)
    - `get_default_model_config(environment)` (`EduMirror/common/simulation_utils/config.py:159`)
    - `is_api_key_configured(api_type)` (`EduMirror/common/simulation_utils/config.py:175`)
    - `get_current_environment()` (`EduMirror/common/simulation_utils/config.py:194`) via `EDUSIM_ENV`
    - `validate_configuration()` (`EduMirror/common/simulation_utils/config.py:207`)

- `intervention_runner.py`
  - Purpose: build and execute pre–intervention–post pipelines, write JSONL logs per branch
  - Key APIs:
    - `InterventionSpec(name, scenes, output_label)` (`EduMirror/common/simulation_utils/intervention_runner.py:11`)
    - `InterventionScenarioRunner(builder, entities, initializer_params, output_root)` (`EduMirror/common/simulation_utils/intervention_runner.py:18`)
      - `set_pipeline(pre_scenes, post_scenes)`
      - `set_interventions(interventions)`
      - `run_pre_and_checkpoint(verbose=True)`: runs pre-scenes and returns log
      - `run_branch(intervention, verbose=True)`: runs full branch and writes `simulation_events.jsonl` to `condition_<label>/`
      - `run_all_branches(verbose=True)`: iterate all `InterventionSpec`

- `log_to_comic.py`
  - Purpose: convert simulation logs into 4-panel comic summaries; REST image generation with graceful fallback
  - Key APIs:
    - `LogToComicGenerator(text_model_config=None, image_model_name, image_style)` (`EduMirror/common/simulation_utils/log_to_comic.py:10`)
      - `parse_log(jsonl_path)`: load events
      - `structure_narrative(events)`: LLM-structured panels or heuristic fallback
      - `build_image_prompts(scene_spec)`: prompts for each panel
      - `generate_images(prompts, out_dir)`: generate images (requires `GEMINI_API_KEY`); falls back to PIL if request fails
      - `render_comic(image_paths, out_path, layout)`: compose final comic

- `model_setup.py`
  - Purpose: standardized language model and embedder setup
  - Key APIs:
    - `ModelConfig(...)` (`EduMirror/common/simulation_utils/model_setup.py:30`)
    - `create_model_config_from_environment(environment=None, **overrides)` (`EduMirror/common/simulation_utils/model_setup.py:62`)
    - `create_language_model(config=None)` (`EduMirror/common/simulation_utils/model_setup.py:101`)
    - `create_simple_embedder(embedding_dim=384)` (`EduMirror/common/simulation_utils/model_setup.py:147`)
    - `create_openai_embedder(model_name='text-embedding-3-small', api_key=None)` (`EduMirror/common/simulation_utils/model_setup.py:181`)
    - Predefined configs: `DEFAULT_CONFIG`, `TEST_CONFIG`, `PRODUCTION_CONFIG`, `GPT4_CONFIG`, `GPT4_TURBO_CONFIG`

- `scene_builder.py`
  - Purpose: assemble game masters and scenes, run sequences
  - Key APIs:
    - `SceneBuilder(model, embedder_model)` (`EduMirror/common/simulation_utils/scene_builder.py:11`)
      - `build_dialogic_and_dramaturgic_game_master(name, entities, scenes)` (`EduMirror/common/simulation_utils/scene_builder.py:21`)
      - `build_initializer_game_master(name, entities, params)` (`EduMirror/common/simulation_utils/scene_builder.py:34`)
      - `make_scene_type(name, default_premise=None, action_spec=None, game_master_name=None, possible_participants=None)` (`EduMirror/common/simulation_utils/scene_builder.py:50`)
      - `make_scene(scene_type, participants, num_rounds, start_time=None, premise=None)` (`EduMirror/common/simulation_utils/scene_builder.py:66`)
      - `run_with_sequential_engine(game_masters, entities, premise='', max_steps=200, verbose=False, log=None)` (`EduMirror/common/simulation_utils/scene_builder.py:82`)

- `time_manager.py`
  - Purpose: simple wrappers for Concordia clocks to control simulation time
  - Key APIs:
    - `create_fixed_interval_clock(start=None, step_minutes=10)` (`EduMirror/common/simulation_utils/time_manager.py:7`)
    - `create_multi_interval_clock(start=None, step_sizes=(timedelta(...),))` (`EduMirror/common/simulation_utils/time_manager.py:12`)
    - `advance(clock)` (`EduMirror/common/simulation_utils/time_manager.py:16`), `set_time(clock, time)` (`:20`), `now(clock)` (`:24`), `current_interval_str(clock)` (`:28`)
- Scenario modules (`EduMirror/scenarios/<scenario>/`)
  - Each scenario includes `agents.py` (roles and personas) and `main.py` (entry and orchestration)
  - Topics include bystander effects, social comparison, parent–teacher communication, bullying, academic integrity, social pressure, romantic rejection, and more
- Dual-track measurement protocol
  - Post-Hoc Rater: quantitative coding of interaction logs
  - In-Situ Surveyor: structured surveys during the scenario to capture internal states

## AgentFactory: Available Agents and Usage
- Overview
  - Unified API for creating agents with consistent architecture.
  - Location: `EduMirror/common/agent/agent_factory.py:38` (class `AgentFactory`).
  - Inputs: a language model instance and a sentence embedder function returning `numpy.ndarray`.

- Responsibilities
  - Create base agents using a `basic_with_plan` prefab and an associative memory bank populated with formative memories.
  - Maintain optional external builders registry for value-oriented agents.

- Built-in builders (core personas)
  - `create_student(name, goal, traits, formative_memories)` (`EduMirror/common/agent/agent_factory.py:254`)
  - `create_teacher(name, goal, traits, formative_memories, subject_area)` (`EduMirror/common/agent/agent_factory.py:288`)
  - `create_parent(name, goal, traits, formative_memories, child_name)` (`EduMirror/common/agent/agent_factory.py:325`)
  - `create_custom_agent(name, goal, traits, formative_memories, role_description)` (`EduMirror/common/agent/agent_factory.py:362`)

- External value-agent builders (optional)
  - `register_external_builders()` (`EduMirror/common/agent/agent_factory.py:67`) enables:
    - `create_value_agent_psych(...)` (`EduMirror/common/agent/agent_factory.py:165`): value-driven agent with psychological profiles and `selected_desires`, `predefined_setting`, `context_dict`.
    - `create_value_agent_social(...)` (`EduMirror/common/agent/agent_factory.py:206`): social-personality agent with `social_personality`, `stored_target_folder`, `agent_names`, `current_time`.

- Outputs
  - All builders return `EntityAgentWithLogging` with a configured memory bank.
  - Formative memories influence retrieval and reasoning via `basic_associative_memory`.

- Integration notes
  - Ensure `concordia-git/` is importable (editable install or `PYTHONPATH`).
  - Agents are designed to plug into `SceneBuilder` and `InterventionScenarioRunner` pipelines for simulation orchestration.

## Running and Outputs
- Purpose: standardized, reproducible outputs per run and per intervention condition.
- Path layout: `results/<scenario_name>/run_<timestamp>/condition_<name>/`.
- Key files:
  - `simulation_events.jsonl`: normalized event log (step, scene, participants, event).
  - `measurements.json`: aggregated dual-track results (rater + surveyor).
- Analysis: compare condition folders to evaluate intervention effects.
- Generation: JSONL logs are written during branch execution (see `EduMirror/common/simulation_utils/intervention_runner.py:147-149`).

## Scenario Overview and Structure
- Overview: each scenario is an independent module that defines roles, interventions, measurement, and outputs.
- Topics include (see `EduMirror/scenarios/` for complete list): bystander effects, social comparison, parent–teacher communication, bullying, academic integrity, social pressure, romantic rejection, student integration, and more.

- Scenario directory structure (example): `EduMirror/scenarios/<scenario_name>/`
  - Required files:
    - `__init__.py`: module initialization
    - `agents.py`: roles and personas (traits, goal, formative_memories)
    - `main.py`: scenario entry and orchestration (init, interventions, measurement, outputs)

- Result outputs: `results/<scenario_name>/run_<timestamp>/condition_<name>/`
  - `simulation_events.jsonl`: process log
  - `measurements.json`: quantitative measurement results (rater + surveyor)

## FAQ and Troubleshooting
- `import concordia` fails
  - In `concordia-git/` run `python -m pip install -e .`, or set `PYTHONPATH` to `concordia-git`
- Language model unavailable / missing API keys
  - Use a local backend (e.g., `Ollama`), or select `no_language_model`
- Dependency conflicts or environment issues
  - Clean the environment and reinstall; check `PYTHONPATH` and model backend settings

## Citation and License
- Cite the Concordia framework (add official repository link and license info)
- Project citation format (for papers and replication)
- License statement consistent with anonymous open-source; do not include any secrets or keys

## Example Scenario Run
- Run the family economic pressure social decision scenario from the scenario project root:
  `python scenarios/family_econ_pressure_social_decision/main.py`
