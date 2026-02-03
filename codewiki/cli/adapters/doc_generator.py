"""
CLI adapter for documentation generator backend.

This adapter wraps the existing backend documentation_generator.py
and provides CLI-specific functionality like progress reporting.
"""

from pathlib import Path
from typing import Dict, Any, List
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
            
            # Process additional paths from config
            additional_paths_raw = self.config.get('additional_paths', [])
            additional_paths_normalized = None

            if additional_paths_raw:
                logger = logging.getLogger(__name__)
                logger.info(f"🔍 CLI received {len(additional_paths_raw)} additional path(s):")

                additional_paths_normalized = []
                for i, path in enumerate(additional_paths_raw, 1):
                    # Convert to absolute path (relative to repo_path)
                    normalized = str((Path(self.repo_path) / path).resolve())
                    logger.info(f"   ├─ Path #{i}: {path}")
                    logger.info(f"   │  └─ Normalized: {normalized}")
                    additional_paths_normalized.append(normalized)

                logger.info(f"   └─ Normalized {len(additional_paths_normalized)} additional path(s)")

            # Create backend config with CLI settings
            backend_config = BackendConfig.from_cli(
                repo_path=str(self.repo_path),
                output_dir=str(self.output_dir),
                main_model=self.config.get('main_model'),
                cluster_model=self.config.get('cluster_model'),
                fallback_model=self.config.get('fallback_model'),
                # Per-provider API keys (required)
                cluster_api_key=self.config.get('cluster_api_key'),
                main_api_key=self.config.get('main_api_key'),
                fallback_api_key=self.config.get('fallback_api_key'),
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
                diagrams_dir=str(self.diagrams_dir) if self.diagrams_dir else None,
                # Additional paths for dependency analysis (normalized)
                additional_source_paths=additional_paths_normalized
            )

            # Log configuration details in verbose mode
            if self.verbose:
                print()
                print("📋 Generation Configuration:")
                print(f"   ├─ Cluster Model: {backend_config.cluster_model}")
                print(f"   │  └─ Base URL: {backend_config.cluster_base_url or '(default)'}")
                print(f"   │  └─ Max Tokens: {backend_config.cluster_max_tokens}")
                print(f"   ├─ Main Model: {backend_config.main_model}")
                print(f"   │  └─ Base URL: {backend_config.main_base_url or '(default)'}")
                print(f"   │  └─ Max Tokens: {backend_config.main_max_tokens}")
                print(f"   ├─ Fallback Model: {backend_config.fallback_model}")
                print(f"   │  └─ Base URL: {backend_config.fallback_base_url or '(default)'}")
                print(f"   │  └─ Max Tokens: {backend_config.fallback_max_tokens}")
                print(f"   ├─ Module Settings:")
                print(f"   │  ├─ Max tokens/module: {backend_config.max_token_per_module}")
                print(f"   │  ├─ Max tokens/leaf: {backend_config.max_token_per_leaf_module}")
                print(f"   │  └─ Max depth: {backend_config.max_depth}")
                if backend_config.additional_source_paths:
                    print(f"   ├─ Additional Paths ({len(backend_config.additional_source_paths)}):")
                    for path in backend_config.additional_source_paths:
                        print(f"   │  └─ {path}")
                if backend_config.agent_instructions:
                    print(f"   └─ Agent Instructions: Configured")
                    if backend_config.agent_instructions.get('custom_instructions'):
                        custom = backend_config.agent_instructions['custom_instructions']
                        preview = custom[:80] + '...' if len(custom) > 80 else custom
                        print(f"      └─ Custom: {preview}")
                print()

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
            logger = logging.getLogger(__name__)
            logger.info("🔍 Stage 1: Repository Dependency Analysis")
            self.progress_tracker.update_stage(0.1, "Initializing dependency analyzer...")
            print(f"   ├─ Repository: {backend_config.repo_path}")
            print(f"   └─ Output: {backend_config.output_dir}")

            if backend_config.additional_source_paths:
                print(f"   ├─ Additional paths: {len(backend_config.additional_source_paths)}")
                for i, path in enumerate(backend_config.additional_source_paths, 1):
                    print(f"   │  └─ Path #{i}: {path}")

        # Create documentation generator
        if self.verbose:
            logger.info("├─ Initializing DocumentationGenerator...")
        doc_generator = DocumentationGenerator(backend_config)

        if self.verbose:
            self.progress_tracker.update_stage(0.4, "Scanning repository for source files...")
            logger.info("├─ Starting file discovery and AST parsing...")

        # Build dependency graph
        try:
            if self.verbose:
                self.progress_tracker.update_stage(0.7, "Building dependency graph...")

            import time
            start_time = time.time()
            components, leaf_nodes = doc_generator.graph_builder.build_dependency_graph()
            elapsed = time.time() - start_time

            self.job.statistics.total_files_analyzed = len(components)
            self.job.statistics.leaf_nodes = len(leaf_nodes)

            if self.verbose:
                self.progress_tracker.update_stage(1.0, f"Analysis complete ({elapsed:.2f}s)")
                logger.info(f"└─ ✅ Dependency graph built in {elapsed:.2f}s:")
                print(f"   ├─ Total components: {len(components)}")
                print(f"   ├─ Leaf nodes: {len(leaf_nodes)}")
                print(f"   └─ Files analyzed: {self.job.statistics.total_files_analyzed}")

                # Show component type breakdown
                type_counts = {}
                for comp in components.values():
                    comp_type = comp.component_type
                    type_counts[comp_type] = type_counts.get(comp_type, 0) + 1

                if type_counts:
                    print(f"   └─ Component types:")
                    for comp_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
                        print(f"      ├─ {comp_type}: {count}")
        except Exception as e:
            if self.verbose:
                logger.error(f"❌ Dependency analysis failed: {e}")
            raise APIError(f"Dependency analysis failed: {e}")

        self.progress_tracker.complete_stage()
        
        # Stage 2: Module Clustering
        self.progress_tracker.start_stage(2, "Module Clustering")

        if self.verbose:
            logger = logging.getLogger(__name__)
            logger.info("🔍 Stage 2: Module Clustering with LLM")

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
                if self.verbose:
                    self.progress_tracker.update_stage(0.3, "Loading cached module tree...")
                    logger.info(f"├─ Found cached module tree")
                    print(f"   └─ Cache file: {first_module_tree_path}")
                import time
                start_time = time.time()
                module_tree = file_manager.load_json(first_module_tree_path)
                elapsed = time.time() - start_time
                if self.verbose:
                    logger.info(f"│  └─ Loaded in {elapsed:.2f}s")
            else:
                if self.verbose:
                    self.progress_tracker.update_stage(0.2, "Analyzing code structure...")
                    logger.info(f"├─ No cached module tree found - calling LLM")
                    print(f"   ├─ Leaf nodes to cluster: {len(leaf_nodes)}")
                    print(f"   ├─ Using model: {backend_config.cluster_model}")
                    print(f"   │  └─ Base URL: {backend_config.cluster_base_url or '(default)'}")
                    print(f"   │  └─ Max tokens: {backend_config.cluster_max_tokens}")
                    print(f"   └─ Calling LLM for clustering...")

                import time
                start_time = time.time()
                module_tree = cluster_modules(leaf_nodes, components, backend_config)
                elapsed = time.time() - start_time

                file_manager.save_json(module_tree, first_module_tree_path)

                if self.verbose:
                    logger.info(f"│  └─ LLM clustering completed in {elapsed:.2f}s")

                if self.verbose:
                    self.progress_tracker.update_stage(0.7, f"Clustered into {len(module_tree)} modules")

            # === SYNTHETIC_MODULE_PATCH: Prevent context overflow ===
            # If module_tree is empty but we have leaf nodes, create synthetic modules
            # This prevents the "whole repo" fallback that exceeds API context limits
            # IMPORTANT: Runs AFTER loading cached file too (fixes cache bypass bug)
            # See: https://github.com/flamingo-stack/CodeWiki - forked with this fix
            if len(module_tree) == 0 and len(leaf_nodes) > 0:
                if self.verbose:
                    logger.warning("⚠️  Module tree is empty - creating synthetic modules")
                    logger.info("├─ Fallback: Creating synthetic modules to prevent context overflow")
                else:
                    logging.warning("⚠️  Module tree is empty - creating synthetic modules to prevent context overflow")

                max_per_module = int(os.environ.get('CODEWIKI_MAX_FILES_PER_MODULE', '5'))
                synthetic_modules = {}

                if self.verbose:
                    print(f"   ├─ Creating synthetic modules...")
                    print(f"   ├─ Files per module: {max_per_module}")
                    print(f"   └─ Total leaf nodes: {len(leaf_nodes)}")

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
                if self.verbose:
                    logger.info(f"│  └─ Created {len(module_tree)} synthetic modules ({max_per_module} files each)")
                else:
                    logging.info(f"✓ Created {len(module_tree)} synthetic modules ({max_per_module} files each)")
                # Update the cached file with synthetic modules
                file_manager.save_json(module_tree, first_module_tree_path)
            # === END SYNTHETIC_MODULE_PATCH ===

            file_manager.save_json(module_tree, module_tree_path)
            self.job.module_count = len(module_tree)

            if self.verbose:
                self.progress_tracker.update_stage(1.0, f"Module tree ready")
                logger.info(f"└─ ✅ Module clustering complete:")
                print(f"   ├─ Total modules: {len(module_tree)}")
                print(f"   └─ Module names: {', '.join(list(module_tree.keys())[:5])}" +
                      (f" ... ({len(module_tree) - 5} more)" if len(module_tree) > 5 else ""))

                # Show module size distribution
                if module_tree:
                    sizes = [len(mod.get('components', [])) for mod in module_tree.values()]
                    print(f"   └─ Module sizes: min={min(sizes)}, max={max(sizes)}, avg={sum(sizes)/len(sizes):.1f}")
        except Exception as e:
            if self.verbose:
                logger.error(f"❌ Module clustering failed: {e}")
            raise APIError(f"Module clustering failed: {e}")
        
        self.progress_tracker.complete_stage()
        
        # Stage 3: Documentation Generation
        self.progress_tracker.start_stage(3, "Documentation Generation")
        if self.verbose:
            logger = logging.getLogger(__name__)
            logger.info("🔍 Stage 3: LLM-Powered Documentation Generation")
            self.progress_tracker.update_stage(0.1, "Starting documentation generation...")
            print(f"   ├─ Modules to document: {len(module_tree)}")
            print(f"   ├─ Using model: {backend_config.main_model}")
            print(f"   │  └─ Base URL: {backend_config.main_base_url or '(default)'}")
            print(f"   │  └─ Max tokens: {backend_config.main_max_tokens}")
            print(f"   └─ Fallback model: {backend_config.fallback_model}")
            print(f"      └─ Base URL: {backend_config.fallback_base_url or '(default)'}")
            print()

        try:
            # Run the actual documentation generation
            if self.verbose:
                logger.info("├─ Generating module documentation (calling LLM for each module)...")

            import time
            start_time = time.time()
            await doc_generator.generate_module_documentation(components, leaf_nodes)
            elapsed = time.time() - start_time

            if self.verbose:
                logger.info(f"│  └─ Module documentation complete in {elapsed:.2f}s")
                self.progress_tracker.update_stage(0.9, "Creating repository overview...")
                logger.info("├─ Creating repository overview...")

            # Create metadata
            doc_generator.create_documentation_metadata(working_dir, components, len(leaf_nodes))

            # Collect generated files
            md_files = []
            json_files = []
            for file_path in os.listdir(working_dir):
                if file_path.endswith('.md'):
                    md_files.append(file_path)
                    self.job.files_generated.append(file_path)
                elif file_path.endswith('.json'):
                    json_files.append(file_path)
                    self.job.files_generated.append(file_path)

            if self.verbose:
                logger.info(f"│  ├─ Generated {len(md_files)} markdown files")
                logger.info(f"│  └─ Generated {len(json_files)} metadata files")

            # Extract Mermaid diagrams to separate directory if configured
            if backend_config.diagrams_dir:
                from codewiki.src.be.utils import extract_and_save_mermaid_diagrams, create_diagrams_readme

                if self.verbose:
                    self.progress_tracker.update_stage(0.95, "Extracting Mermaid diagrams...")
                    logger.info("├─ Extracting Mermaid diagrams...")

                all_diagram_files = []
                for file_path in os.listdir(working_dir):
                    if file_path.endswith('.md'):
                        md_path = os.path.join(working_dir, file_path)
                        diagram_files = extract_and_save_mermaid_diagrams(md_path, backend_config.diagrams_dir)
                        all_diagram_files.extend(diagram_files)

                # Create README index for diagrams
                if all_diagram_files:
                    create_diagrams_readme(backend_config.diagrams_dir, all_diagram_files)
                    if self.verbose:
                        logger.info(f"│  └─ Extracted {len(all_diagram_files)} diagrams to {backend_config.diagrams_dir}")
                    else:
                        logging.info(f"Extracted {len(all_diagram_files)} Mermaid diagrams to {backend_config.diagrams_dir}")

            if self.verbose:
                logger.info(f"└─ ✅ Documentation generation complete")

        except Exception as e:
            if self.verbose:
                logger.error(f"❌ Documentation generation failed: {e}")
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

