"""
LLM service factory for creating configured LLM clients.
"""
import os
import logging
from typing import Any

# pydantic-ai >= 1.x renamed OpenAIModel -> OpenAIChatModel and
# OpenAIModelSettings -> OpenAIChatModelSettings. Import under the historical
# names so the rest of this module stays unchanged and both versions work.
try:
    from pydantic_ai.models.openai import OpenAIChatModel as OpenAIModel
    from pydantic_ai.models.openai import OpenAIChatModelSettings as OpenAIModelSettings
except ImportError:  # older pydantic-ai (< 1.x) still exposes the pre-rename names
    from pydantic_ai.models.openai import OpenAIModel
    from pydantic_ai.models.openai import OpenAIModelSettings

import re
from urllib.parse import urlparse

from pydantic_ai.models import Model
from pydantic_ai.models.anthropic import AnthropicModel, AnthropicModelSettings
from pydantic_ai.models.openai import OpenAIResponsesModel, OpenAIResponsesModelSettings
from pydantic_ai.providers.anthropic import AnthropicProvider
from pydantic_ai.providers.openai import OpenAIProvider

logger = logging.getLogger(__name__)
from pydantic_ai.models.fallback import FallbackModel
from openai import OpenAI, OpenAIError

from codewiki.src.config import Config
from codewiki.src.be.usage_tracker import record_completion


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


# Every SDK call retries a dropped connection, a rate limit and a 5xx on its own (backoff by the SDK), before
# the agent run sees an error at all. A run that still fails is retried whole by the orchestrator.
AGENT_MODEL_MAX_RETRIES = 6


def _agent_api(base_url: str) -> str:
    """Which wire API an agent model is called through, from its provider's host.

    - Anthropic (`api.anthropic.com`): the native Messages API, so the agent's repeated prefix (instructions, tool
      definitions, the conversation so far) is read from the prompt cache at a tenth of the input price. Through the
      OpenAI-compatible endpoint nothing was cached: 6.8M input tokens and 0 cache reads on one repository.
    - OpenAI (`api.openai.com`): the Responses API. Reasoning models refuse function tools on chat completions
      ("Function tools with reasoning_effort are not supported ... use /v1/responses"), so every agent request
      failed there and fell through to the fallback model.
    - Any other host: OpenAI-compatible chat completions, as before.
    """
    host = (urlparse(base_url).hostname or '').lower()
    if host == 'anthropic.com' or host.endswith('.anthropic.com'):
        return 'anthropic'
    if host == 'api.openai.com':
        return 'responses'
    return 'chat'


def _create_agent_model(stage: str, model_name: str, config: Config) -> Model:
    """One agent model (`main` or `fallback`), on the API its provider's host calls for."""
    max_tokens = getattr(config, f'{stage}_max_tokens', None) or get_max_output_tokens()
    temperature = getattr(config, f'{stage}_temperature', 0.0)
    temperature_supported = getattr(config, f'{stage}_temperature_supported', True)
    base_url = getattr(config, f'{stage}_base_url', None)
    api_key = getattr(config, f'{stage}_api_key', None)
    if not base_url:
        raise ValueError(
            f"{stage}_base_url is required in configuration for the {stage} model.\n"
            f"Model: {model_name}\n"
            f"Please set via CLI: --{stage}-base-url <url>"
        )
    if not api_key:
        raise ValueError(
            f"{stage}_api_key is required in configuration for the {stage} model.\n"
            f"Model: {model_name}\n"
            f"Please set via CLI: --{stage}-api-key <key>"
        )

    settings: dict = {'max_tokens': max_tokens, 'max_retries': AGENT_MODEL_MAX_RETRIES}
    if temperature_supported:
        settings['temperature'] = temperature

    api = _agent_api(base_url)
    logger.info(f"🔌 {stage} model {model_name}: {api} API at {base_url}")
    if api == 'anthropic':
        # The SDK appends /v1/messages itself, so the configured `.../v1` is the host.
        anthropic_base = re.sub(r'/v1/?$', '', base_url.rstrip('/'))
        return AnthropicModel(
            model_name,
            provider=AnthropicProvider(api_key=api_key, base_url=anthropic_base),
            settings=AnthropicModelSettings(
                **settings,
                anthropic_cache_instructions=True,
                anthropic_cache_tool_definitions=True,
                anthropic_cache=True,
            ),
        )
    provider = OpenAIProvider(base_url=base_url, api_key=api_key)
    if api == 'responses':
        return OpenAIResponsesModel(model_name, provider=provider, settings=OpenAIResponsesModelSettings(**settings))
    return OpenAIModel(model_name=model_name, provider=provider, settings=OpenAIModelSettings(**settings))


def create_main_model(config: Config) -> Model:
    """The main agent model (module documentation)."""
    return _create_agent_model('main', config.main_model, config)


def create_fallback_model(config: Config) -> Model:
    """The model an agent request falls back to when the main model fails."""
    return _create_agent_model('fallback', config.fallback_model, config)


def create_cluster_model(config: Config) -> OpenAIModel:
    """
    Create the cluster model (used for module clustering).

    Validates cluster_base_url is configured and creates an OpenAI-compatible client
    with cluster-specific settings from config.

    Args:
        config: Configuration with cluster_* provider settings

    Returns:
        OpenAIModel configured for clustering operations

    Raises:
        ValueError: If cluster_base_url is not configured
    """
    # Validate cluster base URL is configured
    base_url = getattr(config, 'cluster_base_url', None)
    if not base_url:
        raise ValueError(
            "cluster_base_url is required in configuration for clustering operations.\n"
            f"Model: {config.cluster_model}\n"
            "Please set via CLI: --cluster-base-url <url>\n"
            "Or in config file: cluster_base_url = '<url>'"
        )

    # Get cluster-specific settings
    api_version = getattr(config, 'cluster_api_version', None)
    max_tokens = getattr(config, 'cluster_max_tokens', None) or get_max_output_tokens()
    temperature = getattr(config, 'cluster_temperature', 0.0)
    temperature_supported = getattr(config, 'cluster_temperature_supported', True)

    # Build settings dict - only include temperature if model supports it
    settings_dict = {'max_tokens': max_tokens}
    if temperature_supported:
        settings_dict['temperature'] = temperature

    # Prepare default headers for API version (Anthropic models)
    default_headers = {}
    if api_version:
        default_headers['anthropic-version'] = api_version

    # Get per-provider API key
    api_key = getattr(config, 'cluster_api_key', None)
    if not api_key:
        raise ValueError(
            "cluster_api_key is required in configuration for clustering operations.\n"
            f"Model: {config.cluster_model}\n"
            "Please set via CLI: --cluster-api-key <key>\n"
            "Different AI providers require different API keys."
        )

    return OpenAIModel(
        model_name=config.cluster_model,
        provider=OpenAIProvider(
            base_url=base_url,
            api_key=api_key,
            # NOTE: pydantic-ai's OpenAIProvider takes only base_url, api_key,
            # openai_client and http_client - there is no default_headers
            # parameter (verified against pydantic-ai 2.40.0), so passing one
            # raises TypeError. To send anthropic-version here, build an
            # AsyncOpenAI client with default_headers and pass it as
            # openai_client=.
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


def create_openai_client(config: Config, model: str = None) -> OpenAI:
    """
    Create OpenAI client from configuration.

    Args:
        config: Configuration with per-provider settings
        model: Model name to determine which base_url to use (cluster, main, or fallback)

    Returns:
        OpenAI client configured for the specified model

    Raises:
        ValueError: When base_url is not configured for the specified model
    """
    # Determine which model we're using to select the right base_url and api_version
    if model is None:
        model = config.main_model

    # Select base_url, api_version, and api_key based on model
    model_stage = "main/generation"
    if model == config.cluster_model:
        base_url = getattr(config, 'cluster_base_url', None)
        api_version = getattr(config, 'cluster_api_version', None)
        api_key = getattr(config, 'cluster_api_key', None)
        model_stage = "cluster"
        config_field = "cluster_base_url"
        api_key_field = "cluster_api_key"
    elif model == config.fallback_model:
        base_url = getattr(config, 'fallback_base_url', None)
        api_version = getattr(config, 'fallback_api_version', None)
        api_key = getattr(config, 'fallback_api_key', None)
        model_stage = "fallback"
        config_field = "fallback_base_url"
        api_key_field = "fallback_api_key"
    else:  # main/generation model
        base_url = getattr(config, 'main_base_url', None)
        api_version = getattr(config, 'main_api_version', None)
        api_key = getattr(config, 'main_api_key', None)
        config_field = "main_base_url"
        api_key_field = "main_api_key"

    if not base_url:
        raise ValueError(
            f"base_url not configured for {model_stage} model '{model}'.\n"
            f"Please set via CLI: --{config_field.replace('_', '-')} <url>\n"
            f"Or in config file: {config_field} = '<url>'"
        )

    if not api_key:
        raise ValueError(
            f"api_key not configured for {model_stage} model '{model}'.\n"
            f"Please set via CLI: --{api_key_field.replace('_', '-')} <key>\n"
            "Different AI providers require different API keys."
        )

    # Prepare default headers for API version (Anthropic models)
    default_headers = {}
    if api_version:
        default_headers['anthropic-version'] = api_version

    return OpenAI(
        base_url=base_url,
        api_key=api_key,
        default_headers=default_headers if default_headers else None,
    )


def call_llm(
    prompt: str,
    config: Config,
    model: str = None,
    temperature: float = 0.0
) -> str:
    """
    Call LLM with the given prompt, with comprehensive error context.

    Args:
        prompt: The prompt to send
        config: Configuration containing LLM settings
        model: Model name (defaults to config.main_model)
        temperature: Temperature setting

    Returns:
        LLM response text

    Raises:
        RuntimeError: When LLM API call fails (wraps original error with context)
    """
    if model is None:
        model = config.main_model

    # Determine which stage we're in based on the model being used
    # This ensures we use the correct max_token_field for each model
    stage = 'generation'  # default
    model_stage_name = "main/generation"
    if model == config.cluster_model:
        stage = 'cluster'
        model_stage_name = 'cluster'
    elif model == config.fallback_model:
        stage = 'fallback'
        model_stage_name = 'fallback'

    # Get base_url for error reporting
    if stage == 'cluster':
        base_url = getattr(config, 'cluster_base_url', 'not configured')
    elif stage == 'fallback':
        base_url = getattr(config, 'fallback_base_url', 'not configured')
    else:  # main/generation
        base_url = getattr(config, 'main_base_url', 'not configured')

    # Log LLM invocation details
    logger.info("🤖 LLM API Invocation")
    logger.info(f"   ├─ Stage: {model_stage_name}")
    logger.info(f"   ├─ Model: {model}")
    logger.info(f"   ├─ Base URL: {base_url}")
    logger.info(f"   ├─ Prompt length: {len(prompt)} chars (~{len(prompt) // 4} tokens)")
    logger.info(f"   │  └─ Preview: {prompt[:150]}...")
    logger.info(f"   ├─ Temperature: {temperature}")

    try:
        client = create_openai_client(config, model=model)

        # Determine max_tokens_value based on which model is being used
        if model == config.cluster_model:
            max_tokens_value = getattr(config, 'cluster_max_tokens', None) or get_max_output_tokens()
        elif model == config.fallback_model:
            max_tokens_value = getattr(config, 'fallback_max_tokens', None) or get_max_output_tokens()
        else:  # main/generation model
            max_tokens_value = getattr(config, 'main_max_tokens', None) or get_max_output_tokens()

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

        logger.info(f"   ├─ Max tokens: {max_tokens_value} (field: {max_token_field})")
        logger.info(f"   ├─ Temperature supported: {temperature_supported}")
        logger.info(f"   └─ 🚀 Sending request to LLM API...")

        response = client.chat.completions.create(**kwargs)
        record_completion(kwargs.get("model") or model or "unknown", response)

        response_content = response.choices[0].message.content
        response_tokens = len(response_content) // 4  # Approximate token count

        logger.info(f"   ✅ LLM Response Received")
        logger.info(f"   ├─ Response length: {len(response_content)} chars (~{response_tokens} tokens)")
        logger.info(f"   └─ Preview: {response_content[:150]}...")

        return response_content

    except OpenAIError as e:
        # Add context to OpenAI SDK errors
        raise RuntimeError(
            f"LLM API call failed for {model_stage_name} model '{model}'.\n"
            f"Base URL: {base_url}\n"
            f"Temperature: {temperature} (supported: {temperature_supported})\n"
            f"Max tokens: {kwargs.get('max_tokens') or kwargs.get('max_completion_tokens', 'not set')} "
            f"(field: {max_token_field})\n"
            f"Original error: {type(e).__name__}: {str(e)}"
        ) from e

    except Exception as e:
        # Wrap unexpected errors with context
        raise RuntimeError(
            f"Unexpected error calling {model_stage_name} model '{model}': "
            f"{type(e).__name__}: {str(e)}"
        ) from e
