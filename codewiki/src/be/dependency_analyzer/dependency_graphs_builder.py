from typing import Dict, List, Any
import os
from codewiki.src.config import Config
from codewiki.src.be.dependency_analyzer.ast_parser import DependencyParser
from codewiki.src.be.dependency_analyzer.topo_sort import build_graph_from_components, get_leaf_nodes
from codewiki.src.be.dependency_analyzer.validation import validate_graph_completeness
from codewiki.src.utils import file_manager

import logging
logger = logging.getLogger(__name__)


class DependencyGraphBuilder:
    """Handles dependency analysis and graph building."""
    
    def __init__(self, config: Config):
        self.config = config
    
    def build_dependency_graph(self) -> tuple[Dict[str, Any], List[str]]:
        """
        Build and save dependency graph, returning components and leaf nodes.
        
        Returns:
            Tuple of (components, leaf_nodes)
        """
        # Ensure output directory exists
        file_manager.ensure_directory(self.config.dependency_graph_dir)

        # Prepare dependency graph path
        repo_name = os.path.basename(os.path.normpath(self.config.repo_path))
        sanitized_repo_name = ''.join(c if c.isalnum() else '_' for c in repo_name)
        dependency_graph_path = os.path.join(
            self.config.dependency_graph_dir, 
            f"{sanitized_repo_name}_dependency_graph.json"
        )
        filtered_folders_path = os.path.join(
            self.config.dependency_graph_dir, 
            f"{sanitized_repo_name}_filtered_folders.json"
        )

        # Get custom include/exclude patterns from config
        include_patterns = self.config.include_patterns if self.config.include_patterns else None
        exclude_patterns = self.config.exclude_patterns if self.config.exclude_patterns else None

        # Build list of paths to analyze
        repo_paths = self.config.all_source_paths

        # Log multi-path mode if enabled
        if self.config.is_multi_path_mode():
            logger.info(f"🔍 Multi-path mode enabled: analyzing {len(repo_paths)} source paths")
            logger.info(f"   ├─ Primary: {repo_paths[0]}")
            for i, path in enumerate(repo_paths[1:], 1):
                logger.info(f"   └─ Additional #{i}: {path}")
        else:
            logger.info(f"📁 Single-path mode: analyzing {repo_paths[0]}")

        parser = DependencyParser(
            repo_paths if len(repo_paths) > 1 else repo_paths[0],
            include_patterns=include_patterns,
            exclude_patterns=exclude_patterns
        )

        filtered_folders = None
        # if os.path.exists(filtered_folders_path):
        #     logger.debug(f"Loading filtered folders from {filtered_folders_path}")
        #     filtered_folders = file_manager.load_json(filtered_folders_path)
        # else:
        #     # Parse repository
        #     filtered_folders = parser.filter_folders()
        #     # Save filtered folders
        #     file_manager.save_json(filtered_folders, filtered_folders_path)

        # Parse repository
        logger.info("🔍 Parsing repository files...")
        components = parser.parse_repository(filtered_folders)
        logger.info(f"   └─ Parsed {len(components)} components total")

        # Log component type breakdown
        type_counts = {}
        for comp in components.values():
            comp_type = comp.component_type
            type_counts[comp_type] = type_counts.get(comp_type, 0) + 1

        logger.info("   └─ Component types found:")
        for comp_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
            logger.info(f"      • {comp_type}: {count}")

        # Save dependency graph
        parser.save_dependency_graph(dependency_graph_path)
        logger.info(f"   └─ Saved dependency graph to: {dependency_graph_path}")
        
        # Build graph for traversal
        graph = build_graph_from_components(components)

        # ✅ Post-build validation - verify graph completeness
        validate_graph_completeness(components, graph)

        # Get leaf nodes
        leaf_nodes = get_leaf_nodes(graph, components)

        # check if leaf_nodes are in components, only keep the ones that are in components
        # and type is one of the following: class, interface, struct (or function for C-based projects)
        
        # Determine if we should include functions based on available component types
        available_types = set()
        for comp in components.values():
            available_types.add(comp.component_type)
        
        # Valid types for leaf nodes - include functions for C-based codebases
        valid_types = {"class", "interface", "struct"}
        # If no classes/interfaces/structs are found, include functions
        if not available_types.intersection(valid_types):
            valid_types.add("function")
        
        logger.info(f"🌿 Filtering leaf nodes (total: {len(leaf_nodes)})...")
        logger.info(f"   └─ Valid types for this codebase: {', '.join(sorted(valid_types))}")

        keep_leaf_nodes = []
        skipped_invalid = 0
        skipped_type = 0
        skipped_not_found = 0

        for leaf_node in leaf_nodes:
            # Skip any leaf nodes that are clearly error strings or invalid identifiers
            if not isinstance(leaf_node, str) or leaf_node.strip() == "" or any(err_keyword in leaf_node.lower() for err_keyword in ['error', 'exception', 'failed', 'invalid']):
                skipped_invalid += 1
                logger.warning(
                    f"Skipping invalid leaf node identifier: '{leaf_node}'\n"
                    f"   └─ Reason: Contains error keywords or is empty/invalid string\n"
                    f"   └─ This likely indicates a parsing error or malformed code"
                )
                continue

            if leaf_node in components:
                if components[leaf_node].component_type in valid_types:
                    keep_leaf_nodes.append(leaf_node)
                else:
                    skipped_type += 1
                    logger.debug(f"Skipping {leaf_node}: type '{components[leaf_node].component_type}' not in valid types")
            else:
                skipped_not_found += 1
                logger.warning(
                    f"Leaf node '{leaf_node}' not found in components\n"
                    f"   └─ Reason: Node exists in dependency graph but component wasn't parsed\n"
                    f"   └─ Possible causes:\n"
                    f"      • File was excluded after initial scan\n"
                    f"      • Component parsing failed for this specific item\n"
                    f"      • External dependency referenced in code"
                )

        logger.info(f"📊 Leaf node filtering complete:")
        logger.info(f"   ├─ Kept: {len(keep_leaf_nodes)} nodes")
        logger.info(f"   ├─ Skipped (invalid identifier): {skipped_invalid}")
        logger.info(f"   ├─ Skipped (wrong type): {skipped_type}")
        logger.info(f"   └─ Skipped (not found): {skipped_not_found}")

        return components, keep_leaf_nodes