"""
Configuration manager with keyring integration for secure credential storage.
"""

import json
from pathlib import Path
from typing import Optional
import keyring
from keyring.errors import KeyringError

from codewiki.cli.models.config import Configuration
from codewiki.cli.utils.errors import ConfigurationError, FileSystemError
from codewiki.cli.utils.fs import ensure_directory, safe_write, safe_read


# Keyring configuration
KEYRING_SERVICE = "codewiki"
KEYRING_API_KEY_ACCOUNT = "api_key"

# Configuration file location
CONFIG_DIR = Path.home() / ".codewiki"
CONFIG_FILE = CONFIG_DIR / "config.json"
CONFIG_VERSION = "1.0"


class ConfigManager:
    """
    Manages CodeWiki configuration with secure keyring storage for API keys.
    
    Storage:
        - API key: System keychain via keyring (macOS Keychain, Windows Credential Manager, 
                  Linux Secret Service)
        - Other settings: ~/.codewiki/config.json
    """
    
    def __init__(self):
        """Initialize the configuration manager."""
        self._api_key: Optional[str] = None
        self._config: Optional[Configuration] = None
        self._keyring_available = self._check_keyring_available()
    
    def _check_keyring_available(self) -> bool:
        """Check if system keyring is available."""
        try:
            # Try to get/set a test value
            keyring.get_password(KEYRING_SERVICE, "__test__")
            return True
        except KeyringError:
            return False
    
    def load(self) -> bool:
        """
        Load configuration from file and keyring.
        
        Returns:
            True if configuration exists, False otherwise
        """
        # Load from JSON file
        if not CONFIG_FILE.exists():
            return False
        
        try:
            content = safe_read(CONFIG_FILE)
            data = json.loads(content)
            
            # Validate version
            if data.get('version') != CONFIG_VERSION:
                # Could implement migration here
                pass
            
            self._config = Configuration.from_dict(data)
            
            # Load API key from keyring
            try:
                self._api_key = keyring.get_password(KEYRING_SERVICE, KEYRING_API_KEY_ACCOUNT)
            except KeyringError:
                # Keyring unavailable, API key will be None
                pass
            
            return True
        except (json.JSONDecodeError, FileSystemError) as e:
            raise ConfigurationError(f"Failed to load configuration: {e}")
    
    def save(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        main_model: Optional[str] = None,
        cluster_model: Optional[str] = None,
        fallback_model: Optional[str] = None,
        default_output: Optional[str] = None,
        cluster_max_tokens: Optional[int] = None,
        main_max_tokens: Optional[int] = None,
        fallback_max_tokens: Optional[int] = None,
        max_token_per_module: Optional[int] = None,
        max_token_per_leaf_module: Optional[int] = None,
        max_depth: Optional[int] = None,
        cluster_temperature: Optional[float] = None,
        main_temperature: Optional[float] = None,
        fallback_temperature: Optional[float] = None,
        cluster_temperature_supported: Optional[bool] = None,
        main_temperature_supported: Optional[bool] = None,
        fallback_temperature_supported: Optional[bool] = None,
        max_token_field: Optional[str] = None,
        api_path: Optional[str] = None,
        api_version: Optional[str] = None
    ):
        """
        Save configuration to file and keyring.

        Args:
            api_key: API key (stored in keyring)
            base_url: LLM API base URL
            main_model: Primary model
            cluster_model: Clustering model
            fallback_model: Fallback model
            default_output: Default output directory
            cluster_max_tokens: Maximum tokens for cluster model
            main_max_tokens: Maximum tokens for main/generation model
            fallback_max_tokens: Maximum tokens for fallback model
            max_token_per_module: Maximum tokens per module for clustering
            max_token_per_leaf_module: Maximum tokens per leaf module
            max_depth: Maximum depth for hierarchical decomposition
            cluster_temperature: Temperature for cluster model
            main_temperature: Temperature for main/generation model
            fallback_temperature: Temperature for fallback model
            cluster_temperature_supported: Whether cluster model supports custom temperature
            main_temperature_supported: Whether main model supports custom temperature
            fallback_temperature_supported: Whether fallback model supports custom temperature
            max_token_field: Parameter name for max tokens ('max_tokens' or 'max_completion_tokens')
            api_path: API endpoint path (e.g., '/v1/chat/completions' or '/v1/messages')
            api_version: API version if different from default
        """
        # Ensure config directory exists
        try:
            ensure_directory(CONFIG_DIR)
        except FileSystemError as e:
            raise ConfigurationError(f"Cannot create config directory: {e}")
        
        # Load existing config or create new
        if self._config is None:
            if CONFIG_FILE.exists():
                self.load()
            else:
                from codewiki.cli.models.config import AgentInstructions
                self._config = Configuration(
                    base_url="",
                    main_model="",
                    cluster_model="",
                    fallback_model="glm-4p5",
                    default_output="docs",
                    agent_instructions=AgentInstructions()
                )
        
        # Update fields if provided
        if base_url is not None:
            self._config.base_url = base_url
        if main_model is not None:
            self._config.main_model = main_model
        if cluster_model is not None:
            self._config.cluster_model = cluster_model
        if fallback_model is not None:
            self._config.fallback_model = fallback_model
        if default_output is not None:
            self._config.default_output = default_output
        if cluster_max_tokens is not None:
            self._config.cluster_max_tokens = cluster_max_tokens
        if main_max_tokens is not None:
            self._config.main_max_tokens = main_max_tokens
        if fallback_max_tokens is not None:
            self._config.fallback_max_tokens = fallback_max_tokens
        if max_token_per_module is not None:
            self._config.max_token_per_module = max_token_per_module
        if max_token_per_leaf_module is not None:
            self._config.max_token_per_leaf_module = max_token_per_leaf_module
        if max_depth is not None:
            self._config.max_depth = max_depth
        if cluster_temperature is not None:
            self._config.cluster_temperature = cluster_temperature
        if main_temperature is not None:
            self._config.main_temperature = main_temperature
        if fallback_temperature is not None:
            self._config.fallback_temperature = fallback_temperature
        if cluster_temperature_supported is not None:
            self._config.cluster_temperature_supported = cluster_temperature_supported
        if main_temperature_supported is not None:
            self._config.main_temperature_supported = main_temperature_supported
        if fallback_temperature_supported is not None:
            self._config.fallback_temperature_supported = fallback_temperature_supported
        if max_token_field is not None:
            self._config.max_token_field = max_token_field
        if api_path is not None:
            self._config.api_path = api_path
        if api_version is not None:
            self._config.api_version = api_version

        # Validate configuration (only if base fields are set)
        if self._config.base_url and self._config.main_model and self._config.cluster_model:
            self._config.validate()
        
        # Save API key to keyring
        if api_key is not None:
            self._api_key = api_key
            try:
                keyring.set_password(KEYRING_SERVICE, KEYRING_API_KEY_ACCOUNT, api_key)
            except KeyringError as e:
                # Fallback: warn about keyring unavailability
                raise ConfigurationError(
                    f"System keychain unavailable: {e}\n"
                    f"Please ensure your system keychain is properly configured."
                )
        
        # Save non-sensitive config to JSON
        config_data = {
            "version": CONFIG_VERSION,
            **self._config.to_dict()
        }
        
        try:
            safe_write(CONFIG_FILE, json.dumps(config_data, indent=2))
        except FileSystemError as e:
            raise ConfigurationError(f"Failed to save configuration: {e}")
    
    def get_api_key(self) -> Optional[str]:
        """
        Get API key from keyring.
        
        Returns:
            API key or None if not set
        """
        if self._api_key is None:
            try:
                self._api_key = keyring.get_password(KEYRING_SERVICE, KEYRING_API_KEY_ACCOUNT)
            except KeyringError:
                pass
        
        return self._api_key
    
    def get_config(self) -> Optional[Configuration]:
        """
        Get current configuration.
        
        Returns:
            Configuration object or None if not loaded
        """
        return self._config
    
    def is_configured(self) -> bool:
        """
        Check if configuration is complete and valid.
        
        Returns:
            True if configured, False otherwise
        """
        if self._config is None:
            return False
        
        # Check if API key is set
        if self.get_api_key() is None:
            return False
        
        # Check if config is complete
        return self._config.is_complete()
    
    def delete_api_key(self):
        """Delete API key from keyring."""
        try:
            keyring.delete_password(KEYRING_SERVICE, KEYRING_API_KEY_ACCOUNT)
            self._api_key = None
        except KeyringError:
            pass
    
    def clear(self):
        """Clear all configuration (file and keyring)."""
        # Delete API key from keyring
        self.delete_api_key()
        
        # Delete config file
        if CONFIG_FILE.exists():
            CONFIG_FILE.unlink()
        
        self._config = None
        self._api_key = None
    
    @property
    def keyring_available(self) -> bool:
        """Check if keyring is available."""
        return self._keyring_available
    
    @property
    def config_file_path(self) -> Path:
        """Get configuration file path."""
        return CONFIG_FILE

