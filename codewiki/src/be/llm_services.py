"""
LLM service factory for creating configured LLM clients.
"""
import os
import logging
from typing import Any

from pydantic_ai.models.openai import OpenAIModel

logger = logging.getLogger(__name__)
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.models.openai import OpenAIModelSettings
from pydantic_ai.models.fallback import FallbackModel
from openai import OpenAI

from codewiki.src.config import Config


# Global request counter for logging progress
_request_counter = {"count": 0, "module": "unknown"}


def reset_request_counter(module_name: str = "unknown"):
    """Reset the request counter for a new module."""
    _request_counter["count"] = 0
    _request_counter["module"] = module_name


def increment_request_counter():
    """Increment request counter and log every 100 requests."""
    _request_counter["count"] += 1
    count = _request_counter["count"]
    module = _request_counter["module"]

    if count % 100 == 0:
        logger.info(f"📊 Module '{module}': {count} LLM requests completed")


def get_max_output_tokens() -> int:
    """
    Get max output tokens from environment variable or use default.

    Environment variable: MAX_OUTPUT_TOKENS
    Default: 16384 (safe for gpt-4o-mini and most models)

    Common values:
    - 16384: gpt-4o-mini, gpt-3.5-turbo, claude-haiku
    - 32768: gpt-4o, gpt-4.1, claude-sonnet, claude-opus
    """
    default_tokens = 16384  # Safe default for mini models
    env_value = os.environ.get('MAX_OUTPUT_TOKENS')
    if env_value:
        try:
            return int(env_value)
        except ValueError:
            logger.warning(f"Invalid MAX_OUTPUT_TOKENS value '{env_value}', using default {default_tokens}")
    return default_tokens


def get_model_max_token_field(stage: str = 'generation') -> str:
    """
    Get the max token parameter field name from environment variable.

    Environment variables:
    - CODEWIKI_CLUSTER_MAX_TOKEN_FIELD (for clustering stage)
    - CODEWIKI_GENERATION_MAX_TOKEN_FIELD (for generation stage)
    - CODEWIKI_FALLBACK_MAX_TOKEN_FIELD (for fallback stage)

    Returns 'max_tokens' for standard models or 'max_completion_tokens' for reasoning models (o3, o3-mini).
    """
    env_var_map = {
        'cluster': 'CODEWIKI_CLUSTER_MAX_TOKEN_FIELD',
        'generation': 'CODEWIKI_GENERATION_MAX_TOKEN_FIELD',
        'fallback': 'CODEWIKI_FALLBACK_MAX_TOKEN_FIELD',
    }

    env_var = env_var_map.get(stage, 'CODEWIKI_GENERATION_MAX_TOKEN_FIELD')
    return os.environ.get(env_var, 'max_tokens')


def create_main_model(config: Config) -> OpenAIModel:
    """
    Create the main LLM model from configuration.

    NOTE: Pydantic AI currently hardcodes the 'max_tokens' parameter name in OpenAIModelSettings.
    For reasoning models (o3, o3-mini) that require 'max_completion_tokens', the direct API call
    in call_llm() uses the correct parameter name. If Pydantic AI models fail with "Unrecognized
    request argument supplied: max_tokens", the system will fall back to the direct API call.
    """
    # Use config.max_tokens if available, otherwise fallback to env var
    max_tokens = getattr(config, 'max_tokens', None) or get_max_output_tokens()
    # Check if model supports custom temperature (use per-provider field)
    temperature = getattr(config, 'main_temperature', 0.0)
    temperature_supported = getattr(config, 'main_temperature_supported', True)

    # Build settings dict - only include temperature if model supports it
    settings_dict = {'max_tokens': max_tokens}
    if temperature_supported:
        settings_dict['temperature'] = temperature

    return OpenAIModel(
        model_name=config.main_model,
        provider=OpenAIProvider(
            base_url=config.llm_base_url,
            api_key=config.llm_api_key
        ),
        settings=OpenAIModelSettings(**settings_dict)
    )


def create_fallback_model(config: Config) -> OpenAIModel:
    """Create the fallback LLM model from configuration."""
    # Use config.max_tokens if available, otherwise fallback to env var
    max_tokens = getattr(config, 'max_tokens', None) or get_max_output_tokens()
    # Check if model supports custom temperature (use per-provider field)
    temperature = getattr(config, 'fallback_temperature', 0.0)
    temperature_supported = getattr(config, 'fallback_temperature_supported', True)

    # Build settings dict - only include temperature if model supports it
    settings_dict = {'max_tokens': max_tokens}
    if temperature_supported:
        settings_dict['temperature'] = temperature

    return OpenAIModel(
        model_name=config.fallback_model,
        provider=OpenAIProvider(
            base_url=config.llm_base_url,
            api_key=config.llm_api_key
        ),
        settings=OpenAIModelSettings(**settings_dict)
    )


class CountingFallbackModel(FallbackModel):
    """FallbackModel wrapper that counts and logs requests every 100 calls."""

    async def request(self, *args, **kwargs):
        """Wrap request to count calls."""
        increment_request_counter()
        return await super().request(*args, **kwargs)


def create_fallback_models(config: Config) -> CountingFallbackModel:
    """Create fallback models chain from configuration with request counting."""
    main = create_main_model(config)
    fallback = create_fallback_model(config)
    return CountingFallbackModel(main, fallback)


def create_openai_client(config: Config) -> OpenAI:
    """Create OpenAI client from configuration."""
    return OpenAI(
        base_url=config.llm_base_url,
        api_key=config.llm_api_key
    )


def call_llm(
    prompt: str,
    config: Config,
    model: str = None,
    temperature: float = 0.0
) -> str:
    """
    Call LLM with the given prompt.

    Args:
        prompt: The prompt to send
        config: Configuration containing LLM settings
        model: Model name (defaults to config.main_model)
        temperature: Temperature setting

    Returns:
        LLM response text
    """
    if model is None:
        model = config.main_model

    client = create_openai_client(config)
    # Use config.max_tokens if available, otherwise fallback to env var
    max_tokens_value = getattr(config, 'max_tokens', None) or get_max_output_tokens()

    # Determine which stage we're in based on the model being used
    # This ensures we use the correct max_token_field for each model
    stage = 'generation'  # default
    if model == config.cluster_model:
        stage = 'cluster'
    elif model == config.fallback_model:
        stage = 'fallback'

    # Get the correct parameter name for max tokens (max_tokens vs max_completion_tokens)
    # GPT-5.2 and reasoning models (o3, o3-mini) use max_completion_tokens instead of max_tokens
    max_token_field = get_model_max_token_field(stage)

    # Check if this model supports custom temperature (use per-provider field)
    if stage == 'cluster':
        temperature_supported = getattr(config, 'cluster_temperature_supported', True)
    elif stage == 'fallback':
        temperature_supported = getattr(config, 'fallback_temperature_supported', True)
    else:  # generation/main
        temperature_supported = getattr(config, 'main_temperature_supported', True)

    # Build kwargs with dynamic parameter name
    kwargs = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        max_token_field: max_tokens_value
    }

    # Only add temperature if model supports it
    if temperature_supported:
        kwargs["temperature"] = temperature

    response = client.chat.completions.create(**kwargs)
    return response.choices[0].message.content