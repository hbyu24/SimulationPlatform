"""Simulation utilities for EduSim project.

This module provides common utilities for simulation management,
including checkpoint saving/loading functionality and model setup.
"""

from .checkpoint_manager import CheckpointManager, save_simulation_state, load_simulation_from_checkpoint
from .model_setup import (
    ModelConfig,
    create_language_model,
    create_model_config_from_environment,
    create_simple_embedder,
    create_openai_embedder,
    DEFAULT_CONFIG,
    TEST_CONFIG,
    PRODUCTION_CONFIG,
    GPT4_CONFIG,
    GPT4_TURBO_CONFIG
)
from .config import (
    get_api_key,
    get_base_url,
    get_default_model_config,
    get_current_environment,
    is_api_key_configured,
    validate_configuration
)
from .intervention_runner import InterventionScenarioRunner, InterventionSpec
from .scene_builder import SceneBuilder
from .time_manager import (
    create_fixed_interval_clock,
    create_multi_interval_clock,
    advance,
    set_time,
    now,
    current_interval_str,
)
from .log_to_comic import LogToComicGenerator

__all__ = [
    'CheckpointManager',
    'save_simulation_state', 
    'load_simulation_from_checkpoint',
    'InterventionScenarioRunner',
    'InterventionSpec',
    'ModelConfig',
    'create_language_model',
    'create_model_config_from_environment',
    'create_simple_embedder',
    'create_openai_embedder',
    'DEFAULT_CONFIG',
    'TEST_CONFIG',
    'PRODUCTION_CONFIG',
    'GPT4_CONFIG',
    'GPT4_TURBO_CONFIG',
    'get_api_key',
    'get_base_url',
    'get_default_model_config',
    'get_current_environment',
    'is_api_key_configured',
    'validate_configuration'
]

__all__ += [
    'SceneBuilder',
    'create_fixed_interval_clock',
    'create_multi_interval_clock',
    'advance',
    'set_time',
    'now',
    'current_interval_str',
    'LogToComicGenerator',
]
