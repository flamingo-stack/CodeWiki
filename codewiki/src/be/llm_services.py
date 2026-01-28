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


def create_main_model(config: Config) -> OpenAIModel:
    """Create the main LLM model from configuration."""
    # Use config.max_tokens if available, otherwise fallback to env var
    max_tokens = getattr(config, 'max_tokens', None) or get_max_output_tokens()
    return OpenAIModel(
        model_name=config.main_model,
        provider=OpenAIProvider(
            base_url=config.llm_base_url,
            api_key=config.llm_api_key
        ),
        settings=OpenAIModelSettings(
            temperature=0.0,
            max_tokens=max_tokens
        )
    )


def create_fallback_model(config: Config) -> OpenAIModel:
    """Create the fallback LLM model from configuration."""
    # Use config.max_tokens if available, otherwise fallback to env var
    max_tokens = getattr(config, 'max_tokens', None) or get_max_output_tokens()
    return OpenAIModel(
        model_name=config.fallback_model,
        provider=OpenAIProvider(
            base_url=config.llm_base_url,
            api_key=config.llm_api_key
        ),
        settings=OpenAIModelSettings(
            temperature=0.0,
            max_tokens=max_tokens
        )
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
    max_tokens = getattr(config, 'max_tokens', None) or get_max_output_tokens()
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_tokens=max_tokens
    )
    return response.choices[0].message.content