from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
import argparse
import os
import sys
from dotenv import load_dotenv
from codewiki.src.be.flamingo_guidelines import escape_format_braces
load_dotenv()

# Constants
OUTPUT_BASE_DIR = 'output'
DEPENDENCY_GRAPHS_DIR = 'dependency_graphs'
DOCS_DIR = 'docs'
FIRST_MODULE_TREE_FILENAME = 'first_module_tree.json'
MODULE_TREE_FILENAME = 'module_tree.json'
OVERVIEW_FILENAME = 'overview.md'
MAX_DEPTH = 2
# Default max token settings
DEFAULT_MAX_TOKENS = 32_768
DEFAULT_MAX_TOKEN_PER_MODULE = 36_369
DEFAULT_MAX_TOKEN_PER_LEAF_MODULE = 16_000
# Legacy constants (for backward compatibility)
MAX_TOKEN_PER_MODULE = DEFAULT_MAX_TOKEN_PER_MODULE
MAX_TOKEN_PER_LEAF_MODULE = DEFAULT_MAX_TOKEN_PER_LEAF_MODULE

# CLI context detection
_CLI_CONTEXT = False

def set_cli_context(enabled: bool = True):
    """Set whether we're running in CLI context (vs web app)."""
    global _CLI_CONTEXT
    _CLI_CONTEXT = enabled

def is_cli_context() -> bool:
    """Check if running in CLI context."""
    return _CLI_CONTEXT

# LLM services
# In CLI mode, these will be loaded from ~/.codewiki/config.json + keyring
# In web app mode, use environment variables
MAIN_MODEL = os.getenv('MAIN_MODEL', 'claude-sonnet-4')
CLUSTER_MODEL = os.getenv('CLUSTER_MODEL', MAIN_MODEL)
LLM_BASE_URL = os.getenv('LLM_BASE_URL', 'http://0.0.0.0:4000/')

@dataclass
class Config:
    """Configuration class for CodeWiki."""
    repo_path: str
    output_dir: str
    dependency_graph_dir: str
    docs_dir: str
    max_depth: int
    # LLM configuration
    main_model: str
    cluster_model: str
    fallback_model: str
    # Per-provider API keys (required)
    cluster_api_key: str
    main_api_key: str
    fallback_api_key: str
    # Per-provider base URLs
    cluster_base_url: Optional[str] = None
    main_base_url: Optional[str] = None
    fallback_base_url: Optional[str] = None
    # Per-provider API versions
    cluster_api_version: Optional[str] = None
    main_api_version: Optional[str] = None
    fallback_api_version: Optional[str] = None
    # Per-provider max tokens settings
    cluster_max_tokens: int = DEFAULT_MAX_TOKENS
    main_max_tokens: int = DEFAULT_MAX_TOKENS
    fallback_max_tokens: int = DEFAULT_MAX_TOKENS
    # Max token settings for clustering (from upstream)
    max_token_per_module: int = DEFAULT_MAX_TOKEN_PER_MODULE
    max_token_per_leaf_module: int = DEFAULT_MAX_TOKEN_PER_LEAF_MODULE
    # Per-provider temperature settings
    cluster_temperature: float = 0.0
    main_temperature: float = 0.0
    fallback_temperature: float = 0.0
    cluster_temperature_supported: bool = True
    main_temperature_supported: bool = True
    fallback_temperature_supported: bool = True
    # Per-provider max token field names
    cluster_max_token_field: str = "max_tokens"  # 'max_tokens' or 'max_completion_tokens'
    main_max_token_field: str = "max_tokens"
    fallback_max_token_field: str = "max_tokens"
    # Agent instructions for customization (from upstream)
    agent_instructions: Optional[Dict[str, Any]] = None
    # Optional separate directory for Mermaid diagrams (from fork)
    # When set, diagrams are extracted from markdown and saved as separate files
    diagrams_dir: str = None
    # Multi-path support: additional source directories to analyze alongside repo_path
    # When None, operates in single-path mode (backward compatible)
    # When set, all paths are analyzed and merged into unified documentation
    additional_source_paths: Optional[List[str]] = None

    @property
    def include_patterns(self) -> Optional[List[str]]:
        """Get file include patterns from agent instructions."""
        if self.agent_instructions:
            return self.agent_instructions.get('include_patterns')
        return None

    @property
    def exclude_patterns(self) -> Optional[List[str]]:
        """Get file exclude patterns from agent instructions."""
        if self.agent_instructions:
            return self.agent_instructions.get('exclude_patterns')
        return None

    @property
    def focus_modules(self) -> Optional[List[str]]:
        """Get focus modules from agent instructions."""
        if self.agent_instructions:
            return self.agent_instructions.get('focus_modules')
        return None

    @property
    def doc_type(self) -> Optional[str]:
        """Get documentation type from agent instructions."""
        if self.agent_instructions:
            return self.agent_instructions.get('doc_type')
        return None

    @property
    def custom_instructions(self) -> Optional[str]:
        """Get custom instructions from agent instructions."""
        if self.agent_instructions:
            # Handle both dict and object with to_dict() method
            if hasattr(self.agent_instructions, 'to_dict'):
                instructions_dict = self.agent_instructions.to_dict()
            elif isinstance(self.agent_instructions, dict):
                instructions_dict = self.agent_instructions
            else:
                return None
            return instructions_dict.get('custom_instructions')
        return None

    @property
    def all_source_paths(self) -> List[str]:
        """
        Get all source paths to analyze (primary + additional).

        Returns:
            List of absolute paths. Always includes repo_path as first element.
            If additional_source_paths is None, returns single-element list.
        """
        import logging
        logger = logging.getLogger(__name__)

        paths = [os.path.abspath(self.repo_path)]
        if self.additional_source_paths:
            paths.extend([os.path.abspath(p) for p in self.additional_source_paths])
            logger.debug(f"🔍 all_source_paths property accessed:")
            logger.debug(f"   ├─ Primary: {paths[0]}")
            for i, path in enumerate(paths[1:], 1):
                logger.debug(f"   └─ Additional #{i}: {path}")
        else:
            logger.debug(f"🔍 all_source_paths property accessed (single-path mode): {paths[0]}")
        return paths

    def validate_source_paths(self) -> None:
        """
        Validate that all source paths exist and are accessible directories.

        Raises:
            ValueError: If any path does not exist or is not a directory
            OSError: If any path cannot be accessed
        """
        import logging
        logger = logging.getLogger(__name__)

        logger.info("🔍 Validating source paths...")

        # Validate primary repo_path
        logger.debug(f"   ├─ Checking primary path: {self.repo_path}")
        if not os.path.exists(self.repo_path):
            raise ValueError(f"Primary repository path does not exist: {self.repo_path}")
        if not os.path.isdir(self.repo_path):
            raise ValueError(f"Primary repository path is not a directory: {self.repo_path}")
        logger.info(f"   ├─ ✓ Primary path valid: {self.repo_path}")

        # Validate additional paths if configured
        if self.additional_source_paths:
            logger.info(f"   ├─ Validating {len(self.additional_source_paths)} additional path(s)...")
            for i, path in enumerate(self.additional_source_paths, start=1):
                logger.debug(f"   │  └─ Checking additional path #{i}: {path}")
                if not os.path.exists(path):
                    raise ValueError(f"Additional source path #{i} does not exist: {path}")
                if not os.path.isdir(path):
                    raise ValueError(f"Additional source path #{i} is not a directory: {path}")

                # Check for read access
                if not os.access(path, os.R_OK):
                    raise OSError(f"Additional source path #{i} is not readable: {path}")
                logger.info(f"   │  ├─ ✓ Additional path #{i} valid: {path}")
            logger.info(f"   └─ ✓ All {len(self.additional_source_paths)} additional path(s) validated")
        else:
            logger.debug(f"   └─ No additional paths to validate (single-path mode)")

    def is_multi_path_mode(self) -> bool:
        """
        Check if configuration is in multi-path mode.

        Returns:
            True if additional_source_paths is set and non-empty, False otherwise
        """
        import logging
        logger = logging.getLogger(__name__)

        result = bool(self.additional_source_paths)
        if result:
            logger.debug(f"🔍 Multi-path mode: ENABLED ({len(self.additional_source_paths)} additional paths)")
        else:
            logger.debug("🔍 Multi-path mode: DISABLED (single-path)")
        return result

    def get_prompt_addition(self) -> str:
        """Generate prompt additions based on agent instructions."""
        import logging
        logger = logging.getLogger(__name__)

        if not self.agent_instructions:
            logger.debug("📋 get_prompt_addition: No agent_instructions configured")
            return ""

        logger.debug("📋 get_prompt_addition: Building combined instructions")

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
                logger.debug(f"   ├─ Added doc_type: {self.doc_type}")
            else:
                additions.append(f"Focus on generating {self.doc_type} documentation.")
                logger.debug(f"   ├─ Added custom doc_type: {self.doc_type}")

        if self.focus_modules:
            additions.append(f"Pay special attention to and provide more detailed documentation for these modules: {', '.join(self.focus_modules)}")
            logger.debug(f"   ├─ Added focus_modules: {len(self.focus_modules)} modules")

        if self.custom_instructions:
            # Escape curly braces to prevent KeyError when used with .format()
            # This is critical when custom_instructions contain JSON (e.g., external_repos config)
            escaped_instructions = escape_format_braces(self.custom_instructions)
            additions.append(f"Additional instructions: {escaped_instructions}")
            logger.debug(f"   ├─ Added custom_instructions: {len(self.custom_instructions)} chars")
            logger.debug(f"   │  └─ Preview: {self.custom_instructions[:100]}...")
        else:
            logger.debug(f"   └─ No custom_instructions field present")

        result = "\n".join(additions) if additions else ""
        logger.debug(f"   └─ Total combined: {len(result)} chars")
        return result
    
    @classmethod
    def from_args(cls, args: argparse.Namespace) -> 'Config':
        """Create configuration from parsed arguments."""
        repo_name = os.path.basename(os.path.normpath(args.repo_path))
        sanitized_repo_name = ''.join(c if c.isalnum() else '_' for c in repo_name)

        # Get fallback model from environment (required)
        fallback_model = os.getenv('FALLBACK_MODEL')
        if not fallback_model:
            raise ValueError("FALLBACK_MODEL environment variable is required")

        # Get per-provider API keys from environment (REQUIRED)
        cluster_api_key = os.getenv('CLUSTER_API_KEY')
        main_api_key = os.getenv('MAIN_API_KEY')
        fallback_api_key = os.getenv('FALLBACK_API_KEY')

        # Validate all per-provider API keys are set
        if not cluster_api_key:
            raise ValueError(
                "CLUSTER_API_KEY environment variable is required.\n"
                "Set it to your cluster provider API key (OpenAI, Anthropic, etc.)"
            )
        if not main_api_key:
            raise ValueError(
                "MAIN_API_KEY environment variable is required.\n"
                "Set it to your main/generation provider API key (OpenAI, Anthropic, etc.)"
            )
        if not fallback_api_key:
            raise ValueError(
                "FALLBACK_API_KEY environment variable is required.\n"
                "Set it to your fallback provider API key (OpenAI, Anthropic, etc.)"
            )

        return cls(
            repo_path=args.repo_path,
            output_dir=OUTPUT_BASE_DIR,
            dependency_graph_dir=os.path.join(OUTPUT_BASE_DIR, DEPENDENCY_GRAPHS_DIR),
            docs_dir=os.path.join(OUTPUT_BASE_DIR, DOCS_DIR, f"{sanitized_repo_name}-docs"),
            max_depth=MAX_DEPTH,
            main_model=MAIN_MODEL,
            cluster_model=CLUSTER_MODEL,
            fallback_model=fallback_model,
            cluster_api_key=cluster_api_key,
            main_api_key=main_api_key,
            fallback_api_key=fallback_api_key,
            # Per-provider base URLs default to LLM_BASE_URL from environment
            cluster_base_url=LLM_BASE_URL,
            main_base_url=LLM_BASE_URL,
            fallback_base_url=LLM_BASE_URL
        )
    
    @classmethod
    def from_cli(
        cls,
        repo_path: str,
        output_dir: str,
        main_model: str,
        cluster_model: str,
        fallback_model: str,
        cluster_api_key: str,
        main_api_key: str,
        fallback_api_key: str,
        cluster_base_url: Optional[str] = None,
        main_base_url: Optional[str] = None,
        fallback_base_url: Optional[str] = None,
        cluster_api_version: Optional[str] = None,
        main_api_version: Optional[str] = None,
        fallback_api_version: Optional[str] = None,
        cluster_max_tokens: int = DEFAULT_MAX_TOKENS,
        main_max_tokens: int = DEFAULT_MAX_TOKENS,
        fallback_max_tokens: int = DEFAULT_MAX_TOKENS,
        max_token_per_module: int = DEFAULT_MAX_TOKEN_PER_MODULE,
        max_token_per_leaf_module: int = DEFAULT_MAX_TOKEN_PER_LEAF_MODULE,
        max_depth: int = MAX_DEPTH,
        cluster_temperature: float = 0.0,
        main_temperature: float = 0.0,
        fallback_temperature: float = 0.0,
        cluster_temperature_supported: bool = True,
        main_temperature_supported: bool = True,
        fallback_temperature_supported: bool = True,
        cluster_max_token_field: str = "max_tokens",
        main_max_token_field: str = "max_tokens",
        fallback_max_token_field: str = "max_tokens",
        agent_instructions: Optional[Dict[str, Any]] = None,
        diagrams_dir: str = None,
        additional_source_paths: Optional[List[str]] = None
    ) -> 'Config':
        """
        Create configuration for CLI context.

        Args:
            repo_path: Repository path
            output_dir: Output directory for generated docs
            main_model: Primary model
            cluster_model: Clustering model
            fallback_model: Fallback model
            cluster_api_key: Cluster model API key (required)
            main_api_key: Main model API key (required)
            fallback_api_key: Fallback model API key (required)
            cluster_base_url: Cluster model API base URL
            main_base_url: Main model API base URL
            fallback_base_url: Fallback model API base URL
            cluster_api_version: Cluster model API version
            main_api_version: Main model API version
            fallback_api_version: Fallback model API version
            cluster_max_tokens: Maximum tokens for cluster model
            main_max_tokens: Maximum tokens for main model
            fallback_max_tokens: Maximum tokens for fallback model
            max_token_per_module: Maximum tokens per module for clustering
            max_token_per_leaf_module: Maximum tokens per leaf module
            max_depth: Maximum depth for hierarchical decomposition
            cluster_temperature: Temperature for cluster model
            main_temperature: Temperature for main model
            fallback_temperature: Temperature for fallback model
            cluster_temperature_supported: Whether cluster model supports custom temperature
            main_temperature_supported: Whether main model supports custom temperature
            fallback_temperature_supported: Whether fallback model supports custom temperature
            cluster_max_token_field: Parameter name for cluster model max tokens
            main_max_token_field: Parameter name for main model max tokens
            fallback_max_token_field: Parameter name for fallback model max tokens
            agent_instructions: Custom agent instructions dict
            diagrams_dir: Optional separate directory for Mermaid diagrams
            additional_source_paths: Additional directories to analyze (multi-path mode)

        Returns:
            Config instance
        """
        # === VALIDATION BLOCK START ===

        # 0. API KEY VALIDATION - CRITICAL: All API keys are required
        if not cluster_api_key or (isinstance(cluster_api_key, str) and cluster_api_key.strip() == ''):
            raise ValueError(
                "cluster_api_key is required for clustering operations.\n"
                "Provide a valid API key for your cluster provider (OpenAI, Anthropic, etc.)"
            )
        if not main_api_key or (isinstance(main_api_key, str) and main_api_key.strip() == ''):
            raise ValueError(
                "main_api_key is required for main/generation model operations.\n"
                "Provide a valid API key for your main provider (OpenAI, Anthropic, etc.)"
            )
        if not fallback_api_key or (isinstance(fallback_api_key, str) and fallback_api_key.strip() == ''):
            raise ValueError(
                "fallback_api_key is required for fallback model operations.\n"
                "Provide a valid API key for your fallback provider (OpenAI, Anthropic, etc.)"
            )

        # 1. Base URL validation - CRITICAL: All base URLs are required
        if not cluster_base_url or cluster_base_url.strip() == '':
            raise ValueError("cluster_base_url is required for clustering operations")
        if not main_base_url or main_base_url.strip() == '':
            raise ValueError("main_base_url is required for main model operations")
        if not fallback_base_url or fallback_base_url.strip() == '':
            raise ValueError("fallback_base_url is required for fallback model operations")

        # 2. Type validation and coercion for max_tokens parameters
        # Ensure all max_tokens are integers
        if not isinstance(cluster_max_tokens, int):
            try:
                cluster_max_tokens = int(cluster_max_tokens)
            except (ValueError, TypeError):
                raise ValueError(
                    f"cluster_max_tokens must be integer, got {type(cluster_max_tokens).__name__}: {cluster_max_tokens}"
                )

        if not isinstance(main_max_tokens, int):
            try:
                main_max_tokens = int(main_max_tokens)
            except (ValueError, TypeError):
                raise ValueError(
                    f"main_max_tokens must be integer, got {type(main_max_tokens).__name__}: {main_max_tokens}"
                )

        if not isinstance(fallback_max_tokens, int):
            try:
                fallback_max_tokens = int(fallback_max_tokens)
            except (ValueError, TypeError):
                raise ValueError(
                    f"fallback_max_tokens must be integer, got {type(fallback_max_tokens).__name__}: {fallback_max_tokens}"
                )

        if not isinstance(max_token_per_module, int):
            try:
                max_token_per_module = int(max_token_per_module)
            except (ValueError, TypeError):
                raise ValueError(
                    f"max_token_per_module must be integer, got {type(max_token_per_module).__name__}: {max_token_per_module}"
                )

        if not isinstance(max_token_per_leaf_module, int):
            try:
                max_token_per_leaf_module = int(max_token_per_leaf_module)
            except (ValueError, TypeError):
                raise ValueError(
                    f"max_token_per_leaf_module must be integer, got {type(max_token_per_leaf_module).__name__}: {max_token_per_leaf_module}"
                )

        if not isinstance(max_depth, int):
            try:
                max_depth = int(max_depth)
            except (ValueError, TypeError):
                raise ValueError(
                    f"max_depth must be integer, got {type(max_depth).__name__}: {max_depth}"
                )

        # Type validation and coercion for temperature parameters
        # Ensure all temperatures are floats
        if not isinstance(cluster_temperature, float):
            try:
                cluster_temperature = float(cluster_temperature)
            except (ValueError, TypeError):
                raise ValueError(
                    f"cluster_temperature must be float, got {type(cluster_temperature).__name__}: {cluster_temperature}"
                )

        if not isinstance(main_temperature, float):
            try:
                main_temperature = float(main_temperature)
            except (ValueError, TypeError):
                raise ValueError(
                    f"main_temperature must be float, got {type(main_temperature).__name__}: {main_temperature}"
                )

        if not isinstance(fallback_temperature, float):
            try:
                fallback_temperature = float(fallback_temperature)
            except (ValueError, TypeError):
                raise ValueError(
                    f"fallback_temperature must be float, got {type(fallback_temperature).__name__}: {fallback_temperature}"
                )

        # 3. Range validation for max_tokens parameters
        # All max_tokens must be positive
        if cluster_max_tokens <= 0:
            raise ValueError(f"cluster_max_tokens must be positive, got {cluster_max_tokens}")

        if main_max_tokens <= 0:
            raise ValueError(f"main_max_tokens must be positive, got {main_max_tokens}")

        if fallback_max_tokens <= 0:
            raise ValueError(f"fallback_max_tokens must be positive, got {fallback_max_tokens}")

        if max_token_per_module <= 0:
            raise ValueError(f"max_token_per_module must be positive, got {max_token_per_module}")

        if max_token_per_leaf_module <= 0:
            raise ValueError(f"max_token_per_leaf_module must be positive, got {max_token_per_leaf_module}")

        if max_depth <= 0:
            raise ValueError(f"max_depth must be positive, got {max_depth}")

        # Range validation for temperature parameters
        # Temperature must be between 0.0 and 2.0 (OpenAI/Anthropic standard)
        if not (0.0 <= cluster_temperature <= 2.0):
            raise ValueError(
                f"cluster_temperature must be between 0.0 and 2.0, got {cluster_temperature}"
            )

        if not (0.0 <= main_temperature <= 2.0):
            raise ValueError(
                f"main_temperature must be between 0.0 and 2.0, got {main_temperature}"
            )

        if not (0.0 <= fallback_temperature <= 2.0):
            raise ValueError(
                f"fallback_temperature must be between 0.0 and 2.0, got {fallback_temperature}"
            )

        # 4. Field name validation for max_token_field parameters
        # Valid options are 'max_tokens' or 'max_completion_tokens'
        valid_max_token_fields = {'max_tokens', 'max_completion_tokens'}

        if cluster_max_token_field not in valid_max_token_fields:
            raise ValueError(
                f"cluster_max_token_field must be one of {valid_max_token_fields}, "
                f"got '{cluster_max_token_field}'"
            )

        if main_max_token_field not in valid_max_token_fields:
            raise ValueError(
                f"main_max_token_field must be one of {valid_max_token_fields}, "
                f"got '{main_max_token_field}'"
            )

        if fallback_max_token_field not in valid_max_token_fields:
            raise ValueError(
                f"fallback_max_token_field must be one of {valid_max_token_fields}, "
                f"got '{fallback_max_token_field}'"
            )

        # === VALIDATION BLOCK END ===

        repo_name = os.path.basename(os.path.normpath(repo_path))
        base_output_dir = os.path.join(output_dir, "temp")

        # Create config instance
        config = cls(
            repo_path=repo_path,
            output_dir=base_output_dir,
            dependency_graph_dir=os.path.join(base_output_dir, DEPENDENCY_GRAPHS_DIR),
            docs_dir=output_dir,
            max_depth=max_depth,
            main_model=main_model,
            cluster_model=cluster_model,
            fallback_model=fallback_model,
            cluster_api_key=cluster_api_key,
            main_api_key=main_api_key,
            fallback_api_key=fallback_api_key,
            cluster_base_url=cluster_base_url,
            main_base_url=main_base_url,
            fallback_base_url=fallback_base_url,
            cluster_api_version=cluster_api_version,
            main_api_version=main_api_version,
            fallback_api_version=fallback_api_version,
            cluster_max_tokens=cluster_max_tokens,
            main_max_tokens=main_max_tokens,
            fallback_max_tokens=fallback_max_tokens,
            max_token_per_module=max_token_per_module,
            max_token_per_leaf_module=max_token_per_leaf_module,
            cluster_temperature=cluster_temperature,
            main_temperature=main_temperature,
            fallback_temperature=fallback_temperature,
            cluster_temperature_supported=cluster_temperature_supported,
            main_temperature_supported=main_temperature_supported,
            fallback_temperature_supported=fallback_temperature_supported,
            cluster_max_token_field=cluster_max_token_field,
            main_max_token_field=main_max_token_field,
            fallback_max_token_field=fallback_max_token_field,
            agent_instructions=agent_instructions,
            diagrams_dir=diagrams_dir,
            additional_source_paths=additional_source_paths
        )

        # Validate all source paths exist and are accessible
        config.validate_source_paths()

        return config

    @classmethod
    def from_config_manager(
        cls,
        manager: 'ConfigManager',
        repo_path: str,
        output_dir: str
    ) -> 'Config':
        """
        Create configuration from ConfigManager.

        Args:
            manager: ConfigManager instance with loaded configuration
            repo_path: Repository path
            output_dir: Output directory for generated docs

        Returns:
            Config instance

        Raises:
            ValueError: If required configuration is missing
        """
        from codewiki.cli.config_manager import ConfigManager

        # Get configuration object
        config_obj = manager.get_config()
        if config_obj is None:
            raise ValueError("ConfigManager has no configuration loaded")

        # Get per-provider API keys (required)
        cluster_api_key = manager.get_cluster_api_key()
        main_api_key = manager.get_main_api_key()
        fallback_api_key = manager.get_fallback_api_key()

        # Validate all API keys are present
        if not cluster_api_key:
            raise ValueError("cluster_api_key is required. Run 'codewiki config set --cluster-api-key <key>'")
        if not main_api_key:
            raise ValueError("main_api_key is required. Run 'codewiki config set --main-api-key <key>'")
        if not fallback_api_key:
            raise ValueError("fallback_api_key is required. Run 'codewiki config set --fallback-api-key <key>'")

        # Validate required models are set
        if not config_obj.main_model:
            raise ValueError("main_model is not configured")
        if not config_obj.cluster_model:
            raise ValueError("cluster_model is not configured")
        if not config_obj.fallback_model:
            raise ValueError("fallback_model is not configured")

        # Extract additional_source_paths from agent_instructions if present
        additional_paths = None
        if config_obj.agent_instructions:
            agent_dict = config_obj.agent_instructions.to_dict() if hasattr(config_obj.agent_instructions, 'to_dict') else config_obj.agent_instructions
            if isinstance(agent_dict, dict):
                additional_paths = agent_dict.get('additional_source_paths')

        # Use from_cli with all configuration from ConfigManager
        return cls.from_cli(
            repo_path=repo_path,
            output_dir=output_dir,
            main_model=config_obj.main_model,
            cluster_model=config_obj.cluster_model,
            fallback_model=config_obj.fallback_model,
            cluster_api_key=cluster_api_key,
            main_api_key=main_api_key,
            fallback_api_key=fallback_api_key,
            cluster_base_url=config_obj.cluster_base_url,
            main_base_url=config_obj.main_base_url,
            fallback_base_url=config_obj.fallback_base_url,
            cluster_api_version=config_obj.cluster_api_version,
            main_api_version=config_obj.main_api_version,
            fallback_api_version=config_obj.fallback_api_version,
            cluster_max_tokens=config_obj.cluster_max_tokens,
            main_max_tokens=config_obj.main_max_tokens,
            fallback_max_tokens=config_obj.fallback_max_tokens,
            max_token_per_module=config_obj.max_token_per_module,
            max_token_per_leaf_module=config_obj.max_token_per_leaf_module,
            max_depth=config_obj.max_depth,
            cluster_temperature=config_obj.cluster_temperature,
            main_temperature=config_obj.main_temperature,
            fallback_temperature=config_obj.fallback_temperature,
            cluster_temperature_supported=config_obj.cluster_temperature_supported,
            main_temperature_supported=config_obj.main_temperature_supported,
            fallback_temperature_supported=config_obj.fallback_temperature_supported,
            cluster_max_token_field=config_obj.cluster_max_token_field,
            main_max_token_field=config_obj.main_max_token_field,
            fallback_max_token_field=config_obj.fallback_max_token_field,
            agent_instructions=config_obj.agent_instructions.to_dict() if config_obj.agent_instructions else None,
            diagrams_dir=None,
            additional_source_paths=additional_paths
        )