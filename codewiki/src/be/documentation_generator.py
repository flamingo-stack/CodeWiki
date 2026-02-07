"""
Documentation Generator Module

SYNTHETIC_MODULE_PATCH: Patched by flamingo-stack to prevent context overflow

This module contains the DocumentationGenerator class which orchestrates the
documentation generation process for a given repository.
"""
import logging
import os
import json
from typing import Dict, List, Any
from copy import deepcopy
import traceback

# Configure logging and monitoring
logger = logging.getLogger(__name__)

# Local imports
from codewiki.src.be.dependency_analyzer import DependencyGraphBuilder
from codewiki.src.be.llm_services import call_llm
from codewiki.src.be.prompt_template import (
    REPO_OVERVIEW_PROMPT,
    MODULE_OVERVIEW_PROMPT,
    format_repo_overview_prompt,
    format_module_overview_prompt,
)
from codewiki.src.be.cluster_modules import cluster_modules
from codewiki.src.config import (
    Config,
    FIRST_MODULE_TREE_FILENAME,
    MODULE_TREE_FILENAME,
    OVERVIEW_FILENAME
)
from codewiki.src.utils import file_manager
from codewiki.src.be.agent_orchestrator import AgentOrchestrator


class DocumentationGenerator:
    """Main documentation generation orchestrator."""
    
    def __init__(self, config: Config, commit_id: str = None):
        self.config = config
        self.commit_id = commit_id
        self.graph_builder = DependencyGraphBuilder(config)
        self.agent_orchestrator = AgentOrchestrator(config)

    def _get_nested_working_dir(self, base_dir: str, module_path: List[str]) -> str:
        """
        Compute nested working directory based on module hierarchy.

        Args:
            base_dir: Base output directory (e.g., "docs/reference/architecture")
            module_path: Module path list (e.g., ["Backend", "Authentication", "JWT"])

        Returns:
            Nested directory path (e.g., "docs/reference/architecture/Backend/Authentication")

        Note: The module's own name is NOT included in the path - it becomes the filename.
        For module_path ["Backend", "Authentication", "JWT"], the directory is:
        "docs/reference/architecture/Backend/Authentication/" and file is "JWT.md"
        """
        if not module_path or len(module_path) <= 1:
            # Root modules stay in base directory
            return base_dir

        # Use all path elements except the last one (which is the module name, not a directory)
        parent_path = module_path[:-1]
        nested_path = os.path.join(base_dir, *parent_path)
        return os.path.abspath(nested_path)

    def create_documentation_metadata(self, working_dir: str, components: Dict[str, Any], num_leaf_nodes: int):
        """Create a metadata file with documentation generation information."""
        from datetime import datetime
        
        metadata = {
            "generation_info": {
                "timestamp": datetime.now().isoformat(),
                "main_model": self.config.main_model,
                "generator_version": "1.0.1",
                "repo_path": self.config.repo_path,
                "commit_id": self.commit_id
            },
            "statistics": {
                "total_components": len(components),
                "leaf_nodes": num_leaf_nodes,
                "max_depth": self.config.max_depth
            },
            "files_generated": [
                "overview.md",
                "module_tree.json",
                "first_module_tree.json"
            ]
        }
        
        # Add generated markdown files to the metadata
        try:
            for file_path in os.listdir(working_dir):
                if file_path.endswith('.md') and file_path not in metadata["files_generated"]:
                    metadata["files_generated"].append(file_path)
        except Exception as e:
            logger.warning(f"Could not list generated files: {e}")
        
        metadata_path = os.path.join(working_dir, "metadata.json")
        file_manager.save_json(metadata, metadata_path)

    
    def get_processing_order(self, module_tree: Dict[str, Any], parent_path: List[str] = []) -> List[tuple[List[str], str]]:
        """Get the processing order using topological sort (leaf modules first)."""
        processing_order = []
        
        def collect_modules(tree: Dict[str, Any], path: List[str]):
            for module_name, module_info in tree.items():
                current_path = path + [module_name]
                
                # If this module has children, process them first
                if module_info.get("children") and isinstance(module_info["children"], dict) and module_info["children"]:
                    collect_modules(module_info["children"], current_path)
                    # Add this parent module after its children
                    processing_order.append((current_path, module_name))
                else:
                    # This is a leaf module, add it immediately
                    processing_order.append((current_path, module_name))
        
        collect_modules(module_tree, parent_path)
        return processing_order

    def is_leaf_module(self, module_info: Dict[str, Any]) -> bool:
        """Check if a module is a leaf module (has no children or empty children)."""
        children = module_info.get("children", {})
        return not children or (isinstance(children, dict) and len(children) == 0)

    def build_overview_structure(self, module_tree: Dict[str, Any], module_path: List[str],
                                 working_dir: str) -> Dict[str, Any]:
        """Build structure for overview generation with 1-depth children docs and target indicator."""
        
        processed_module_tree = deepcopy(module_tree)
        module_info = processed_module_tree
        for path_part in module_path:
            module_info = module_info[path_part]
            if path_part != module_path[-1]:
                module_info = module_info.get("children", {})
            else:
                module_info["is_target_for_overview_generation"] = True

        if "children" in module_info:
            module_info = module_info["children"]

        for child_name, child_info in module_info.items():
            child_doc_path = os.path.join(working_dir, f"{child_name}.md")
            if os.path.exists(child_doc_path):
                child_info["docs"] = file_manager.load_text(child_doc_path)
            else:
                logger.warning(f"Module docs not found at {child_doc_path}")
                child_info["docs"] = ""

        return processed_module_tree

    async def generate_module_documentation(self, components: Dict[str, Any], leaf_nodes: List[str]) -> str:
        """Generate documentation for all modules using dynamic programming approach."""
        logger.info("📝 Stage 3.1: Module Documentation Generation")

        # Prepare output directory
        working_dir = os.path.abspath(self.config.docs_dir)
        file_manager.ensure_directory(working_dir)
        logger.debug(f"├─ Working directory: {working_dir}")

        module_tree_path = os.path.join(working_dir, MODULE_TREE_FILENAME)
        first_module_tree_path = os.path.join(working_dir, FIRST_MODULE_TREE_FILENAME)
        logger.debug(f"├─ Loading module trees...")
        logger.debug(f"│  ├─ Module tree: {MODULE_TREE_FILENAME}")
        logger.debug(f"│  └─ First module tree: {FIRST_MODULE_TREE_FILENAME}")

        module_tree = file_manager.load_json(module_tree_path)
        first_module_tree = file_manager.load_json(first_module_tree_path)

        logger.info(f"├─ Module tree loaded: {len(module_tree)} top-level modules")

        # Get processing order (leaf modules first)
        logger.debug("├─ Calculating processing order (topological sort: leaf modules first)...")
        processing_order = self.get_processing_order(first_module_tree)
        logger.info(f"│  └─ Processing order: {len(processing_order)} modules total")

        
        # Process modules in dependency order
        final_module_tree = module_tree
        processed_modules = set()

        if len(module_tree) > 0:
            logger.info(f"├─ Processing {len(processing_order)} modules...")
            for idx, (module_path, module_name) in enumerate(processing_order, 1):
                try:
                    # Get the module info from the tree
                    module_info = module_tree
                    for path_part in module_path:
                        module_info = module_info[path_part]
                        if path_part != module_path[-1]:  # Not the last part
                            module_info = module_info.get("children", {})

                    # Skip if already processed
                    module_key = "/".join(module_path)
                    if module_key in processed_modules:
                        logger.debug(f"│  ├─ [{idx}/{len(processing_order)}] Skipping {module_key} (already processed)")
                        continue

                    # Process the module
                    if self.is_leaf_module(module_info):
                        component_list = module_info["components"]
                        logger.info(f"│  ├─ [{idx}/{len(processing_order)}] 📄 Leaf module: {module_key}")
                        logger.info(f"│  │  ├─ Components: {len(component_list)}")
                        logger.info(f"│  │  │  └─ {', '.join(component_list[:5])}" +
                                   (f" ... and {len(component_list) - 5} more" if len(component_list) > 5 else ""))

                        # Log file breakdown
                        files_with_components = {}
                        for comp_name in component_list:
                            if comp_name in components:
                                file_path = components[comp_name].relative_path
                                if file_path not in files_with_components:
                                    files_with_components[file_path] = []
                                files_with_components[file_path].append(comp_name)

                        logger.info(f"│  │  └─ Files: {len(files_with_components)}")
                        for file_path, comps in list(files_with_components.items())[:3]:
                            logger.debug(f"│  │     ├─ {file_path} ({len(comps)} component{'s' if len(comps) > 1 else ''})")
                        if len(files_with_components) > 3:
                            logger.debug(f"│  │     └─ ... and {len(files_with_components) - 3} more files")

                        logger.debug(f"│  │  └─ Calling LLM for leaf module documentation...")
                        import time
                        start_time = time.time()

                        # HIERARCHICAL OUTPUT: Create nested directory based on module_path
                        nested_working_dir = self._get_nested_working_dir(working_dir, module_path)
                        file_manager.ensure_directory(nested_working_dir)

                        final_module_tree = await self.agent_orchestrator.process_module(
                            module_name, components, module_info["components"], module_path, nested_working_dir
                        )
                        elapsed = time.time() - start_time
                        logger.info(f"│  │     └─ ✅ Generated in {elapsed:.2f}s")
                    else:
                        logger.info(f"│  ├─ [{idx}/{len(processing_order)}] 📁 Parent module: {module_key}")
                        logger.info(f"│  │  ├─ Children: {len(module_info.get('children', {}))} sub-modules")
                        logger.debug(f"│  │  └─ Calling LLM for parent module overview...")
                        import time
                        start_time = time.time()

                        # HIERARCHICAL OUTPUT: Create nested directory based on module_path
                        nested_working_dir = self._get_nested_working_dir(working_dir, module_path)
                        file_manager.ensure_directory(nested_working_dir)

                        final_module_tree = await self.generate_parent_module_docs(
                            module_path, nested_working_dir
                        )
                        elapsed = time.time() - start_time
                        logger.info(f"│  │     └─ ✅ Generated in {elapsed:.2f}s")

                    processed_modules.add(module_key)

                except Exception as e:
                    logger.error(f"│  ├─ [{idx}/{len(processing_order)}] ❌ Failed: {module_key}")
                    logger.error(f"│  │  └─ Error: {str(e)}")
                    logger.error(f"│  │  └─ Traceback:\n{traceback.format_exc()}")
                    # Continue processing other modules (graceful degradation)
                    continue

            # Generate repo overview
            logger.info(f"├─ 📚 Generating repository overview...")
            import time
            start_time = time.time()
            final_module_tree = await self.generate_parent_module_docs(
                [], working_dir
            )
            elapsed = time.time() - start_time
            logger.info(f"│  └─ ✅ Repository overview generated in {elapsed:.2f}s")
        else:
            logger.info(f"└─ ⚡ Small repository: Processing entire repo in single pass")
            repo_name = os.path.basename(os.path.normpath(self.config.repo_path))
            logger.info(f"   ├─ Repository name: {repo_name}")
            logger.info(f"   ├─ Components: {len(components)}")
            logger.info(f"   └─ Leaf nodes: {len(leaf_nodes)}")

            logger.debug(f"   └─ Calling LLM for complete repository documentation...")
            import time
            start_time = time.time()
            final_module_tree = await self.agent_orchestrator.process_module(
                repo_name, components, leaf_nodes, [], working_dir
            )
            elapsed = time.time() - start_time
            logger.info(f"      └─ ✅ Generated in {elapsed:.2f}s")

            # save final_module_tree to module_tree.json
            file_manager.save_json(final_module_tree, os.path.join(working_dir, MODULE_TREE_FILENAME))
            logger.debug(f"   └─ Saved module tree to {MODULE_TREE_FILENAME}")

            # rename repo_name.md to overview.md
            repo_overview_path = os.path.join(working_dir, f"{repo_name}.md")
            if os.path.exists(repo_overview_path):
                os.rename(repo_overview_path, os.path.join(working_dir, OVERVIEW_FILENAME))
                logger.debug(f"   └─ Renamed {repo_name}.md to {OVERVIEW_FILENAME}")

        logger.info(f"└─ ✅ Module documentation generation complete")
        return working_dir

    async def generate_parent_module_docs(self, module_path: List[str], 
                                        working_dir: str) -> Dict[str, Any]:
        """Generate documentation for a parent module based on its children's documentation."""
        module_name = module_path[-1] if len(module_path) >= 1 else os.path.basename(os.path.normpath(self.config.repo_path))

        logger.info(f"Generating parent documentation for: {module_name}")
        
        # Load module tree
        module_tree_path = os.path.join(working_dir, MODULE_TREE_FILENAME)
        module_tree = file_manager.load_json(module_tree_path)

        # check if overview docs already exists
        overview_docs_path = os.path.join(working_dir, OVERVIEW_FILENAME)
        if os.path.exists(overview_docs_path):
            logger.info(f"✓ Overview docs already exists at {overview_docs_path}")
            return module_tree

        # check if parent docs already exists
        parent_docs_path = os.path.join(working_dir, f"{module_name if len(module_path) >= 1 else OVERVIEW_FILENAME.replace('.md', '')}.md")
        if os.path.exists(parent_docs_path):
            logger.info(f"✓ Parent docs already exists at {parent_docs_path}")
            return module_tree

        # Create repo structure with 1-depth children docs and target indicator
        repo_structure = self.build_overview_structure(module_tree, module_path, working_dir)

        # FIXED: Use formatting functions instead of .format()
        # repo_structure is JSON which contains curly braces that .format() would interpret
        repo_structure_json = json.dumps(repo_structure, indent=4)

        logger.info("📄 Generating Parent Module Documentation")
        logger.info(f"   ├─ Module name: {module_name}")
        logger.info(f"   ├─ Module path: {' > '.join(module_path) if module_path else '(repository overview)'}")
        logger.info(f"   ├─ Repo structure JSON: {len(repo_structure_json)} chars")
        logger.info(f"   └─ Prompt type: {'MODULE_OVERVIEW' if len(module_path) >= 1 else 'REPO_OVERVIEW'}")
        logger.info("")

        prompt = format_module_overview_prompt(
            module_name,
            repo_structure_json
        ) if len(module_path) >= 1 else format_repo_overview_prompt(
            module_name,
            repo_structure_json
        )

        logger.info("🤖 Calling documentation generation LLM for parent module")
        logger.info(f"   ├─ Model: {self.config.main_model}")
        logger.info(f"   └─ Generating overview documentation...")
        logger.info("")

        try:
            parent_docs = call_llm(prompt, self.config)

            # Parse and save parent documentation
            # Handle case where LLM doesn't wrap response in <OVERVIEW> tags
            if "<OVERVIEW>" in parent_docs and "</OVERVIEW>" in parent_docs:
                parent_content = parent_docs.split("<OVERVIEW>")[1].split("</OVERVIEW>")[0].strip()
            else:
                # Use the entire response if no tags present
                logger.warning(f"LLM response missing <OVERVIEW> tags for {module_name}, using full response")
                parent_content = parent_docs.strip()

            file_manager.save_text(parent_content, parent_docs_path)

            logger.debug(f"Successfully generated parent documentation for: {module_name}")
            return module_tree

        except Exception as e:
            logger.error(f"Error generating parent documentation for {module_name}: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
    
    async def run(self) -> None:
        """Run the complete documentation generation process using dynamic programming."""
        try:
            # Build dependency graph
            components, leaf_nodes = self.graph_builder.build_dependency_graph()

            logger.debug(f"Found {len(leaf_nodes)} leaf nodes")
            # logger.debug(f"Leaf nodes:\n{'\n'.join(sorted(leaf_nodes)[:200])}")
            # exit()
            
            # Cluster modules
            working_dir = os.path.abspath(self.config.docs_dir)
            file_manager.ensure_directory(working_dir)
            first_module_tree_path = os.path.join(working_dir, FIRST_MODULE_TREE_FILENAME)
            module_tree_path = os.path.join(working_dir, MODULE_TREE_FILENAME)
            
            # Check if module tree exists
            if os.path.exists(first_module_tree_path):
                logger.debug(f"Module tree found at {first_module_tree_path}")
                module_tree = file_manager.load_json(first_module_tree_path)
            else:
                logger.debug(f"Module tree not found at {module_tree_path}, clustering modules")
                module_tree = cluster_modules(leaf_nodes, components, self.config)
                file_manager.save_json(module_tree, first_module_tree_path)

            # === SYNTHETIC_MODULE_PATCH: Prevent context overflow ===
            # If module_tree is empty but we have leaf nodes, create synthetic modules
            # This prevents the "whole repo" fallback that exceeds API context limits
            # IMPORTANT: Runs AFTER loading cached file too (fixes cache bypass bug)
            # See: https://github.com/flamingo-stack/CodeWiki - forked with this fix
            if len(module_tree) == 0 and len(leaf_nodes) > 0:
                logger.warning("Module tree is empty - creating synthetic modules to prevent context overflow")
                synthetic_modules = {}

                # Group leaf nodes by their top-level directory for semantic naming
                dir_groups: Dict[str, List[str]] = {}
                for leaf_node in leaf_nodes:
                    if leaf_node in components:
                        rel_path = components[leaf_node].relative_path
                        # Extract top-level directory (e.g., "openframe-api/src/..." -> "openframe-api")
                        parts = rel_path.split('/')
                        top_dir = parts[0] if len(parts) > 1 else "root"
                        # Sanitize directory name for use as module name
                        top_dir = top_dir.replace('-', '_').replace('.', '_')
                        if top_dir not in dir_groups:
                            dir_groups[top_dir] = []
                        dir_groups[top_dir].append(leaf_node)
                    else:
                        # Fallback for components not in dict
                        if "misc" not in dir_groups:
                            dir_groups["misc"] = []
                        dir_groups["misc"].append(leaf_node)

                # Create modules from directory groups
                for dir_name, dir_leaf_nodes in dir_groups.items():
                    module_name = dir_name
                    # Handle both Node objects and strings (leaf_nodes can be either)
                    if dir_leaf_nodes and dir_leaf_nodes[0] in components:
                        component_names = list(dir_leaf_nodes)
                    else:
                        component_names = list(dir_leaf_nodes)
                    synthetic_modules[module_name] = {
                        "name": module_name,
                        "components": component_names,
                        "leaf_nodes": dir_leaf_nodes,
                        "children": {}  # Required for module tree traversal
                    }

                module_tree = synthetic_modules
                logger.info(f"Created {len(module_tree)} synthetic modules based on directory structure: {list(module_tree.keys())}")
                # Update the cached file with synthetic modules
                file_manager.save_json(module_tree, first_module_tree_path)
            # === END SYNTHETIC_MODULE_PATCH ===
            
            file_manager.save_json(module_tree, module_tree_path)
            
            logger.debug(f"Grouped components into {len(module_tree)} modules")
            
            # Generate module documentation using dynamic programming approach
            # This processes leaf modules first, then parent modules
            working_dir = await self.generate_module_documentation(components, leaf_nodes)
            
            # Create documentation metadata
            self.create_documentation_metadata(working_dir, components, len(leaf_nodes))
            
            logger.debug(f"Documentation generation completed successfully using dynamic programming!")
            logger.debug(f"Processing order: leaf modules → parent modules → repository overview")
            logger.debug(f"Documentation saved to: {working_dir}")
            
        except Exception as e:
            logger.error(f"Documentation generation failed: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise