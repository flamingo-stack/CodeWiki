import os
import json
import logging
import argparse
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Optional, Any, Union
from pathlib import Path
import re

from codewiki.src.be.dependency_analyzer.analysis.analysis_service import AnalysisService
from codewiki.src.be.dependency_analyzer.models.core import Node


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class DependencyParser:
    """Parser for extracting code components from multi-language repositories."""

    def __init__(self, repo_path: Union[str, List[str]], include_patterns: List[str] = None, exclude_patterns: List[str] = None):
        """
        Initialize the dependency parser.

        Args:
            repo_path: Path to the repository or list of paths to multiple repositories
            include_patterns: File patterns to include (e.g., ["*.cs", "*.py"])
            exclude_patterns: File/directory patterns to exclude (e.g., ["*Tests*"])
        """
        # Support both single path (str) and multiple paths (List[str])
        if isinstance(repo_path, str):
            self.repo_paths = [os.path.abspath(repo_path)]
            self.repo_path = self.repo_paths[0]  # Maintain backward compatibility
        else:
            self.repo_paths = [os.path.abspath(p) for p in repo_path]
            self.repo_path = self.repo_paths[0]  # Default to first path for backward compat

        self.components: Dict[str, Node] = {}
        self.modules: Set[str] = set()
        self.include_patterns = include_patterns
        self.exclude_patterns = exclude_patterns

        self.analysis_service = AnalysisService()

    def parse_repository(self, filtered_folders: List[str] = None) -> Dict[str, Node]:
        """
        Parse repository or repositories and extract components.
        If multiple paths were provided, components are namespaced by source directory.

        Args:
            filtered_folders: Optional list of folders to filter

        Returns:
            Dictionary mapping component IDs to Node objects
        """
        logger.info("🔍 Stage 2: AST Parsing & Dependency Analysis")
        logger.info(f"├─ Repository paths: {len(self.repo_paths)}")

        if len(self.repo_paths) == 1:
            logger.info(f"│  └─ Single-path mode: {self.repo_paths[0]}")
            # Single path - maintain backward compatibility
            return self._parse_single_repository(self.repo_paths[0], filtered_folders)
        else:
            logger.info(f"│  └─ Multi-path mode: {len(self.repo_paths)} sources")
            # Multiple paths - use multi-path parsing
            return self._parse_multiple_repositories(filtered_folders)

    def _parse_single_repository(self, repo_path: str, filtered_folders: List[str] = None) -> Dict[str, Node]:
        """Parse a single repository (backward compatible)."""
        logger.info(f"📂 Parsing repository: {repo_path}")

        # Log custom patterns if set
        if self.include_patterns:
            logger.info(f"├─ Custom include patterns: {', '.join(self.include_patterns)}")
        if self.exclude_patterns:
            logger.info(f"├─ Custom exclude patterns: {', '.join(self.exclude_patterns)}")

        logger.info("├─ Step 2.1: Analyzing file structure...")
        structure_result = self.analysis_service._analyze_structure(
            repo_path,
            include_patterns=self.include_patterns,
            exclude_patterns=self.exclude_patterns
        )
        logger.info(f"│  └─ Found {structure_result.get('summary', {}).get('total_files', 0)} files to analyze")

        logger.info("├─ Step 2.2: Building call graph...")
        call_graph_result = self.analysis_service._analyze_call_graph(
            structure_result["file_tree"],
            repo_path
        )
        logger.info(f"│  ├─ Extracted {len(call_graph_result.get('functions', []))} functions/classes")
        logger.info(f"│  └─ Found {len(call_graph_result.get('relationships', []))} relationships")

        logger.info("├─ Step 2.3: Building component graph...")
        self._build_components_from_analysis(call_graph_result)

        logger.info(f"└─ ✅ AST parsing complete:")
        logger.info(f"   ├─ Total components: {len(self.components)}")
        logger.info(f"   └─ Total modules: {len(self.modules)}")
        return self.components

    def _parse_multiple_repositories(self, filtered_folders: List[str] = None) -> Dict[str, Node]:
        """
        Parse multiple repositories and merge components with namespace prefixes.

        Each repository gets a namespace prefix based on its directory name.
        Component IDs are prefixed to avoid collisions: {namespace}.{original_id}

        Returns:
            Dictionary of all components from all repositories with namespaced IDs
        """
        logger.info(f"🔍 Multi-path mode detected: analyzing {len(self.repo_paths)} source directories")
        logger.info(f"   ├─ Primary: {self.repo_paths[0]}")
        for i, path in enumerate(self.repo_paths[1:], 1):
            logger.info(f"   └─ Additional #{i}: {path}")

        all_components: Dict[str, Node] = {}
        namespace_mapping: Dict[str, str] = {}  # Maps original IDs to namespaced IDs

        for idx, repo_path in enumerate(self.repo_paths):
            # Create namespace from directory name
            namespace = self._get_namespace_from_path(repo_path)
            logger.info(f"\n📂 Analyzing path {idx+1}/{len(self.repo_paths)}: {repo_path}")
            logger.info(f"   └─ Namespace: '{namespace}'")

            # Log custom patterns if set
            if self.include_patterns:
                logger.info(f"Using custom include patterns: {self.include_patterns}")
            if self.exclude_patterns:
                logger.info(f"Using custom exclude patterns: {self.exclude_patterns}")

            # Analyze structure
            structure_result = self.analysis_service._analyze_structure(
                repo_path,
                include_patterns=self.include_patterns,
                exclude_patterns=self.exclude_patterns
            )

            # Analyze call graph
            call_graph_result = self.analysis_service._analyze_call_graph(
                structure_result["file_tree"],
                repo_path
            )

            # Build components with namespace (idx=0 is main repo, idx>0 is deps)
            repo_components = self._build_namespaced_components(
                call_graph_result,
                namespace,
                namespace_mapping,
                repo_index=idx
            )

            # Merge into all_components
            all_components.update(repo_components)

            logger.info(f"📊 Namespace '{namespace}': found {len(repo_components)} components")

            # Log component type breakdown for this namespace
            type_counts = {}
            for comp in repo_components.values():
                comp_type = comp.component_type
                type_counts[comp_type] = type_counts.get(comp_type, 0) + 1

            if type_counts:
                logger.info(f"   └─ Component types:")
                for comp_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
                    logger.info(f"      • {comp_type}: {count}")

        # Update cross-repository dependencies
        logger.info(f"\n🔗 Resolving cross-namespace dependencies...")
        cross_deps_count = self._resolve_cross_namespace_dependencies(all_components, namespace_mapping)
        if cross_deps_count > 0:
            logger.info(f"   └─ ✓ Resolved {cross_deps_count} cross-namespace dependencies")
        else:
            logger.info(f"   └─ No cross-namespace dependencies found")

        self.components = all_components
        logger.info(f"\n📊 Multi-path analysis complete:")
        logger.info(f"   ├─ Total components: {len(all_components)}")
        logger.info(f"   ├─ Total modules: {len(self.modules)}")
        logger.info(f"   └─ Namespaces: {len(self.repo_paths)}")

        return self.components

    def _get_namespace_from_path(self, repo_path: str) -> str:
        """
        Generate a namespace prefix from a repository path.

        Args:
            repo_path: Absolute path to repository

        Returns:
            Namespace string (e.g., 'openframe-frontend', 'ui-kit')
        """
        # Use the last directory name as namespace
        return os.path.basename(repo_path.rstrip(os.sep))

    def _build_namespaced_components(
        self,
        call_graph_result: Dict,
        namespace: str,
        namespace_mapping: Dict[str, str],
        repo_index: int = 0
    ) -> Dict[str, Node]:
        """
        Build components with namespace prefixes.

        Args:
            call_graph_result: Result from call graph analysis
            namespace: Namespace prefix for this repository
            namespace_mapping: Global mapping of original IDs to namespaced IDs
            repo_index: Index of this repository (0 = main, >0 = deps)

        Returns:
            Dictionary of namespaced components
        """
        functions = call_graph_result.get("functions", [])
        relationships = call_graph_result.get("relationships", [])

        components: Dict[str, Node] = {}

        # First pass: Create components with namespaced IDs
        for func_dict in functions:
            original_id = func_dict.get("id", "")
            if not original_id:
                continue

            # Create FQDN (namespaced component ID)
            fqdn = f"{namespace}.{original_id}"

            # Store mapping for dependency resolution
            namespace_mapping[original_id] = fqdn

            # Create node with FQDN as id and metadata fields
            node = Node(
                id=fqdn,  # FQDN as primary identifier
                name=func_dict.get("name", ""),
                component_type=func_dict.get("component_type", func_dict.get("node_type", "function")),
                file_path=func_dict.get("file_path", ""),
                relative_path=func_dict.get("relative_path", ""),
                source_code=func_dict.get("source_code", func_dict.get("code_snippet", "")),
                start_line=func_dict.get("start_line", 0),
                end_line=func_dict.get("end_line", 0),
                has_docstring=func_dict.get("has_docstring", bool(func_dict.get("docstring", ""))),
                docstring=func_dict.get("docstring", "") or "",
                parameters=func_dict.get("parameters", []),
                node_type=func_dict.get("node_type", "function"),
                base_classes=func_dict.get("base_classes"),
                class_name=func_dict.get("class_name"),
                display_name=func_dict.get("display_name", ""),
                component_id=fqdn,
                # FQDN metadata fields
                short_id=original_id,
                namespace=namespace,
                is_from_deps=(repo_index > 0)
            )

            # Dictionary key is FQDN
            components[fqdn] = node

            # Track module (with namespace)
            if "." in original_id:
                module_parts = original_id.split(".")[:-1]
                module_path = ".".join(module_parts)
                if module_path:
                    self.modules.add(f"{namespace}.{module_path}")

        # Second pass: Add dependencies within this namespace
        for rel_dict in relationships:
            caller_id = rel_dict.get("caller", "")
            callee_id = rel_dict.get("callee", "")

            # Map to namespaced IDs
            namespaced_caller = namespace_mapping.get(caller_id)
            namespaced_callee = namespace_mapping.get(callee_id)

            if namespaced_caller and namespaced_caller in components:
                if namespaced_callee:
                    components[namespaced_caller].depends_on.add(namespaced_callee)

        return components

    def _resolve_cross_namespace_dependencies(
        self,
        all_components: Dict[str, Node],
        namespace_mapping: Dict[str, str]
    ) -> int:
        """
        Resolve dependencies that cross namespace boundaries.

        This handles cases where one component in namespace A depends on
        a component in namespace B.

        Args:
            all_components: All components from all repositories
            namespace_mapping: Mapping of original IDs to namespaced IDs

        Returns:
            Number of cross-namespace dependencies resolved
        """
        cross_deps_resolved = 0

        # For each component, check if any dependencies need cross-namespace resolution
        for component_id, component in sorted(all_components.items()):  # ✅ SORT for determinism
            resolved_deps = set()

            for dep_id in component.depends_on:
                # If dependency exists in all_components, it's already resolved
                if dep_id in all_components:
                    resolved_deps.add(dep_id)
                else:
                    # Try to find it by name match across namespaces
                    dep_name = dep_id.split(".")[-1]
                    for other_id, other_component in sorted(all_components.items()):  # ✅ SORT for determinism
                        if other_component.name == dep_name and other_id != component_id:
                            # Extract namespaces to check if it's cross-namespace
                            source_namespace = component_id.split(".")[0]
                            target_namespace = other_id.split(".")[0]
                            if source_namespace != target_namespace:
                                logger.debug(f"   ├─ Cross-namespace dependency: {component_id} → {other_id}")
                                cross_deps_resolved += 1
                            resolved_deps.add(other_id)
                            break
                    else:
                        # Keep original if not resolved
                        resolved_deps.add(dep_id)

            component.depends_on = resolved_deps

        return cross_deps_resolved
    
    def _build_components_from_analysis(self, call_graph_result: Dict):
        functions = call_graph_result.get("functions", [])
        relationships = call_graph_result.get("relationships", [])

        component_id_mapping = {}

        # Compute namespace from repo path
        namespace = self._get_namespace_from_path(self.repo_path)

        for func_dict in functions:
            original_id = func_dict.get("id", "")
            if not original_id:
                continue

            # Construct FQDN: {namespace}.{original_id}
            fqdn = f"{namespace}.{original_id}"

            node = Node(
                id=fqdn,  # FQDN as primary identifier
                name=func_dict.get("name", ""),
                component_type=func_dict.get("component_type", func_dict.get("node_type", "function")),
                file_path=func_dict.get("file_path", ""),
                relative_path=func_dict.get("relative_path", ""),
                source_code=func_dict.get("source_code", func_dict.get("code_snippet", "")),
                start_line=func_dict.get("start_line", 0),
                end_line=func_dict.get("end_line", 0),
                has_docstring=func_dict.get("has_docstring", bool(func_dict.get("docstring", ""))),
                docstring=func_dict.get("docstring", "") or "",
                parameters=func_dict.get("parameters", []),
                node_type=func_dict.get("node_type", "function"),
                base_classes=func_dict.get("base_classes"),
                class_name=func_dict.get("class_name"),
                display_name=func_dict.get("display_name", ""),
                component_id=fqdn,
                # FQDN metadata fields
                short_id=original_id,
                namespace=namespace,
                is_from_deps=False  # Single-path mode = main repo
            )

            # Dictionary key is FQDN
            self.components[fqdn] = node

            # Update mapping for dependency resolution
            component_id_mapping[original_id] = fqdn
            component_id_mapping[fqdn] = fqdn
            legacy_id = f"{func_dict.get('file_path', '')}:{func_dict.get('name', '')}"
            if legacy_id and legacy_id != fqdn:
                component_id_mapping[legacy_id] = fqdn

            if "." in original_id:
                module_parts = original_id.split(".")[:-1]
                module_path = ".".join(module_parts)
                if module_path:
                    # Store module with namespace
                    self.modules.add(f"{namespace}.{module_path}")
        
        processed_relationships = 0
        for rel_dict in relationships:
            caller_id = rel_dict.get("caller", "")
            callee_id = rel_dict.get("callee", "")
            is_resolved = rel_dict.get("is_resolved", False)
            
            caller_component_id = component_id_mapping.get(caller_id)
            
            callee_component_id = component_id_mapping.get(callee_id)
            if not callee_component_id:
                for comp_id, comp_node in sorted(self.components.items()):  # ✅ SORT for determinism
                    if comp_node.name == callee_id:
                        callee_component_id = comp_id
                        break
            
            if caller_component_id and caller_component_id in self.components:
                if callee_component_id:
                    self.components[caller_component_id].depends_on.add(callee_component_id)
                    processed_relationships += 1
    
    def _determine_component_type(self, func_dict: Dict) -> str:
        if func_dict.get("is_method", False):
            return "method"
        
        node_type = func_dict.get("node_type", "")
        if node_type in ["class", "interface", "struct", "enum", "record", "abstract class", "annotation", "delegate"]:
            return node_type
            
        return "function"
    
    def _file_to_module_path(self, file_path: str) -> str:
        path = file_path
        extensions = ['.py', '.js', '.ts', '.java', '.cs', '.cpp', '.hpp', '.h', '.c', '.tsx', '.jsx', '.cc', '.mjs', '.cxx', '.cc', '.cjs']
        for ext in extensions:
            if path.endswith(ext):
                path = path[:-len(ext)]
                break
        return path.replace(os.path.sep, ".")
    
    def save_dependency_graph(self, output_path: str):
        result = {}
        for component_id in sorted(self.components.keys()):  # ✅ SORT for determinism
            component = self.components[component_id]
            component_dict = component.model_dump()
            if 'depends_on' in component_dict and isinstance(component_dict['depends_on'], set):
                component_dict['depends_on'] = sorted(list(component_dict['depends_on']))  # ✅ SORT for determinism
            result[component_id] = component_dict
        
        dir_name = os.path.dirname(output_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        logger.debug(f"Saved {len(self.components)} components to {output_path}")
        return result
