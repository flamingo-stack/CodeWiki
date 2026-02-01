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
LLM_API_KEY = os.getenv('LLM_API_KEY', 'sk-1234')

@dataclass
class Config:
    """Configuration class for CodeWiki."""
    repo_path: str
    output_dir: str
    dependency_graph_dir: str
    docs_dir: str
    max_depth: int
    # LLM configuration
    llm_api_key: str
    main_model: str
    cluster_model: str
    fallback_model: str
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
            return self.agent_instructions.get('custom_instructions')
        return None

    def get_prompt_addition(self) -> str:
        """Generate prompt additions based on agent instructions."""
        if not self.agent_instructions:
            return ""

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
            # Escape curly braces to prevent KeyError when used with .format()
            # This is critical when custom_instructions contain JSON (e.g., external_repos config)
            escaped_instructions = escape_format_braces(self.custom_instructions)
            additions.append(f"Additional instructions: {escaped_instructions}")

        return "\n".join(additions) if additions else ""
    
    @classmethod
    def from_args(cls, args: argparse.Namespace) -> 'Config':
        """Create configuration from parsed arguments."""
        repo_name = os.path.basename(os.path.normpath(args.repo_path))
        sanitized_repo_name = ''.join(c if c.isalnum() else '_' for c in repo_name)

        # Get fallback model from environment (required)
        fallback_model = os.getenv('FALLBACK_MODEL')
        if not fallback_model:
            raise ValueError("FALLBACK_MODEL environment variable is required")

        return cls(
            repo_path=args.repo_path,
            output_dir=OUTPUT_BASE_DIR,
            dependency_graph_dir=os.path.join(OUTPUT_BASE_DIR, DEPENDENCY_GRAPHS_DIR),
            docs_dir=os.path.join(OUTPUT_BASE_DIR, DOCS_DIR, f"{sanitized_repo_name}-docs"),
            max_depth=MAX_DEPTH,
            llm_api_key=LLM_API_KEY,
            main_model=MAIN_MODEL,
            cluster_model=CLUSTER_MODEL,
            fallback_model=fallback_model,
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
        llm_api_key: str,
        main_model: str,
        cluster_model: str,
        fallback_model: str,
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
        diagrams_dir: str = None
    ) -> 'Config':
        """
        Create configuration for CLI context.

        Args:
            repo_path: Repository path
            output_dir: Output directory for generated docs
            llm_api_key: LLM API key
            main_model: Primary model
            cluster_model: Clustering model
            fallback_model: Fallback model
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

        Returns:
            Config instance
        """
        # === VALIDATION BLOCK START ===

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

        return cls(
            repo_path=repo_path,
            output_dir=base_output_dir,
            dependency_graph_dir=os.path.join(base_output_dir, DEPENDENCY_GRAPHS_DIR),
            docs_dir=output_dir,
            max_depth=max_depth,
            llm_api_key=llm_api_key,
            main_model=main_model,
            cluster_model=cluster_model,
            fallback_model=fallback_model,
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
            diagrams_dir=diagrams_dir
        )