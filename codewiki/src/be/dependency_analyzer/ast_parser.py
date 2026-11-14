"""AST parsing and dependency graph construction for a repository.

This module implements the core dependency analysis pipeline stage that:
- Parses the repository into structural and call-graph representations
  using the AnalysisService. Only the repository itself is parsed: code it
  imports from other repositories is looked up on demand by the writing
  agents through the hub's code-graph tools (see agent_tools/code_graph.py).
- Builds Node-based components keyed by fully-qualified domain names (FQDNs)
  in the canonical `module.path::ComponentName` format, namespaced by the
  repository's directory name, and tracks module membership for each one.
- Resolves dependency edges between components.
- Persists the resulting dependency graph to disk for downstream consumers
  (e.g., clustering, LLM-based summarization, and documentation generation).
"""
import os
import json
import logging
import argparse
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Optional, Any
from pathlib import Path
import re

from codewiki.src.be.dependency_analyzer.analysis.analysis_service import AnalysisService
from codewiki.src.be.dependency_analyzer.models.core import Node


logger = logging.getLogger(__name__)


class DependencyParser:
    """Parser for extracting code components from a multi-language repository."""

    def __init__(self, repo_path: str, include_patterns: List[str] = None, exclude_patterns: List[str] = None):
        """
        Initialize the dependency parser.

        Args:
            repo_path: Path to the repository
            include_patterns: File patterns to include (e.g., ["*.cs", "*.py"])
            exclude_patterns: File/directory patterns to exclude (e.g., ["*Tests*"])
        """
        self.repo_path = os.path.abspath(repo_path)

        self.components: Dict[str, Node] = {}
        self.modules: Set[str] = set()
        self.include_patterns = include_patterns
        self.exclude_patterns = exclude_patterns

        self.analysis_service = AnalysisService()

    def parse_repository(self, filtered_folders: List[str] = None) -> Dict[str, Node]:
        """
        Parse the repository and extract components.

        Args:
            filtered_folders: Optional list of folders to filter

        Returns:
            Dictionary mapping component IDs to Node objects
        """
        repo_path = self.repo_path
        logger.info("🔍 Stage 2: AST Parsing & Dependency Analysis")
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

    def _get_namespace_from_path(self, repo_path: str) -> str:
        """
        Generate a namespace prefix from a repository path.

        Args:
            repo_path: Absolute path to repository

        Returns:
            Namespace string: the repository directory's name
        """
        # Use the last directory name as namespace
        return os.path.basename(repo_path.rstrip(os.sep))

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

            # Construct FQDN: {namespace}::{original_id}
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
                namespace=namespace
            )

            # Dictionary key is FQDN
            self.components[fqdn] = node

            # Update mapping for dependency resolution
            component_id_mapping[original_id] = fqdn
            component_id_mapping[fqdn] = fqdn
            legacy_id = f"{func_dict.get('file_path', '')}:{func_dict.get('name', '')}"
            if legacy_id and legacy_id != fqdn:
                component_id_mapping[legacy_id] = fqdn

            # original_id is '<module.path>::<Name>' from the analyzers, so the
            # module path is everything before '::'. (The dot-split fallback is
            # for ids that predate the '::' separator.)
            module_path = (
                original_id.split("::")[0]
                if "::" in original_id
                else ".".join(original_id.split(".")[:-1])
            )
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

