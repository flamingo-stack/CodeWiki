"""
Configuration commands for CodeWiki CLI.
"""

import json
import sys
import click
from typing import Optional, List

from codewiki.cli.config_manager import ConfigManager
from codewiki.cli.models.config import AgentInstructions
from codewiki.cli.utils.errors import (
    ConfigurationError, 
    handle_error, 
    EXIT_SUCCESS,
    EXIT_CONFIG_ERROR
)
from codewiki.cli.utils.validation import (
    validate_url,
    validate_api_key,
    validate_model_name,
    is_top_tier_model,
    mask_api_key
)


def parse_patterns(patterns_str: str) -> List[str]:
    """Parse comma-separated patterns into a list."""
    if not patterns_str:
        return []
    return [p.strip() for p in patterns_str.split(',') if p.strip()]


def parse_bool_string(ctx, param, value):
    """
    Parse string boolean values for click options.
    Handles "true", "false", "1", "0", True, False, 1, 0.
    """
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ('true', '1', 'yes')
    return bool(value)


def _validate_no_deprecated_options(ctx, param, value):
    """
    Callback to catch deprecated option usage and provide helpful migration message.

    This prevents users from using removed single-provider options and directs them
    to the new per-provider configuration system.
    """
    if value is not None:
        # Map deprecated options to their replacements
        deprecated_map = {
            'base_url': '--cluster-base-url, --main-base-url, --fallback-base-url',
            'api_path': 'Removed (no longer needed - use base URLs only)',
            'api_version': '--cluster-api-version, --main-api-version, --fallback-api-version',
            'max_token_field': '--cluster-max-token-field, --main-max-token-field, --fallback-max-token-field',
            'max_tokens': '--cluster-max-tokens, --main-max-tokens, --fallback-max-tokens'
        }

        if param.name in deprecated_map:
            replacement = deprecated_map[param.name]
            raise click.UsageError(
                f"\n{'='*70}\n"
                f"ERROR: The option '--{param.name.replace('_', '-')}' is DEPRECATED and has been removed.\n\n"
                f"CodeWiki now uses per-provider LLM configuration to support different models\n"
                f"for clustering, main generation, and fallback.\n\n"
                f"Use instead: {replacement}\n\n"
                f"Example migration:\n"
                f"  OLD: codewiki config set --base-url https://api.anthropic.com/v1 \\\n"
                f"                           --max-tokens 128000\n\n"
                f"  NEW: codewiki config set --cluster-base-url https://api.anthropic.com/v1 \\\n"
                f"                           --main-base-url https://api.anthropic.com/v1 \\\n"
                f"                           --cluster-max-tokens 128000 \\\n"
                f"                           --main-max-tokens 128000\n\n"
                f"See migration guide: https://github.com/flamingo-stack/CodeWiki#migration\n"
                f"{'='*70}\n"
            )
    return value


@click.group(name="config")
def config_group():
    """Manage CodeWiki configuration (API credentials and settings)."""
    pass


@config_group.command(name="set")
# Hidden deprecated options - catch usage and show helpful error
@click.option(
    '--base-url',
    hidden=True,
    callback=_validate_no_deprecated_options,
    expose_value=False,
    help='DEPRECATED: Use --cluster-base-url, --main-base-url, --fallback-base-url instead'
)
@click.option(
    '--api-path',
    hidden=True,
    callback=_validate_no_deprecated_options,
    expose_value=False,
    help='DEPRECATED: Removed (no longer needed)'
)
@click.option(
    '--api-version',
    hidden=True,
    callback=_validate_no_deprecated_options,
    expose_value=False,
    help='DEPRECATED: Use --cluster-api-version, --main-api-version, --fallback-api-version instead'
)
@click.option(
    '--max-token-field',
    hidden=True,
    callback=_validate_no_deprecated_options,
    expose_value=False,
    help='DEPRECATED: Use --cluster-max-token-field, --main-max-token-field, --fallback-max-token-field instead'
)
@click.option(
    '--max-tokens',
    hidden=True,
    callback=_validate_no_deprecated_options,
    expose_value=False,
    help='DEPRECATED: Use --cluster-max-tokens, --main-max-tokens, --fallback-max-tokens instead'
)
# Active options - Per-provider API keys (NO shared fallback)
@click.option(
    "--cluster-api-key",
    type=str,
    help="API key for cluster model provider (REQUIRED with --cluster-base-url)"
)
@click.option(
    "--main-api-key",
    type=str,
    help="API key for main/generation model provider (REQUIRED with --main-base-url)"
)
@click.option(
    "--fallback-api-key",
    type=str,
    help="API key for fallback model provider (REQUIRED with --fallback-base-url)"
)
@click.option(
    "--main-model",
    type=str,
    help="Primary model for documentation generation"
)
@click.option(
    "--cluster-model",
    type=str,
    help="Model for module clustering (recommend top-tier)"
)
@click.option(
    "--fallback-model",
    type=str,
    help="Fallback model for documentation generation"
)
@click.option(
    "--cluster-max-tokens",
    type=int,
    help="Maximum tokens for cluster model (default: 128000)"
)
@click.option(
    "--main-max-tokens",
    type=int,
    help="Maximum tokens for main/generation model (default: 128000)"
)
@click.option(
    "--fallback-max-tokens",
    type=int,
    help="Maximum tokens for fallback model (default: 64000)"
)
@click.option(
    "--max-token-per-module",
    type=int,
    help="Maximum tokens per module for clustering (default: 36369)"
)
@click.option(
    "--max-token-per-leaf-module",
    type=int,
    help="Maximum tokens per leaf module (default: 16000)"
)
@click.option(
    "--max-depth",
    type=int,
    help="Maximum depth for hierarchical decomposition (default: 2)"
)
@click.option(
    "--cluster-temperature",
    type=float,
    help="Temperature setting for cluster model"
)
@click.option(
    "--main-temperature",
    type=float,
    help="Temperature setting for main/generation model"
)
@click.option(
    "--fallback-temperature",
    type=float,
    help="Temperature setting for fallback model"
)
@click.option(
    "--cluster-temperature-supported",
    callback=parse_bool_string,
    help="Whether cluster model supports custom temperature (true/false)"
)
@click.option(
    "--main-temperature-supported",
    callback=parse_bool_string,
    help="Whether main model supports custom temperature (true/false)"
)
@click.option(
    "--fallback-temperature-supported",
    callback=parse_bool_string,
    help="Whether fallback model supports custom temperature (true/false)"
)
@click.option(
    "--cluster-base-url",
    type=str,
    help="Cluster model API base URL (e.g., https://api.openai.com/v1)"
)
@click.option(
    "--main-base-url",
    type=str,
    help="Main model API base URL (e.g., https://api.openai.com/v1)"
)
@click.option(
    "--fallback-base-url",
    type=str,
    help="Fallback model API base URL (e.g., https://api.anthropic.com/v1)"
)
@click.option(
    "--cluster-api-version",
    type=str,
    help="Cluster model API version (for Anthropic models)"
)
@click.option(
    "--main-api-version",
    type=str,
    help="Main model API version (for Anthropic models)"
)
@click.option(
    "--fallback-api-version",
    type=str,
    help="Fallback model API version (for Anthropic models)"
)
@click.option(
    "--cluster-max-token-field",
    type=str,
    help="Parameter name for cluster model max tokens ('max_tokens' or 'max_completion_tokens')"
)
@click.option(
    "--main-max-token-field",
    type=str,
    help="Parameter name for main model max tokens ('max_tokens' or 'max_completion_tokens')"
)
@click.option(
    "--fallback-max-token-field",
    type=str,
    help="Parameter name for fallback model max tokens ('max_tokens' or 'max_completion_tokens')"
)
def config_set(
    cluster_api_key: Optional[str],
    main_api_key: Optional[str],
    fallback_api_key: Optional[str],
    main_model: Optional[str],
    cluster_model: Optional[str],
    fallback_model: Optional[str],
    cluster_max_tokens: Optional[int],
    main_max_tokens: Optional[int],
    fallback_max_tokens: Optional[int],
    max_token_per_module: Optional[int],
    max_token_per_leaf_module: Optional[int],
    max_depth: Optional[int],
    cluster_temperature: Optional[float],
    main_temperature: Optional[float],
    fallback_temperature: Optional[float],
    cluster_temperature_supported: Optional[bool],
    main_temperature_supported: Optional[bool],
    fallback_temperature_supported: Optional[bool],
    cluster_base_url: Optional[str],
    main_base_url: Optional[str],
    fallback_base_url: Optional[str],
    cluster_api_version: Optional[str],
    main_api_version: Optional[str],
    fallback_api_version: Optional[str],
    cluster_max_token_field: Optional[str],
    main_max_token_field: Optional[str],
    fallback_max_token_field: Optional[str]
):
    """
    Set configuration values for CodeWiki.

    API keys are stored securely in your system keychain:
      • macOS: Keychain Access
      • Windows: Credential Manager
      • Linux: Secret Service (GNOME Keyring, KWallet)

    MIGRATION NOTICE:
    CodeWiki now uses per-provider LLM configuration. If you previously used:
      --base-url      → --cluster-base-url, --main-base-url, --fallback-base-url
      --max-tokens    → --cluster-max-tokens, --main-max-tokens, --fallback-max-tokens
      --api-version   → --cluster-api-version, --main-api-version, --fallback-api-version
      --max-token-field → --cluster-max-token-field, --main-max-token-field, --fallback-max-token-field
      --api-path      → Removed (no longer needed)

    Examples:

    \b
    # Set all configuration with per-provider URLs
    $ codewiki config set --api-key sk-abc123 \\
        --cluster-base-url https://api.anthropic.com/v1 \\
        --main-base-url https://api.anthropic.com/v1 \\
        --fallback-base-url https://api.anthropic.com/v1 \\
        --cluster-model claude-sonnet-4 \\
        --main-model claude-sonnet-4 \\
        --fallback-model glm-4p5

    \b
    # Update only API key
    $ codewiki config set --api-key sk-new-key

    \b
    # Set per-provider max tokens
    $ codewiki config set --cluster-max-tokens 128000 \\
        --main-max-tokens 128000 --fallback-max-tokens 64000

    \b
    # Set all max token settings
    $ codewiki config set --cluster-max-tokens 128000 --main-max-tokens 128000 \\
        --max-token-per-module 40000 --max-token-per-leaf-module 20000

    \b
    # Set max depth for hierarchical decomposition
    $ codewiki config set --max-depth 3
    """
    try:
        # Check for old config file with deprecated structure
        from pathlib import Path
        config_path = Path.home() / '.codewiki' / 'config.json'
        if config_path.exists():
            try:
                with open(config_path) as f:
                    old_config = json.load(f)
                    deprecated_fields = []
                    if 'base_url' in old_config:
                        deprecated_fields.append('base_url')
                    if 'api_path' in old_config:
                        deprecated_fields.append('api_path')
                    if 'api_version' in old_config:
                        deprecated_fields.append('api_version')
                    if 'max_token_field' in old_config:
                        deprecated_fields.append('max_token_field')
                    if 'max_tokens' in old_config:
                        deprecated_fields.append('max_tokens')

                    if deprecated_fields:
                        click.echo()
                        click.secho("⚠️  WARNING: Your config file contains deprecated fields:", fg='yellow', bold=True)
                        for field in deprecated_fields:
                            click.secho(f"   • {field}", fg='yellow')
                        click.echo()
                        click.secho("   Please update to per-provider configuration.", fg='yellow')
                        click.secho("   The old fields will be ignored by CodeWiki.", fg='yellow')
                        click.echo()
                        click.secho("   Quick fix: Delete ~/.codewiki/config.json and run:", fg='cyan')
                        click.secho("   $ codewiki config set --api-key <key> --cluster-base-url <url> \\", fg='cyan')
                        click.secho("                         --main-base-url <url> --cluster-model <model> \\", fg='cyan')
                        click.secho("                         --main-model <model> --fallback-model <model>", fg='cyan')
                        click.echo()
            except (json.JSONDecodeError, IOError):
                pass  # Ignore if can't read config file

        # Check if at least one option is provided
        if not any([cluster_api_key, main_api_key, fallback_api_key,
                    main_model, cluster_model, fallback_model,
                    cluster_max_tokens, main_max_tokens, fallback_max_tokens,
                    max_token_per_module, max_token_per_leaf_module, max_depth,
                    cluster_temperature is not None, main_temperature is not None, fallback_temperature is not None,
                    cluster_temperature_supported is not None, main_temperature_supported is not None, fallback_temperature_supported is not None,
                    cluster_base_url, main_base_url, fallback_base_url,
                    cluster_api_version, main_api_version, fallback_api_version,
                    cluster_max_token_field, main_max_token_field, fallback_max_token_field]):
            click.echo("No options provided. Use --help for usage information.")
            sys.exit(EXIT_CONFIG_ERROR)
        
        # Validate inputs before saving
        validated_data = {}

        if cluster_api_key:
            validated_data['cluster_api_key'] = validate_api_key(cluster_api_key)

        if main_api_key:
            validated_data['main_api_key'] = validate_api_key(main_api_key)

        if fallback_api_key:
            validated_data['fallback_api_key'] = validate_api_key(fallback_api_key)

        if main_model:
            validated_data['main_model'] = validate_model_name(main_model)
        
        if cluster_model:
            validated_data['cluster_model'] = validate_model_name(cluster_model)
        
        if fallback_model:
            validated_data['fallback_model'] = validate_model_name(fallback_model)
        
        if cluster_max_tokens is not None:
            if cluster_max_tokens < 1:
                raise ConfigurationError("cluster_max_tokens must be a positive integer")
            validated_data['cluster_max_tokens'] = cluster_max_tokens

        if main_max_tokens is not None:
            if main_max_tokens < 1:
                raise ConfigurationError("main_max_tokens must be a positive integer")
            validated_data['main_max_tokens'] = main_max_tokens

        if fallback_max_tokens is not None:
            if fallback_max_tokens < 1:
                raise ConfigurationError("fallback_max_tokens must be a positive integer")
            validated_data['fallback_max_tokens'] = fallback_max_tokens
        
        if max_token_per_module is not None:
            if max_token_per_module < 1:
                raise ConfigurationError("max_token_per_module must be a positive integer")
            validated_data['max_token_per_module'] = max_token_per_module
        
        if max_token_per_leaf_module is not None:
            if max_token_per_leaf_module < 1:
                raise ConfigurationError("max_token_per_leaf_module must be a positive integer")
            validated_data['max_token_per_leaf_module'] = max_token_per_leaf_module
        
        if max_depth is not None:
            if max_depth < 1:
                raise ConfigurationError("max_depth must be a positive integer")
            validated_data['max_depth'] = max_depth

        if cluster_temperature is not None:
            if cluster_temperature < 0.0 or cluster_temperature > 2.0:
                raise ConfigurationError("cluster_temperature must be between 0.0 and 2.0")
            validated_data['cluster_temperature'] = cluster_temperature

        if main_temperature is not None:
            if main_temperature < 0.0 or main_temperature > 2.0:
                raise ConfigurationError("main_temperature must be between 0.0 and 2.0")
            validated_data['main_temperature'] = main_temperature

        if fallback_temperature is not None:
            if fallback_temperature < 0.0 or fallback_temperature > 2.0:
                raise ConfigurationError("fallback_temperature must be between 0.0 and 2.0")
            validated_data['fallback_temperature'] = fallback_temperature

        if cluster_temperature_supported is not None:
            validated_data['cluster_temperature_supported'] = cluster_temperature_supported

        if main_temperature_supported is not None:
            validated_data['main_temperature_supported'] = main_temperature_supported

        if fallback_temperature_supported is not None:
            validated_data['fallback_temperature_supported'] = fallback_temperature_supported

        # Per-provider base_url validation
        if cluster_base_url:
            validated_data['cluster_base_url'] = validate_url(cluster_base_url)

        if main_base_url:
            validated_data['main_base_url'] = validate_url(main_base_url)

        if fallback_base_url:
            validated_data['fallback_base_url'] = validate_url(fallback_base_url)

        # Per-provider api_version (no validation needed - optional string)
        if cluster_api_version is not None:
            validated_data['cluster_api_version'] = cluster_api_version

        if main_api_version is not None:
            validated_data['main_api_version'] = main_api_version

        if fallback_api_version is not None:
            validated_data['fallback_api_version'] = fallback_api_version

        # Per-provider max_token_field validation
        if cluster_max_token_field is not None:
            if cluster_max_token_field not in ['max_tokens', 'max_completion_tokens']:
                raise ConfigurationError("cluster_max_token_field must be 'max_tokens' or 'max_completion_tokens'")
            validated_data['cluster_max_token_field'] = cluster_max_token_field

        if main_max_token_field is not None:
            if main_max_token_field not in ['max_tokens', 'max_completion_tokens']:
                raise ConfigurationError("main_max_token_field must be 'max_tokens' or 'max_completion_tokens'")
            validated_data['main_max_token_field'] = main_max_token_field

        if fallback_max_token_field is not None:
            if fallback_max_token_field not in ['max_tokens', 'max_completion_tokens']:
                raise ConfigurationError("fallback_max_token_field must be 'max_tokens' or 'max_completion_tokens'")
            validated_data['fallback_max_token_field'] = fallback_max_token_field

        # FAIL-FAST VALIDATION: Require per-provider API keys when per-provider base URLs are set
        # Load existing config to check combined state
        manager = ConfigManager()
        manager.load()
        existing_config = manager.get_config()

        # Determine final state after this update
        final_cluster_base_url = validated_data.get('cluster_base_url') or (existing_config.cluster_base_url if existing_config else None)
        final_main_base_url = validated_data.get('main_base_url') or (existing_config.main_base_url if existing_config else None)
        final_fallback_base_url = validated_data.get('fallback_base_url') or (existing_config.fallback_base_url if existing_config else None)

        final_cluster_api_key = validated_data.get('cluster_api_key') or (existing_config.cluster_api_key if existing_config else None)
        final_main_api_key = validated_data.get('main_api_key') or (existing_config.main_api_key if existing_config else None)
        final_fallback_api_key = validated_data.get('fallback_api_key') or (existing_config.fallback_api_key if existing_config else None)

        # Fail-fast checks
        if final_cluster_base_url and not final_cluster_api_key:
            raise ConfigurationError(
                "cluster_api_key is REQUIRED when cluster_base_url is set.\n"
                "Different providers require different API keys.\n"
                "Use: --cluster-api-key <key>"
            )

        if final_main_base_url and not final_main_api_key:
            raise ConfigurationError(
                "main_api_key is REQUIRED when main_base_url is set.\n"
                "Different providers require different API keys.\n"
                "Use: --main-api-key <key>"
            )

        if final_fallback_base_url and not final_fallback_api_key:
            raise ConfigurationError(
                "fallback_api_key is REQUIRED when fallback_base_url is set.\n"
                "Different providers require different API keys.\n"
                "Use: --fallback-api-key <key>"
            )

        # Save configuration with per-provider API keys
        manager.save(
            cluster_api_key=validated_data.get('cluster_api_key'),
            main_api_key=validated_data.get('main_api_key'),
            fallback_api_key=validated_data.get('fallback_api_key'),
            main_model=validated_data.get('main_model'),
            cluster_model=validated_data.get('cluster_model'),
            fallback_model=validated_data.get('fallback_model'),
            cluster_base_url=validated_data.get('cluster_base_url'),
            main_base_url=validated_data.get('main_base_url'),
            fallback_base_url=validated_data.get('fallback_base_url'),
            cluster_api_version=validated_data.get('cluster_api_version'),
            main_api_version=validated_data.get('main_api_version'),
            fallback_api_version=validated_data.get('fallback_api_version'),
            cluster_max_tokens=validated_data.get('cluster_max_tokens'),
            main_max_tokens=validated_data.get('main_max_tokens'),
            fallback_max_tokens=validated_data.get('fallback_max_tokens'),
            max_token_per_module=validated_data.get('max_token_per_module'),
            max_token_per_leaf_module=validated_data.get('max_token_per_leaf_module'),
            max_depth=validated_data.get('max_depth'),
            cluster_temperature=validated_data.get('cluster_temperature'),
            main_temperature=validated_data.get('main_temperature'),
            fallback_temperature=validated_data.get('fallback_temperature'),
            cluster_temperature_supported=validated_data.get('cluster_temperature_supported'),
            main_temperature_supported=validated_data.get('main_temperature_supported'),
            fallback_temperature_supported=validated_data.get('fallback_temperature_supported'),
            cluster_max_token_field=validated_data.get('cluster_max_token_field'),
            main_max_token_field=validated_data.get('main_max_token_field'),
            fallback_max_token_field=validated_data.get('fallback_max_token_field')
        )
        
        # Display success messages
        click.echo()
        if cluster_api_key:
            if manager.keyring_available:
                click.secho("✓ Cluster API key saved to system keychain", fg="green")
            else:
                click.secho("⚠️  Cluster API key stored in encrypted file.", fg="yellow")

        if main_api_key:
            if manager.keyring_available:
                click.secho("✓ Main API key saved to system keychain", fg="green")
            else:
                click.secho("⚠️  Main API key stored in encrypted file.", fg="yellow")

        if fallback_api_key:
            if manager.keyring_available:
                click.secho("✓ Fallback API key saved to system keychain", fg="green")
            else:
                click.secho("⚠️  Fallback API key stored in encrypted file.", fg="yellow")

        if cluster_base_url:
            click.secho(f"✓ Cluster base URL: {cluster_base_url}", fg="green")

        if main_base_url:
            click.secho(f"✓ Main base URL: {main_base_url}", fg="green")

        if fallback_base_url:
            click.secho(f"✓ Fallback base URL: {fallback_base_url}", fg="green")

        if cluster_api_version:
            click.secho(f"✓ Cluster API version: {cluster_api_version}", fg="green")

        if main_api_version:
            click.secho(f"✓ Main API version: {main_api_version}", fg="green")

        if fallback_api_version:
            click.secho(f"✓ Fallback API version: {fallback_api_version}", fg="green")

        if main_model:
            click.secho(f"✓ Main model: {main_model}", fg="green")
        
        if cluster_model:
            click.secho(f"✓ Cluster model: {cluster_model}", fg="green")
            
            # Warn if not using top-tier model for clustering
            if not is_top_tier_model(cluster_model):
                click.secho(
                    "\n⚠️  Cluster model is not a top-tier LLM. "
                    "Documentation quality may be suboptimal.",
                    fg="yellow"
                )
                click.echo(
                    "   Recommended models: claude-opus, claude-sonnet-4, gpt-4, gpt-4-turbo"
                )
        
        if fallback_model:
            click.secho(f"✓ Fallback model: {fallback_model}", fg="green")

        if cluster_max_tokens:
            click.secho(f"✓ Cluster max tokens: {cluster_max_tokens}", fg="green")

        if main_max_tokens:
            click.secho(f"✓ Main max tokens: {main_max_tokens}", fg="green")

        if fallback_max_tokens:
            click.secho(f"✓ Fallback max tokens: {fallback_max_tokens}", fg="green")
        
        if max_token_per_module:
            click.secho(f"✓ Max token per module: {max_token_per_module}", fg="green")
        
        if max_token_per_leaf_module:
            click.secho(f"✓ Max token per leaf module: {max_token_per_leaf_module}", fg="green")
        
        if max_depth:
            click.secho(f"✓ Max depth: {max_depth}", fg="green")

        if cluster_temperature is not None:
            click.secho(f"✓ Cluster temperature: {cluster_temperature}", fg="green")

        if main_temperature is not None:
            click.secho(f"✓ Main temperature: {main_temperature}", fg="green")

        if fallback_temperature is not None:
            click.secho(f"✓ Fallback temperature: {fallback_temperature}", fg="green")

        click.echo("\n" + click.style("Configuration updated successfully.", fg="green", bold=True))
        
    except ConfigurationError as e:
        click.secho(f"\n✗ Configuration error: {e.message}", fg="red", err=True)
        sys.exit(e.exit_code)
    except Exception as e:
        sys.exit(handle_error(e))


@config_group.command(name="show")
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output in JSON format"
)
def config_show(output_json: bool):
    """
    Display current configuration.
    
    API keys are masked for security (showing only first and last 4 characters).
    
    Examples:
    
    \b
    # Display configuration
    $ codewiki config show
    
    \b
    # Display as JSON
    $ codewiki config show --json
    """
    try:
        manager = ConfigManager()
        
        if not manager.load():
            click.secho("\n✗ Configuration not found.", fg="red", err=True)
            click.echo("\nPlease run 'codewiki config set' to configure your API credentials:")
            click.echo("  codewiki config set --api-key <key> --base-url <url> \\")
            click.echo("    --main-model <model> --cluster-model <model> --fallback-model <model>")
            click.echo("\nFor more help: codewiki config set --help")
            sys.exit(EXIT_CONFIG_ERROR)
        
        config = manager.get_config()
        api_key = manager.get_api_key()
        
        if output_json:
            # JSON output
            output = {
                "api_key": mask_api_key(api_key) if api_key else "Not set",
                "api_key_storage": "keychain" if manager.keyring_available else "encrypted_file",
                "base_url": config.base_url if config else "",
                "main_model": config.main_model if config else "",
                "cluster_model": config.cluster_model if config else "",
                "fallback_model": config.fallback_model if config else "glm-4p5",
                "default_output": config.default_output if config else "docs",
                "cluster_max_tokens": config.cluster_max_tokens if config else 128000,
                "main_max_tokens": config.main_max_tokens if config else 128000,
                "fallback_max_tokens": config.fallback_max_tokens if config else 64000,
                "cluster_temperature": config.cluster_temperature if config else 0.0,
                "main_temperature": config.main_temperature if config else 0.0,
                "fallback_temperature": config.fallback_temperature if config else 0.0,
                "cluster_temperature_supported": config.cluster_temperature_supported if config else True,
                "main_temperature_supported": config.main_temperature_supported if config else True,
                "fallback_temperature_supported": config.fallback_temperature_supported if config else True,
                "max_token_per_module": config.max_token_per_module if config else 36369,
                "max_token_per_leaf_module": config.max_token_per_leaf_module if config else 16000,
                "max_depth": config.max_depth if config else 2,
                "agent_instructions": config.agent_instructions.to_dict() if config and config.agent_instructions else {},
                "config_file": str(manager.config_file_path)
            }
            click.echo(json.dumps(output, indent=2))
        else:
            # Human-readable output
            click.echo()
            click.secho("CodeWiki Configuration", fg="blue", bold=True)
            click.echo("━" * 40)
            click.echo()
            
            click.secho("Credentials", fg="cyan", bold=True)
            if api_key:
                storage = "system keychain" if manager.keyring_available else "encrypted file"
                click.echo(f"  API Key:          {mask_api_key(api_key)} (in {storage})")
            else:
                click.secho("  API Key:          Not set", fg="yellow")
            
            click.echo()
            click.secho("API Settings", fg="cyan", bold=True)
            if config:
                click.echo(f"  Base URL:         {config.base_url or 'Not set'}")
                click.echo(f"  Main Model:       {config.main_model or 'Not set'}")
                click.echo(f"  Cluster Model:    {config.cluster_model or 'Not set'}")
                click.echo(f"  Fallback Model:   {config.fallback_model or 'Not set'}")
            else:
                click.secho("  Not configured", fg="yellow")
            
            click.echo()
            click.secho("Output Settings", fg="cyan", bold=True)
            if config:
                click.echo(f"  Default Output:   {config.default_output}")
            
            click.echo()
            click.secho("Token Settings", fg="cyan", bold=True)
            if config:
                click.echo(f"  Cluster Max Tokens:      {config.cluster_max_tokens}")
                click.echo(f"  Main Max Tokens:         {config.main_max_tokens}")
                click.echo(f"  Fallback Max Tokens:     {config.fallback_max_tokens}")
                click.echo(f"  Max Token/Module:        {config.max_token_per_module}")
                click.echo(f"  Max Token/Leaf Module:   {config.max_token_per_leaf_module}")

            click.echo()
            click.secho("Temperature Settings", fg="cyan", bold=True)
            if config:
                click.echo(f"  Cluster Temperature:     {config.cluster_temperature} (supported: {config.cluster_temperature_supported})")
                click.echo(f"  Main Temperature:        {config.main_temperature} (supported: {config.main_temperature_supported})")
                click.echo(f"  Fallback Temperature:    {config.fallback_temperature} (supported: {config.fallback_temperature_supported})")

            click.echo()
            click.secho("Decomposition Settings", fg="cyan", bold=True)
            if config:
                click.echo(f"  Max Depth:               {config.max_depth}")
            
            click.echo()
            click.secho("Agent Instructions", fg="cyan", bold=True)
            if config and config.agent_instructions and not config.agent_instructions.is_empty():
                agent = config.agent_instructions
                if agent.include_patterns:
                    click.echo(f"  Include patterns:   {', '.join(agent.include_patterns)}")
                if agent.exclude_patterns:
                    click.echo(f"  Exclude patterns:   {', '.join(agent.exclude_patterns)}")
                if agent.focus_modules:
                    click.echo(f"  Focus modules:      {', '.join(agent.focus_modules)}")
                if agent.doc_type:
                    click.echo(f"  Doc type:           {agent.doc_type}")
                if agent.custom_instructions:
                    click.echo(f"  Custom instructions: {agent.custom_instructions[:50]}...")
            else:
                click.secho("  Using defaults (no custom settings)", fg="yellow")
            
            click.echo()
            click.echo(f"Configuration file: {manager.config_file_path}")
            click.echo()
        
    except Exception as e:
        sys.exit(handle_error(e))


@config_group.command(name="validate")
@click.option(
    "--quick",
    is_flag=True,
    help="Skip API connectivity test"
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show detailed validation steps"
)
def config_validate(quick: bool, verbose: bool):
    """
    Validate configuration and test LLM API connectivity.
    
    Checks:
      • Configuration file exists and is valid
      • API key is present
      • API settings are correctly formatted
      • (Optional) API connectivity test
    
    Examples:
    
    \b
    # Full validation with API test
    $ codewiki config validate
    
    \b
    # Quick validation (config only)
    $ codewiki config validate --quick
    
    \b
    # Verbose output
    $ codewiki config validate --verbose
    """
    try:
        click.echo()
        click.secho("Validating configuration...", fg="blue", bold=True)
        click.echo()
        
        manager = ConfigManager()
        
        # Step 1: Check config file
        if verbose:
            click.echo("[1/5] Checking configuration file...")
            click.echo(f"      Path: {manager.config_file_path}")
        
        if not manager.load():
            click.secho("✗ Configuration file not found", fg="red")
            click.echo()
            click.echo("Error: Configuration is incomplete. Run 'codewiki config set --help' for setup instructions.")
            sys.exit(EXIT_CONFIG_ERROR)
        
        if verbose:
            click.secho("      ✓ File exists", fg="green")
            click.secho("      ✓ Valid JSON format", fg="green")
        else:
            click.secho("✓ Configuration file exists", fg="green")
        
        # Step 2: Check API key
        if verbose:
            click.echo()
            click.echo("[2/5] Checking API key...")
            storage = "system keychain" if manager.keyring_available else "encrypted file"
            click.echo(f"      Storage: {storage}")
        
        api_key = manager.get_api_key()
        if not api_key:
            click.secho("✗ API key missing", fg="red")
            click.echo()
            click.echo("Error: API key not set. Run 'codewiki config set --api-key <key>'")
            sys.exit(EXIT_CONFIG_ERROR)
        
        if verbose:
            click.secho(f"      ✓ API key retrieved", fg="green")
            click.secho(f"      ✓ Length: {len(api_key)} characters", fg="green")
        else:
            click.secho("✓ API key present (stored in keychain)", fg="green")
        
        # Step 3: Check base URL
        config = manager.get_config()
        if verbose:
            click.echo()
            click.echo("[3/5] Checking base URL...")
            click.echo(f"      URL: {config.base_url}")
        
        if not config.base_url:
            click.secho("✗ Base URL not set", fg="red")
            sys.exit(EXIT_CONFIG_ERROR)
        
        try:
            validate_url(config.base_url)
            if verbose:
                click.secho("      ✓ Valid HTTPS URL", fg="green")
            else:
                click.secho(f"✓ Base URL valid: {config.base_url}", fg="green")
        except ConfigurationError as e:
            click.secho(f"✗ Invalid base URL: {e.message}", fg="red")
            sys.exit(EXIT_CONFIG_ERROR)
        
        # Step 4: Check models
        if verbose:
            click.echo()
            click.echo("[4/5] Checking model configuration...")
            click.echo(f"      Main model: {config.main_model}")
            click.echo(f"      Cluster model: {config.cluster_model}")
            click.echo(f"      Fallback model: {config.fallback_model}")
        
        if not config.main_model or not config.cluster_model or not config.fallback_model:
            click.secho("✗ Models not configured", fg="red")
            sys.exit(EXIT_CONFIG_ERROR)
        
        if verbose:
            click.secho("      ✓ Models configured", fg="green")
        else:
            click.secho(f"✓ Main model configured: {config.main_model}", fg="green")
            click.secho(f"✓ Cluster model configured: {config.cluster_model}", fg="green")
            click.secho(f"✓ Fallback model configured: {config.fallback_model}", fg="green")
        
        # Warn about non-top-tier cluster model
        if not is_top_tier_model(config.cluster_model):
            click.secho(
                "⚠️  Cluster model is not top-tier. Consider using claude-sonnet-4 or gpt-4.",
                fg="yellow"
            )
        
        # Step 5: API connectivity test (unless --quick)
        if not quick:
            try:
                base_url_lower = config.base_url.lower()

                # Determine provider from base URL
                if "anthropic.com" in base_url_lower:
                    # Anthropic API - use Anthropic client
                    if verbose:
                        click.echo("[5/5] Testing Anthropic API connectivity...")
                    from anthropic import Anthropic
                    client = Anthropic(api_key=api_key)
                    # Make a minimal messages call to verify API key
                    response = client.messages.create(
                        model=config.main_model,
                        max_tokens=1,
                        messages=[{"role": "user", "content": "test"}]
                    )
                elif "openai.com" in base_url_lower or "api.openai" in base_url_lower:
                    # OpenAI API - use OpenAI client
                    if verbose:
                        click.echo("[5/5] Testing OpenAI API connectivity...")
                    from openai import OpenAI
                    client = OpenAI(api_key=api_key, base_url=config.base_url)
                    response = client.models.list()
                else:
                    # Generic OpenAI-compatible API (LiteLLM, vLLM, etc.)
                    if verbose:
                        click.echo("[5/5] Testing OpenAI-compatible API connectivity...")
                    from openai import OpenAI
                    client = OpenAI(api_key=api_key, base_url=config.base_url)
                    response = client.models.list()

                click.secho("✓ API connectivity test successful", fg="green")
            except Exception as e:
                if verbose:
                    click.secho(f"✗ API connectivity test failed: {e}", fg="red")
                else:
                    click.secho("✗ API connectivity test failed", fg="red")
                sys.exit(EXIT_CONFIG_ERROR)
        
        # Success
        click.echo()
        click.secho("✓ Configuration is valid!", fg="green", bold=True)
        click.echo()
        
    except ConfigurationError as e:
        click.secho(f"\n✗ Configuration error: {e.message}", fg="red", err=True)
        sys.exit(e.exit_code)
    except Exception as e:
        sys.exit(handle_error(e, verbose=verbose))


@config_group.command(name="agent")
@click.option(
    "--include",
    "-i",
    type=str,
    default=None,
    help="Comma-separated file patterns to include (e.g., '*.cs,*.py')",
)
@click.option(
    "--exclude",
    "-e",
    type=str,
    default=None,
    help="Comma-separated patterns to exclude (e.g., '*Tests*,*Specs*')",
)
@click.option(
    "--focus",
    "-f",
    type=str,
    default=None,
    help="Comma-separated modules/paths to focus on (e.g., 'src/core,src/api')",
)
@click.option(
    "--doc-type",
    "-t",
    type=click.Choice(['api', 'architecture', 'user-guide', 'developer'], case_sensitive=False),
    default=None,
    help="Default type of documentation to generate",
)
@click.option(
    "--instructions",
    type=str,
    default=None,
    help="Custom instructions for the documentation agent",
)
@click.option(
    "--clear",
    is_flag=True,
    help="Clear all agent instructions",
)
def config_agent(
    include: Optional[str],
    exclude: Optional[str],
    focus: Optional[str],
    doc_type: Optional[str],
    instructions: Optional[str],
    clear: bool
):
    """
    Configure default agent instructions for documentation generation.
    
    These settings are used as defaults when running 'codewiki generate'.
    Runtime options (--include, --exclude, etc.) override these defaults.
    
    Examples:
    
    \b
    # Set include patterns for C# projects
    $ codewiki config agent --include "*.cs"
    
    \b
    # Exclude test projects
    $ codewiki config agent --exclude "*Tests*,*Specs*,test_*"
    
    \b
    # Focus on specific modules
    $ codewiki config agent --focus "src/core,src/api"
    
    \b
    # Set default doc type
    $ codewiki config agent --doc-type architecture
    
    \b
    # Add custom instructions
    $ codewiki config agent --instructions "Focus on public APIs and include usage examples"
    
    \b
    # Clear all agent instructions
    $ codewiki config agent --clear
    """
    try:
        manager = ConfigManager()
        
        if not manager.load():
            click.secho("\n✗ Configuration not found.", fg="red", err=True)
            click.echo("\nPlease run 'codewiki config set' first to configure your API credentials.")
            sys.exit(EXIT_CONFIG_ERROR)
        
        config = manager.get_config()
        
        if clear:
            # Clear all agent instructions
            config.agent_instructions = AgentInstructions()
            manager.save()
            click.echo()
            click.secho("✓ Agent instructions cleared", fg="green")
            click.echo()
            return
        
        # Check if at least one option is provided
        if not any([include, exclude, focus, doc_type, instructions]):
            # Display current settings
            click.echo()
            click.secho("Agent Instructions", fg="blue", bold=True)
            click.echo("━" * 40)
            click.echo()
            
            agent = config.agent_instructions
            if agent and not agent.is_empty():
                if agent.include_patterns:
                    click.echo(f"  Include patterns:   {', '.join(agent.include_patterns)}")
                if agent.exclude_patterns:
                    click.echo(f"  Exclude patterns:   {', '.join(agent.exclude_patterns)}")
                if agent.focus_modules:
                    click.echo(f"  Focus modules:      {', '.join(agent.focus_modules)}")
                if agent.doc_type:
                    click.echo(f"  Doc type:           {agent.doc_type}")
                if agent.custom_instructions:
                    click.echo(f"  Custom instructions: {agent.custom_instructions}")
            else:
                click.secho("  No agent instructions configured (using defaults)", fg="yellow")
            
            click.echo()
            click.echo("Use 'codewiki config agent --help' for usage information.")
            click.echo()
            return
        
        # Update agent instructions
        current = config.agent_instructions or AgentInstructions()
        
        if include is not None:
            current.include_patterns = parse_patterns(include) if include else None
        if exclude is not None:
            current.exclude_patterns = parse_patterns(exclude) if exclude else None
        if focus is not None:
            current.focus_modules = parse_patterns(focus) if focus else None
        if doc_type is not None:
            current.doc_type = doc_type if doc_type else None
        if instructions is not None:
            current.custom_instructions = instructions if instructions else None
        
        config.agent_instructions = current
        manager.save()
        
        # Display success messages
        click.echo()
        if include:
            click.secho(f"✓ Include patterns: {parse_patterns(include)}", fg="green")
        if exclude:
            click.secho(f"✓ Exclude patterns: {parse_patterns(exclude)}", fg="green")
        if focus:
            click.secho(f"✓ Focus modules: {parse_patterns(focus)}", fg="green")
        if doc_type:
            click.secho(f"✓ Doc type: {doc_type}", fg="green")
        if instructions:
            click.secho(f"✓ Custom instructions set", fg="green")
        
        click.echo("\n" + click.style("Agent instructions updated successfully.", fg="green", bold=True))
        click.echo()
        
    except ConfigurationError as e:
        click.secho(f"\n✗ Configuration error: {e.message}", fg="red", err=True)
        sys.exit(e.exit_code)
    except Exception as e:
        sys.exit(handle_error(e))

