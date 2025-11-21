# Copyright 2024 EduMirror Project
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

"""Configuration management for EduMirror project.

This module provides centralized configuration management for API keys,
model settings, and other project-wide configurations.
"""

import os
from typing import Optional, Dict, Any

# =============================================================================
# API KEYS CONFIGURATION
# =============================================================================
# Configure your API keys here. These will be used across all EduMirror scenarios.
# You only need to set them once, and all simulations will use these keys.

# OpenAI API Key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# OpenAI Base URL (optional)
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")

# Google AI Studio API Key (optional)
# Uncomment and set if you want to use Google AI models
# GOOGLE_AI_STUDIO_API_KEY = "your-google-ai-studio-key-here"

# Google Cloud API Key (optional)
# Uncomment and set if you want to use Google Cloud Vertex AI
# GOOGLE_CLOUD_API_KEY = "your-google-cloud-key-here"

# Amazon Bedrock API Key (optional)
# Uncomment and set if you want to use Amazon Bedrock
# AMAZON_BEDROCK_API_KEY = "your-amazon-bedrock-key-here"

# Mistral API Key (optional)
# Uncomment and set if you want to use Mistral AI
# MISTRAL_API_KEY = "your-mistral-key-here"

# Together AI API Key (optional)
# Uncomment and set if you want to use Together AI
# TOGETHER_AI_API_KEY = "your-together-ai-key-here"

# =============================================================================
# DEFAULT MODEL CONFIGURATIONS
# =============================================================================

# Default model settings for different environments
DEFAULT_MODEL_CONFIGS = {
    'development': {
        'api_type': 'openai',
        'model_name': 'gpt-4.1-nano',
        'disable_language_model': True,  # Safe default for development
    },
    'testing': {
        'api_type': 'openai',
        'model_name': 'gpt-4.1-nano',
        'disable_language_model': True,  # Use mock model for testing
    },
    'production': {
        'api_type': 'openai',
        'model_name': 'gpt-4.1-nano',
        'disable_language_model': False,  # Use real model for production
    }
}

# =============================================================================
# CONFIGURATION FUNCTIONS
# =============================================================================

def get_api_key(api_type: str) -> Optional[str]:
    """Get API key for the specified API type.
    
    Args:
        api_type: The type of API (e.g., 'openai', 'google_aistudio_model')
        
    Returns:
        The API key if configured, None otherwise
        
    Example:
        api_key = get_api_key('openai')
        if api_key:
            print("OpenAI API key is configured")
    """
    # First check configured keys in this file (prioritize config file)
    config_key_map = {
        'openai': OPENAI_API_KEY,
        'google_aistudio_model': globals().get('GOOGLE_AI_STUDIO_API_KEY'),
        'google_cloud_custom_model': globals().get('GOOGLE_CLOUD_API_KEY'),
        'amazon_bedrock': globals().get('AMAZON_BEDROCK_API_KEY'),
        'mistral': globals().get('MISTRAL_API_KEY'),
        'together_ai': globals().get('TOGETHER_AI_API_KEY'),
    }
    
    config_key = config_key_map.get(api_type)
    if config_key:
        return config_key
    
    # Then check environment variables as fallback
    env_key_map = {
        'openai': 'OPENAI_API_KEY',
        'google_aistudio_model': 'GOOGLE_AI_STUDIO_API_KEY',
        'google_cloud_custom_model': 'GOOGLE_CLOUD_API_KEY',
        'amazon_bedrock': 'AMAZON_BEDROCK_API_KEY',
        'mistral': 'MISTRAL_API_KEY',
        'together_ai': 'TOGETHER_AI_API_KEY',
    }
    
    env_var = env_key_map.get(api_type)
    if env_var and os.getenv(env_var):
        return os.getenv(env_var)
    
    return None


def get_base_url(api_type: str) -> Optional[str]:
    """Get base URL for the specified API type.
    
    Args:
        api_type: The type of API (e.g., 'openai', 'google_aistudio_model')
        
    Returns:
        The base URL if configured, None otherwise
        
    Example:
        base_url = get_base_url('openai')
        if base_url:
            print(f"OpenAI base URL: {base_url}")
    """
    # First check environment variables (they take precedence)
    env_key_map = {
        'openai': 'OPENAI_BASE_URL',
    }
    
    env_var = env_key_map.get(api_type)
    if env_var and os.getenv(env_var):
        return os.getenv(env_var)
    
    # Then check configured base URLs in this file
    config_key_map = {
        'openai': globals().get('OPENAI_BASE_URL'),
    }
    
    return config_key_map.get(api_type)


def get_default_model_config(environment: str = 'development') -> Dict[str, Any]:
    """Get default model configuration for the specified environment.
    
    Args:
        environment: The environment ('development', 'testing', 'production')
        
    Returns:
        Dictionary containing model configuration
        
    Example:
        config = get_default_model_config('production')
        print(f"Production model: {config['model_name']}")
    """
    return DEFAULT_MODEL_CONFIGS.get(environment, DEFAULT_MODEL_CONFIGS['development'])


def is_api_key_configured(api_type: str) -> bool:
    """Check if API key is configured for the specified API type.
    
    Args:
        api_type: The type of API to check
        
    Returns:
        True if API key is configured, False otherwise
        
    Example:
        if is_api_key_configured('openai'):
            print("Ready to use OpenAI models")
        else:
            print("Please configure OpenAI API key")
    """
    api_key = get_api_key(api_type)
    return api_key is not None and api_key.strip() != ""


def get_current_environment() -> str:
    """Get current environment from environment variable or default to development.
    
    Returns:
        Current environment string
        
    Example:
        env = get_current_environment()
        print(f"Running in {env} environment")
    """
    return os.getenv('EDUSIM_ENV', 'development')


def validate_configuration() -> Dict[str, bool]:
    """Validate current configuration and return status for each API type.
    
    Returns:
        Dictionary mapping API types to their configuration status
        
    Example:
        status = validate_configuration()
        for api_type, configured in status.items():
            print(f"{api_type}: {'✓' if configured else '✗'}")
    """
    api_types = ['openai', 'google_aistudio_model', 'google_cloud_custom_model', 
                 'amazon_bedrock', 'mistral', 'together_ai']
    
    return {api_type: is_api_key_configured(api_type) for api_type in api_types}


# =============================================================================
# CONFIGURATION VALIDATION
# =============================================================================

if __name__ == '__main__':
    """Run configuration validation when script is executed directly."""
    print("EduSim Configuration Status")
    print("==========================\n")
    
    # Show current environment
    env = get_current_environment()
    print(f"Current Environment: {env}")
    
    # Show default config for current environment
    default_config = get_default_model_config(env)
    print(f"Default Model: {default_config['model_name']}")
    print(f"API Type: {default_config['api_type']}")
    print(f"Language Model Disabled: {default_config['disable_language_model']}\n")
    
    # Validate API key configurations
    print("API Key Configuration Status:")
    status = validate_configuration()
    
    for api_type, configured in status.items():
        status_symbol = "✓" if configured else "✗"
        status_text = "Configured" if configured else "Not configured"
        print(f"  {api_type:25} {status_symbol} {status_text}")
    
    # Show recommendations
    print("\nRecommendations:")
    if not any(status.values()):
        print("  ⚠️  No API keys configured. Please set at least one API key.")
    elif status.get('openai', False):
        print("  ✅ OpenAI API key configured.")
    else:
        print("  ℹ️  Consider configuring OpenAI API key for best compatibility.")
