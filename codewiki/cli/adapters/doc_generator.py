"""
CLI adapter for documentation generator backend.

This adapter wraps the existing backend documentation_generator.py
and provides CLI-specific functionality like progress reporting.
"""

from pathlib import Path
from typing import Dict, Any
import time
import asyncio
import os
import logging
import sys

# Suppress verbose third-party library logs (OpenAI, Anthropic, httpx)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("openai._base_client").setLevel(logging.WARNING)
logging.getLogger("anthropic").setLevel(logging.WARNING)

from codewiki.cli.utils.progress import ProgressTracker
from codewiki.cli.models.job import DocumentationJob, LLMConfig
from codewiki.cli.utils.errors import APIError

# Import backend modules
from codewiki.src.be.documentation_generator import DocumentationGenerator
from codewiki.src.config import Config as BackendConfig, set_cli_context


class CLIDocumentationGenerator:
    """
    CLI adapter for documentation generation with progress reporting.

    This class wraps the backend documentation generator and adds
    CLI-specific features like progress tracking and error handling.
    """

    def __init__(
        self,
        repo_path: Path,
        output_dir: Path,
        config: Dict[str, Any],
        verbose: bool = False,
        generate_html: bool = False,
        diagrams_dir: Path = None
    ):
        """
        Initialize the CLI documentation generator.

        Args:
            repo_path: Repository path
            output_dir: Output directory
            config: LLM configuration
            verbose: Enable verbose output
            generate_html: Whether to generate HTML viewer
            diagrams_dir: Optional separate directory for Mermaid diagrams
        """
        self.repo_path = repo_path
        self.output_dir = output_dir
        self.config = config
        self.verbose = verbose
        self.generate_html = generate_html
        self.diagrams_dir = diagrams_dir
        self.progress_tracker = ProgressTracker(total_stages=5, verbose=verbose)
        self.job = DocumentationJob()
        
        # Setup job metadata
        self.job.repository_path = str(repo_path)
        self.job.repository_name = repo_path.name
        self.job.output_directory = str(output_dir)
        self.job.llm_config = LLMConfig(
            main_model=config.get('main_model', ''),
            cluster_model=config.get('cluster_model', ''),
            base_url=config.get('main_base_url', '')  # Use main_base_url for display
        )
        
        # Configure backend logging
        self._configure_backend_logging()
    
    def _configure_backend_logging(self):
        """Configure backend logger for CLI use with colored output."""
        from codewiki.src.be.dependency_analyzer.utils.logging_config import ColoredFormatter
        
        # Get backend logger (parent of all backend modules)
        backend_logger = logging.getLogger('codewiki.src.be')
        
        # Remove existing handlers to avoid duplicates
        backend_logger.handlers.clear()
        
        if self.verbose:
            # In verbose mode, show INFO and above
            backend_logger.setLevel(logging.INFO)
            
            # Create console handler with formatting
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            
            # Use colored formatter for better readability
            colored_formatter = ColoredFormatter()
            console_handler.setFormatter(colored_formatter)
            
            # Add handler to logger
            backend_logger.addHandler(console_handler)
        else:
            # In non-verbose mode, suppress backend logs (use WARNING level to hide INFO/DEBUG)
            backend_logger.setLevel(logging.WARNING)
            
            # Create console handler for warnings and errors only
            console_handler = logging.StreamHandler(sys.stderr)
            console_handler.setLevel(logging.WARNING)
            
            # Use colored formatter even for warnings/errors
            colored_formatter = ColoredFormatter()
            console_handler.setFormatter(colored_formatter)
            
            backend_logger.addHandler(console_handler)
        
        # Prevent propagation to root logger to avoid duplicate messages
        backend_logger.propagate = False
    
    def generate(self) -> DocumentationJob:
        """
        Generate documentation with progress tracking.
        
        Returns:
            Completed DocumentationJob
            
        Raises:
            APIError: If LLM API call fails
        """
        self.job.start()
        start_time = time.time()
        
        try:
            # Set CLI context for backend
            set_cli_context(True)
            
            # Create backend config with CLI settings
            backend_config = BackendConfig.from_cli(
                repo_path=str(self.repo_path),
                output_dir=str(self.output_dir),
                llm_api_key=self.config.get('api_key'),
                main_model=self.config.get('main_model'),
                cluster_model=self.config.get('cluster_model'),
                fallback_model=self.config.get('fallback_model'),
                # Per-provider base URLs
                cluster_base_url=self.config.get('cluster_base_url'),
                main_base_url=self.config.get('main_base_url'),
                fallback_base_url=self.config.get('fallback_base_url'),
                # Per-provider API versions
                cluster_api_version=self.config.get('cluster_api_version'),
                main_api_version=self.config.get('main_api_version'),
                fallback_api_version=self.config.get('fallback_api_version'),
                # Per-provider max tokens
                cluster_max_tokens=self.config.get('cluster_max_tokens', 128000),
                main_max_tokens=self.config.get('main_max_tokens', 128000),
                fallback_max_tokens=self.config.get('fallback_max_tokens', 64000),
                # Per-provider temperature
                cluster_temperature=self.config.get('cluster_temperature', 0.0),
                main_temperature=self.config.get('main_temperature', 0.0),
                fallback_temperature=self.config.get('fallback_temperature', 0.0),
                # Per-provider temperature support
                cluster_temperature_supported=self.config.get('cluster_temperature_supported', True),
                main_temperature_supported=self.config.get('main_temperature_supported', True),
                fallback_temperature_supported=self.config.get('fallback_temperature_supported', True),
                # Per-provider max token field names
                cluster_max_token_field=self.config.get('cluster_max_token_field', 'max_tokens'),
                main_max_token_field=self.config.get('main_max_token_field', 'max_tokens'),
                fallback_max_token_field=self.config.get('fallback_max_token_field', 'max_tokens'),
                # Shared clustering settings
                max_token_per_module=self.config.get('max_token_per_module', 36369),
                max_token_per_leaf_module=self.config.get('max_token_per_leaf_module', 16000),
                max_depth=self.config.get('max_depth', 2),
                # Agent instructions
                agent_instructions=self.config.get('agent_instructions'),
                # Optional diagrams directory
                diagrams_dir=str(self.diagrams_dir) if self.diagrams_dir else None
            )
            
            # Run backend documentation generation
            asyncio.run(self._run_backend_generation(backend_config))
            
            # Stage 4: HTML Generation (optional)
            if self.generate_html:
                self._run_html_generation()
            
            # Stage 5: Finalization (metadata already created by backend)
            self._finalize_job()
            
            # Complete job
            generation_time = time.time() - start_time
            self.job.complete()
            
            return self.job
            
        except APIError as e:
            self.job.fail(str(e))
            raise
        except Exception as e:
            self.job.fail(str(e))
            raise
    
    async def _run_backend_generation(self, backend_config: BackendConfig):
        """Run the backend documentation generation with progress tracking."""
        
        # Stage 1: Dependency Analysis
        self.progress_tracker.start_stage(1, "Dependency Analysis")
        if self.verbose:
            self.progress_tracker.update_stage(0.2, "Initializing dependency analyzer...")
        
        # Create documentation generator
        doc_generator = DocumentationGenerator(backend_config)
        
        if self.verbose:
            self.progress_tracker.update_stage(0.5, "Parsing source files...")
        
        # Build dependency graph
        try:
            components, leaf_nodes = doc_generator.graph_builder.build_dependency_graph()
            self.job.statistics.total_files_analyzed = len(components)
            self.job.statistics.leaf_nodes = len(leaf_nodes)
            
            if self.verbose:
                self.progress_tracker.update_stage(1.0, f"Found {len(leaf_nodes)} leaf nodes")
        except Exception as e:
            raise APIError(f"Dependency analysis failed: {e}")
        
        self.progress_tracker.complete_stage()
        
        # Stage 2: Module Clustering
        self.progress_tracker.start_stage(2, "Module Clustering")
        if self.verbose:
            self.progress_tracker.update_stage(0.5, "Clustering modules with LLM...")
        
        # Import clustering function
        from codewiki.src.be.cluster_modules import cluster_modules
        from codewiki.src.utils import file_manager
        from codewiki.src.config import FIRST_MODULE_TREE_FILENAME, MODULE_TREE_FILENAME
        
        working_dir = str(self.output_dir.absolute())
        file_manager.ensure_directory(working_dir)
        first_module_tree_path = os.path.join(working_dir, FIRST_MODULE_TREE_FILENAME)
        module_tree_path = os.path.join(working_dir, MODULE_TREE_FILENAME)
        
        try:
            if os.path.exists(first_module_tree_path):
                module_tree = file_manager.load_json(first_module_tree_path)
            else:
                module_tree = cluster_modules(leaf_nodes, components, backend_config)
                file_manager.save_json(module_tree, first_module_tree_path)

            # === SYNTHETIC_MODULE_PATCH: Prevent context overflow ===
            # If module_tree is empty but we have leaf nodes, create synthetic modules
            # This prevents the "whole repo" fallback that exceeds API context limits
            # IMPORTANT: Runs AFTER loading cached file too (fixes cache bypass bug)
            # See: https://github.com/flamingo-stack/CodeWiki - forked with this fix
            if len(module_tree) == 0 and len(leaf_nodes) > 0:
                logging.warning("Module tree is empty - creating synthetic modules to prevent context overflow")
                max_per_module = int(os.environ.get('CODEWIKI_MAX_FILES_PER_MODULE', '5'))
                synthetic_modules = {}

                for i in range(0, len(leaf_nodes), max_per_module):
                    batch = leaf_nodes[i:i + max_per_module]
                    module_name = f"module_{i // max_per_module + 1}"
                    # Handle both Node objects and strings (leaf_nodes can be either)
                    if batch and hasattr(batch[0], 'name'):
                        component_names = [node.name for node in batch]
                    else:
                        component_names = list(batch)  # Already strings
                    synthetic_modules[module_name] = {
                        "name": module_name,
                        "components": component_names,
                        "leaf_nodes": batch
                    }

                module_tree = synthetic_modules
                logging.info(f"Created {len(module_tree)} synthetic modules ({max_per_module} files each)")
                # Update the cached file with synthetic modules
                file_manager.save_json(module_tree, first_module_tree_path)
            # === END SYNTHETIC_MODULE_PATCH ===

            file_manager.save_json(module_tree, module_tree_path)
            self.job.module_count = len(module_tree)

            if self.verbose:
                self.progress_tracker.update_stage(1.0, f"Created {len(module_tree)} modules")
        except Exception as e:
            raise APIError(f"Module clustering failed: {e}")
        
        self.progress_tracker.complete_stage()
        
        # Stage 3: Documentation Generation
        self.progress_tracker.start_stage(3, "Documentation Generation")
        if self.verbose:
            self.progress_tracker.update_stage(0.1, "Generating module documentation...")
        
        try:
            # Run the actual documentation generation
            await doc_generator.generate_module_documentation(components, leaf_nodes)
            
            if self.verbose:
                self.progress_tracker.update_stage(0.9, "Creating repository overview...")
            
            # Create metadata
            doc_generator.create_documentation_metadata(working_dir, components, len(leaf_nodes))
            
            # Collect generated files
            for file_path in os.listdir(working_dir):
                if file_path.endswith('.md') or file_path.endswith('.json'):
                    self.job.files_generated.append(file_path)

            # Extract Mermaid diagrams to separate directory if configured
            if backend_config.diagrams_dir:
                from codewiki.src.be.utils import extract_and_save_mermaid_diagrams, create_diagrams_readme

                if self.verbose:
                    self.progress_tracker.update_stage(0.95, "Extracting Mermaid diagrams...")

                all_diagram_files = []
                for file_path in os.listdir(working_dir):
                    if file_path.endswith('.md'):
                        md_path = os.path.join(working_dir, file_path)
                        diagram_files = extract_and_save_mermaid_diagrams(md_path, backend_config.diagrams_dir)
                        all_diagram_files.extend(diagram_files)

                # Create README index for diagrams
                if all_diagram_files:
                    create_diagrams_readme(backend_config.diagrams_dir, all_diagram_files)
                    logging.info(f"Extracted {len(all_diagram_files)} Mermaid diagrams to {backend_config.diagrams_dir}")

        except Exception as e:
            raise APIError(f"Documentation generation failed: {e}")

        self.progress_tracker.complete_stage()
    
    def _run_html_generation(self):
        """Run HTML generation stage."""
        self.progress_tracker.start_stage(4, "HTML Generation")
        
        from codewiki.cli.html_generator import HTMLGenerator
        
        # Generate HTML
        html_generator = HTMLGenerator()
        
        if self.verbose:
            self.progress_tracker.update_stage(0.3, "Loading module tree and metadata...")
        
        repo_info = html_generator.detect_repository_info(self.repo_path)
        
        # Generate HTML with auto-loading of module_tree and metadata from docs_dir
        output_path = self.output_dir / "index.html"
        html_generator.generate(
            output_path=output_path,
            title=repo_info['name'],
            repository_url=repo_info['url'],
            github_pages_url=repo_info['github_pages_url'],
            docs_dir=self.output_dir  # Auto-load module_tree and metadata from here
        )
        
        self.job.files_generated.append("index.html")
        
        if self.verbose:
            self.progress_tracker.update_stage(1.0, "Generated index.html")
        
        self.progress_tracker.complete_stage()
    
    def _finalize_job(self):
        """Finalize the job (metadata already created by backend)."""
        # Just verify metadata exists
        metadata_path = self.output_dir / "metadata.json"
        if not metadata_path.exists():
            # Create our own if backend didn't
            with open(metadata_path, 'w') as f:
                f.write(self.job.to_json())

