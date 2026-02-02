"""
Configuration data models for CodeWiki CLI.

This module contains the Configuration class which represents persistent
user settings stored in ~/.codewiki/config.json. These settings are converted
to the backend Config class when running documentation generation.
"""

from dataclasses import dataclass, asdict, field
from typing import Optional, List
from pathlib import Path

from codewiki.cli.utils.validation import (
    validate_url,
    validate_api_key,
    validate_model_name,
)


@dataclass
class AgentInstructions:
    """
    Custom instructions for the documentation agent.
    
    Allows users to customize:
    - File filtering (include/exclude patterns)
    - Module focus (prioritize certain modules)
    - Documentation type (API docs, architecture docs, etc.)
    - Custom instructions for the LLM
    
    Attributes:
        include_patterns: File patterns to include (e.g., ["*.cs", "*.py"])
        exclude_patterns: File/directory patterns to exclude (e.g., ["*Tests*", "*test*"])
        focus_modules: Modules to document in more detail
        doc_type: Type of documentation to generate
        custom_instructions: Additional instructions for the documentation agent
    """
    include_patterns: Optional[List[str]] = None  # e.g., ["*.cs"] for C# projects
    exclude_patterns: Optional[List[str]] = None  # e.g., ["*Tests*", "*Specs*"]
    focus_modules: Optional[List[str]] = None  # e.g., ["src/core", "src/api"]
    doc_type: Optional[str] = None  # e.g., "api", "architecture", "user-guide"
    custom_instructions: Optional[str] = None  # Free-form instructions
    
    def to_dict(self) -> dict:
        """Convert to dictionary, excluding None values."""
        result = {}
        if self.include_patterns:
            result['include_patterns'] = self.include_patterns
        if self.exclude_patterns:
            result['exclude_patterns'] = self.exclude_patterns
        if self.focus_modules:
            result['focus_modules'] = self.focus_modules
        if self.doc_type:
            result['doc_type'] = self.doc_type
        if self.custom_instructions:
            result['custom_instructions'] = self.custom_instructions
        return result
    
    @classmethod
    def from_dict(cls, data: dict) -> 'AgentInstructions':
        """Create AgentInstructions from dictionary."""
        return cls(
            include_patterns=data.get('include_patterns'),
            exclude_patterns=data.get('exclude_patterns'),
            focus_modules=data.get('focus_modules'),
            doc_type=data.get('doc_type'),
            custom_instructions=data.get('custom_instructions'),
        )
    
    def is_empty(self) -> bool:
        """Check if all fields are empty/None."""
        return not any([
            self.include_patterns,
            self.exclude_patterns,
            self.focus_modules,
            self.doc_type,
            self.custom_instructions,
        ])
    
    def get_prompt_addition(self) -> str:
        """Generate prompt additions based on instructions."""
        additions = []
        
        if self.doc_type:
            doc_type_instructions = {
                'api': "Focus on API documentation: endpoints, parameters, return types, and usage examples.",
                'architecture': "Focus on architecture documentation: system design, component relationships, and data flow.",
                'user-guide': "Focus on user guide documentation: how to use features, step-by-step tutorials.",
                'developer': "Focus on developer documentation: code structure, contribution guidelines, and implementation details.",
            }
            if self.doc_type.lower() in doc_type_instructions:
                additions.append(doc_type_instructions[self.doc_type.lower()])
            else:
                additions.append(f"Focus on generating {self.doc_type} documentation.")
        
        if self.focus_modules:
            additions.append(f"Pay special attention to and provide more detailed documentation for these modules: {', '.join(self.focus_modules)}")
        
        if self.custom_instructions:
            additions.append(f"Additional instructions: {self.custom_instructions}")
        
        return "\n".join(additions) if additions else ""


@dataclass
class Configuration:
    """
    CodeWiki configuration data model.

    Attributes:
        main_model: Primary model for documentation generation (generation phase)
        cluster_model: Model for module clustering
        fallback_model: Fallback model for documentation generation
        cluster_api_key: API key for cluster model (stored in keyring, runtime only)
        main_api_key: API key for main/generation model (stored in keyring, runtime only)
        fallback_api_key: API key for fallback model (stored in keyring, runtime only)
        default_output: Default output directory
        cluster_base_url: Base URL for cluster model API
        main_base_url: Base URL for main model API
        fallback_base_url: Base URL for fallback model API
        cluster_api_version: API version for cluster model (optional)
        main_api_version: API version for main model (optional)
        fallback_api_version: API version for fallback model (optional)
        cluster_max_tokens: Maximum tokens for cluster model (default: 128000)
        main_max_tokens: Maximum tokens for main/generation model (default: 128000)
        fallback_max_tokens: Maximum tokens for fallback model (default: 64000)
        cluster_temperature: Temperature for cluster model (default: 0.0)
        main_temperature: Temperature for main/generation model (default: 0.0)
        fallback_temperature: Temperature for fallback model (default: 0.0)
        cluster_temperature_supported: Whether cluster model supports temperature (default: True)
        main_temperature_supported: Whether main model supports temperature (default: True)
        fallback_temperature_supported: Whether fallback model supports temperature (default: True)
        cluster_max_token_field: Parameter name for cluster model max tokens (default: "max_tokens")
        main_max_token_field: Parameter name for main model max tokens (default: "max_tokens")
        fallback_max_token_field: Parameter name for fallback model max tokens (default: "max_tokens")
        max_token_per_module: Maximum tokens per module for clustering (default: 36369)
        max_token_per_leaf_module: Maximum tokens per leaf module (default: 16000)
        max_depth: Maximum depth for hierarchical decomposition (default: 2)
        agent_instructions: Custom agent instructions for documentation generation
    """
    main_model: str
    cluster_model: str
    fallback_model: str
    # Runtime API keys (not persisted to config.json, fetched from keyring)
    cluster_api_key: Optional[str] = None
    main_api_key: Optional[str] = None
    fallback_api_key: Optional[str] = None
    default_output: str = "docs"
    cluster_base_url: Optional[str] = None
    main_base_url: Optional[str] = None
    fallback_base_url: Optional[str] = None
    cluster_api_version: Optional[str] = None
    main_api_version: Optional[str] = None
    fallback_api_version: Optional[str] = None
    cluster_max_tokens: int = 128000
    main_max_tokens: int = 128000
    fallback_max_tokens: int = 64000
    cluster_temperature: float = 0.0
    main_temperature: float = 0.0
    fallback_temperature: float = 0.0
    cluster_temperature_supported: bool = True
    main_temperature_supported: bool = True
    fallback_temperature_supported: bool = True
    cluster_max_token_field: str = "max_tokens"
    main_max_token_field: str = "max_tokens"
    fallback_max_token_field: str = "max_tokens"
    max_token_per_module: int = 36369
    max_token_per_leaf_module: int = 16000
    max_depth: int = 2
    agent_instructions: AgentInstructions = field(default_factory=AgentInstructions)
    
    def validate(self):
        """
        Validate all configuration fields.

        Raises:
            ConfigurationError: If validation fails
        """
        # Validate per-provider base_urls if set
        if self.cluster_base_url:
            validate_url(self.cluster_base_url)
        if self.main_base_url:
            validate_url(self.main_base_url)
        if self.fallback_base_url:
            validate_url(self.fallback_base_url)

        # Validate model names
        validate_model_name(self.main_model)
        validate_model_name(self.cluster_model)
        validate_model_name(self.fallback_model)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        result = {
            'main_model': self.main_model,
            'cluster_model': self.cluster_model,
            'fallback_model': self.fallback_model,
            'default_output': self.default_output,
            'cluster_max_tokens': self.cluster_max_tokens,
            'main_max_tokens': self.main_max_tokens,
            'fallback_max_tokens': self.fallback_max_tokens,
            'cluster_temperature': self.cluster_temperature,
            'main_temperature': self.main_temperature,
            'fallback_temperature': self.fallback_temperature,
            'cluster_temperature_supported': self.cluster_temperature_supported,
            'main_temperature_supported': self.main_temperature_supported,
            'fallback_temperature_supported': self.fallback_temperature_supported,
            'cluster_max_token_field': self.cluster_max_token_field,
            'main_max_token_field': self.main_max_token_field,
            'fallback_max_token_field': self.fallback_max_token_field,
            'max_token_per_module': self.max_token_per_module,
            'max_token_per_leaf_module': self.max_token_per_leaf_module,
            'max_depth': self.max_depth,
        }
        # Per-provider base_urls (optional)
        if self.cluster_base_url is not None:
            result['cluster_base_url'] = self.cluster_base_url
        if self.main_base_url is not None:
            result['main_base_url'] = self.main_base_url
        if self.fallback_base_url is not None:
            result['fallback_base_url'] = self.fallback_base_url
        # Per-provider api_versions (optional)
        if self.cluster_api_version is not None:
            result['cluster_api_version'] = self.cluster_api_version
        if self.main_api_version is not None:
            result['main_api_version'] = self.main_api_version
        if self.fallback_api_version is not None:
            result['fallback_api_version'] = self.fallback_api_version
        # Agent instructions (optional)
        if self.agent_instructions and not self.agent_instructions.is_empty():
            result['agent_instructions'] = self.agent_instructions.to_dict()
        return result
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Configuration':
        """
        Create Configuration from dictionary with type coercion.

        Args:
            data: Configuration dictionary (may contain string values from JSON)

        Returns:
            Configuration instance with properly typed fields

        Raises:
            ValueError: If type conversion fails or validation fails
        """
        # Helper function for integer conversion
        def to_int(value, field_name: str, default: int = None):
            if value is None:
                return default
            if isinstance(value, int):
                return value
            if isinstance(value, str):
                try:
                    result = int(value)
                    if result <= 0:
                        raise ValueError(f"{field_name} must be positive, got {result}")
                    return result
                except ValueError as e:
                    raise ValueError(f"Invalid {field_name}: {value} - {str(e)}")
            raise ValueError(f"{field_name} must be integer, got {type(value).__name__}")

        # Helper function for float conversion
        def to_float(value, field_name: str, default: float = None, min_val: float = 0.0, max_val: float = 2.0):
            if value is None:
                return default
            if isinstance(value, (int, float)):
                result = float(value)
            elif isinstance(value, str):
                try:
                    result = float(value)
                except ValueError:
                    raise ValueError(f"Invalid {field_name}: {value}")
            else:
                raise ValueError(f"{field_name} must be number, got {type(value).__name__}")

            if not (min_val <= result <= max_val):
                raise ValueError(f"{field_name} must be between {min_val} and {max_val}, got {result}")
            return result

        # Helper function for bool conversion
        def to_bool(value, field_name: str, default: bool = True):
            if value is None:
                return default
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                if value.lower() in ('true', '1', 'yes'):
                    return True
                if value.lower() in ('false', '0', 'no'):
                    return False
                raise ValueError(f"Invalid {field_name}: {value}")
            raise ValueError(f"{field_name} must be boolean, got {type(value).__name__}")

        # Parse agent instructions
        agent_instructions = AgentInstructions()
        if 'agent_instructions' in data:
            agent_instructions = AgentInstructions.from_dict(data['agent_instructions'])

        # Apply type conversions with validation
        cluster_max_tokens = to_int(data.get('cluster_max_tokens'), 'cluster_max_tokens', 128000)
        main_max_tokens = to_int(data.get('main_max_tokens'), 'main_max_tokens', 128000)
        fallback_max_tokens = to_int(data.get('fallback_max_tokens'), 'fallback_max_tokens', 64000)
        max_token_per_module = to_int(data.get('max_token_per_module'), 'max_token_per_module', 36369)
        max_token_per_leaf_module = to_int(data.get('max_token_per_leaf_module'), 'max_token_per_leaf_module', 16000)
        max_depth = to_int(data.get('max_depth'), 'max_depth', 2)

        cluster_temperature = to_float(data.get('cluster_temperature'), 'cluster_temperature', 0.0)
        main_temperature = to_float(data.get('main_temperature'), 'main_temperature', 0.0)
        fallback_temperature = to_float(data.get('fallback_temperature'), 'fallback_temperature', 0.0)

        cluster_temperature_supported = to_bool(data.get('cluster_temperature_supported'), 'cluster_temperature_supported', True)
        main_temperature_supported = to_bool(data.get('main_temperature_supported'), 'main_temperature_supported', True)
        fallback_temperature_supported = to_bool(data.get('fallback_temperature_supported'), 'fallback_temperature_supported', True)

        return cls(
            main_model=data.get('main_model', ''),
            cluster_model=data.get('cluster_model', ''),
            fallback_model=data.get('fallback_model', ''),
            default_output=data.get('default_output', 'docs'),
            cluster_base_url=data.get('cluster_base_url'),
            main_base_url=data.get('main_base_url'),
            fallback_base_url=data.get('fallback_base_url'),
            cluster_api_version=data.get('cluster_api_version'),
            main_api_version=data.get('main_api_version'),
            fallback_api_version=data.get('fallback_api_version'),
            cluster_max_tokens=cluster_max_tokens,
            main_max_tokens=main_max_tokens,
            fallback_max_tokens=fallback_max_tokens,
            cluster_temperature=cluster_temperature,
            main_temperature=main_temperature,
            fallback_temperature=fallback_temperature,
            cluster_temperature_supported=cluster_temperature_supported,
            main_temperature_supported=main_temperature_supported,
            fallback_temperature_supported=fallback_temperature_supported,
            cluster_max_token_field=data.get('cluster_max_token_field', 'max_tokens'),
            main_max_token_field=data.get('main_max_token_field', 'max_tokens'),
            fallback_max_token_field=data.get('fallback_max_token_field', 'max_tokens'),
            max_token_per_module=max_token_per_module,
            max_token_per_leaf_module=max_token_per_leaf_module,
            max_depth=max_depth,
            agent_instructions=agent_instructions,
        )
    
    def is_complete(self) -> bool:
        """Check if all required fields are set."""
        return bool(
            self.main_model and
            self.cluster_model and
            self.fallback_model
        )
    
    def to_backend_config(self, repo_path: str, output_dir: str, cluster_api_key: str = None, main_api_key: str = None, fallback_api_key: str = None, runtime_instructions: AgentInstructions = None):
        """
        Convert CLI Configuration to Backend Config.

        This method bridges the gap between persistent user settings (CLI Configuration)
        and runtime job configuration (Backend Config).

        Args:
            repo_path: Path to the repository to document
            output_dir: Output directory for generated documentation
            cluster_api_key: Optional cluster model API key (if not provided, fetched from keyring)
            main_api_key: Optional main model API key (if not provided, fetched from keyring)
            fallback_api_key: Optional fallback model API key (if not provided, fetched from keyring)
            runtime_instructions: Runtime agent instructions (override persistent settings)

        Returns:
            Backend Config instance ready for documentation generation
            
        Note:
            If API keys are not provided as arguments, they will be fetched from the system keyring
            using the ConfigManager.
        """
        from codewiki.src.config import Config

        # Fetch API keys from keyring if not provided
        if cluster_api_key is None or main_api_key is None or fallback_api_key is None:
            from codewiki.cli.config_manager import ConfigManager
            config_manager = ConfigManager()
            if cluster_api_key is None:
                cluster_api_key = config_manager.get_cluster_api_key()
            if main_api_key is None:
                main_api_key = config_manager.get_main_api_key()
            if fallback_api_key is None:
                fallback_api_key = config_manager.get_fallback_api_key()

        # Merge runtime instructions with persistent settings
        # Runtime instructions take precedence
        final_instructions = self.agent_instructions
        if runtime_instructions and not runtime_instructions.is_empty():
            final_instructions = AgentInstructions(
                include_patterns=runtime_instructions.include_patterns or self.agent_instructions.include_patterns,
                exclude_patterns=runtime_instructions.exclude_patterns or self.agent_instructions.exclude_patterns,
                focus_modules=runtime_instructions.focus_modules or self.agent_instructions.focus_modules,
                doc_type=runtime_instructions.doc_type or self.agent_instructions.doc_type,
                custom_instructions=runtime_instructions.custom_instructions or self.agent_instructions.custom_instructions,
            )

        return Config.from_cli(
            repo_path=repo_path,
            output_dir=output_dir,
            main_model=self.main_model,
            cluster_model=self.cluster_model,
            fallback_model=self.fallback_model,
            cluster_api_key=cluster_api_key,
            main_api_key=main_api_key,
            fallback_api_key=fallback_api_key,
            cluster_base_url=self.cluster_base_url,
            main_base_url=self.main_base_url,
            fallback_base_url=self.fallback_base_url,
            cluster_api_version=self.cluster_api_version,
            main_api_version=self.main_api_version,
            fallback_api_version=self.fallback_api_version,
            cluster_max_tokens=self.cluster_max_tokens,
            main_max_tokens=self.main_max_tokens,
            fallback_max_tokens=self.fallback_max_tokens,
            cluster_temperature=self.cluster_temperature,
            main_temperature=self.main_temperature,
            fallback_temperature=self.fallback_temperature,
            cluster_temperature_supported=self.cluster_temperature_supported,
            main_temperature_supported=self.main_temperature_supported,
            fallback_temperature_supported=self.fallback_temperature_supported,
            cluster_max_token_field=self.cluster_max_token_field,
            main_max_token_field=self.main_max_token_field,
            fallback_max_token_field=self.fallback_max_token_field,
            max_token_per_module=self.max_token_per_module,
            max_token_per_leaf_module=self.max_token_per_leaf_module,
            max_depth=self.max_depth,
            agent_instructions=final_instructions.to_dict() if final_instructions else None
        )

