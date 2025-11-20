# Copyright 2024 EduSim Project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Utilities for setting up language models and embedders for EduSim scenarios.

This module provides standardized functions for creating and configuring
language models and embedding functions that can be reused across all
EduSim simulation scenarios.
"""

import os
import numpy as np
from typing import Callable, Optional
from concordia.language_model import language_model
from concordia.language_model import utils
from .config import get_api_key, get_base_url, get_default_model_config, get_current_environment


class ModelConfig:
    """Configuration class for language model setup."""
    
    def __init__(
        self,
        api_type: str = 'openai',
        model_name: str = 'gpt-4.1-mini',
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        device: Optional[str] = None,
        disable_language_model: bool = False
    ):
        """Initialize model configuration.
        
        Args:
            api_type: The type of API to use (e.g., 'openai', 'google_aistudio_model')
            model_name: The name of the specific model to use
            api_key: The API key to use (if None, will auto-load from config)
            base_url: The base URL for the API (if None, will auto-load from config)
            device: The device to use for model processing (if supported)
            disable_language_model: If True, use a mock model for testing
        """
        self.api_type = api_type
        self.model_name = model_name
        # Auto-load API key from config if not provided
        self.api_key = api_key or get_api_key(api_type)
        # Auto-load base URL from config if not provided
        self.base_url = base_url or get_base_url(api_type)
        self.device = device
        self.disable_language_model = disable_language_model


def create_model_config_from_environment(
    environment: Optional[str] = None,
    **kwargs
) -> ModelConfig:
    """Create a ModelConfig based on environment settings.
    
    Args:
        environment: Environment name ('development', 'testing', 'production')
                    If None, uses current environment from EDUSIM_ENV
        **kwargs: Additional arguments to override default config
        
    Returns:
        ModelConfig instance configured for the environment
        
    Example:
        # Use current environment settings
        config = create_model_config_from_environment()
        
        # Use production settings
        config = create_model_config_from_environment('production')
        
        # Override specific settings
        config = create_model_config_from_environment(
            'production',
            model_name='gpt-4'
        )
    """
    if environment is None:
        environment = get_current_environment()
    
    # Get default config for environment
    default_config = get_default_model_config(environment)
    
    # Merge with any overrides
    final_config = {**default_config, **kwargs}
    
    return ModelConfig(**final_config)


def create_language_model(
    config: Optional[ModelConfig] = None
) -> language_model.LanguageModel:
    """Create and configure a language model using standardized settings.
    
    This function provides a centralized way to create language models
    for all EduSim scenarios, ensuring consistency across the platform.
    
    Args:
        config: ModelConfig instance. If None, uses environment-based default.
        
    Returns:
        Configured language model instance
        
    Example:
        # Use environment-based default configuration
        model = create_language_model()
        
        # Use custom configuration
        config = ModelConfig(
            api_type='openai',
            model_name='gpt-4',
            disable_language_model=False
        )
        model = create_language_model(config)
        
        # Use environment-specific config with overrides
        config = create_model_config_from_environment(
            'production',
            model_name='gpt-4'
        )
        model = create_language_model(config)
    """
    if config is None:
        config = create_model_config_from_environment()
    
    return utils.language_model_setup(
        api_type=config.api_type,
        model_name=config.model_name,
        api_key=config.api_key,
        base_url=config.base_url,
        device=config.device,
        disable_language_model=config.disable_language_model
    )


def create_simple_embedder(embedding_dim: int = 384) -> Callable[[str], np.ndarray]:
    """Create a simple hash-based embedding function for demonstration purposes.
    
    This embedder is suitable for testing and development. For production use,
    consider using more sophisticated embedding models.
    
    Args:
        embedding_dim: Dimension of the embedding vectors
        
    Returns:
        Embedding function that takes text and returns numpy array
        
    Example:
        embedder = create_simple_embedder()
        embedding = embedder("Hello world")
        print(embedding.shape)  # (384,)
    """
    def simple_embedder(text: str) -> np.ndarray:
        """Convert text to a simple hash-based embedding vector.
        
        Args:
            text: Input text to embed
            
        Returns:
            Numpy array representing the text embedding
        """
        # Simple hash-based embedding for demonstration
        hash_value = hash(text)
        # Convert to a simple vector with values between 0 and 1
        return np.array([float((hash_value + i) % 1000) / 1000.0 for i in range(embedding_dim)])
    
    return simple_embedder


def create_openai_embedder(
    model_name: str = 'text-embedding-3-small',
    api_key: Optional[str] = None
) -> Callable[[str], np.ndarray]:
    """Create an OpenAI-based embedding function.
    
    Note: This requires the openai package and a valid API key.
    
    Args:
        model_name: OpenAI embedding model name
        api_key: OpenAI API key (if None, uses environment variable)
        
    Returns:
        Embedding function that uses OpenAI's embedding API
        
    Raises:
        ImportError: If openai package is not installed
        ValueError: If API key is not provided
    """
    try:
        import openai
    except ImportError:
        raise ImportError(
            "OpenAI package is required for OpenAI embedder. "
            "Install with: pip install openai"
        )
    
    if api_key is None:
        api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        raise ValueError(
            "OpenAI API key is required. Set OPENAI_API_KEY environment variable "
            "or pass api_key parameter."
        )
    
    client = openai.OpenAI(api_key=api_key)
    
    def openai_embedder(text: str) -> np.ndarray:
        """Get embedding from OpenAI API.
        
        Args:
            text: Input text to embed
            
        Returns:
            Numpy array representing the text embedding
        """
        response = client.embeddings.create(
            model=model_name,
            input=text
        )
        return np.array(response.data[0].embedding)
    
    return openai_embedder


# Predefined configurations for common use cases
# These now automatically use the configured API keys
DEFAULT_CONFIG = create_model_config_from_environment('development')
TEST_CONFIG = create_model_config_from_environment('testing')
PRODUCTION_CONFIG = create_model_config_from_environment('production')
GPT4_CONFIG = ModelConfig(model_name='gpt-4', disable_language_model=False)
GPT4_TURBO_CONFIG = ModelConfig(model_name='gpt-4-turbo', disable_language_model=False)