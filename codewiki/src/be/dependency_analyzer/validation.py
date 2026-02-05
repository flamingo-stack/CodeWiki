"""
Dependency graph validation and bulletproof checks.

This module provides pre-flight and post-build validation to ensure
dependency graph integrity and catch missing components early.
"""

import logging
import os
from typing import Dict, Set, List, Any
from collections import defaultdict

logger = logging.getLogger(__name__)


def validate_components_before_clustering(
    components: Dict[str, Any],
    leaf_nodes: List[str]
) -> bool:
    """
    Pre-flight validation: Ensure all leaf nodes reference actual components.

    This validation catches hallucinated or missing component references BEFORE
    clustering begins, preventing broken dependency graphs.

    Args:
        components: All extracted components (dictionary with component IDs as keys)
        leaf_nodes: Proposed leaf nodes for clustering

    Returns:
        True if validation passes (all leaf nodes exist in components)

    Raises:
        ValueError: If strict mode enabled and missing components found
    """
    logger.info("🔍 Pre-Flight Validation - Component Existence Check")

    component_ids = set(components.keys())
    missing_components = []

    for leaf_node in leaf_nodes:
        if leaf_node not in component_ids:
            missing_components.append(leaf_node)
            logger.error(f"   ❌ Missing component: {leaf_node}")

    if missing_components:
        logger.error(
            f"❌ Pre-flight validation FAILED: {len(missing_components)} missing components"
        )
        logger.error("   These components don't exist but are referenced in the graph:")
        for comp_id in sorted(missing_components[:20]):  # Show first 20
            logger.error(f"      - {comp_id}")

        if len(missing_components) > 20:
            logger.error(f"      ... and {len(missing_components) - 20} more")

        # Check if strict mode is enabled
        strict_mode = os.environ.get('CODEWIKI_STRICT_MODE', 'false').lower() == 'true'
        if strict_mode:
            raise ValueError(
                f"Pre-flight validation failed: {len(missing_components)} missing components. "
                f"Set CODEWIKI_STRICT_MODE=false to continue with warnings."
            )
        return False

    logger.info(f"   ✅ All {len(leaf_nodes)} leaf nodes validated")
    return True


def validate_graph_completeness(
    components: Dict[str, Any],
    graph: Dict[str, Set[str]]
) -> bool:
    """
    Post-build validation: Verify graph completeness and integrity.

    This validation ensures:
    1. All graph nodes exist as components
    2. All dependency edges point to existing components
    3. No dangling references or broken edges

    Args:
        components: All components (dictionary with component IDs as keys)
        graph: Dependency graph (node ID -> set of dependency IDs)

    Returns:
        True if graph is complete and valid

    Raises:
        ValueError: If strict mode enabled and validation fails
    """
    logger.info("🔍 Post-Build Validation - Graph Completeness")

    component_ids = set(components.keys())
    graph_nodes = set(graph.keys())

    # Check 1: All graph nodes exist as components
    missing_in_components = graph_nodes - component_ids
    if missing_in_components:
        logger.error(
            f"   ❌ {len(missing_in_components)} graph nodes missing from components:"
        )
        for node_id in sorted(list(missing_in_components)[:10]):  # Show first 10
            logger.error(f"      - {node_id}")
        if len(missing_in_components) > 10:
            logger.error(f"      ... and {len(missing_in_components) - 10} more")

    # Check 2: All dependencies exist
    broken_edges = []
    for node, deps in graph.items():
        for dep in deps:
            if dep not in component_ids:
                broken_edges.append((node, dep))

    if broken_edges:
        logger.error(f"   ❌ {len(broken_edges)} broken dependency edges:")
        for src, tgt in sorted(broken_edges[:10]):  # Show first 10
            logger.error(f"      - {src} → {tgt} (target missing)")
        if len(broken_edges) > 10:
            logger.error(f"      ... and {len(broken_edges) - 10} more")

    success = len(missing_in_components) == 0 and len(broken_edges) == 0

    if success:
        logger.info(f"   ✅ Graph is complete ({len(graph_nodes)} nodes)")
    else:
        logger.error("   ❌ Graph validation FAILED")

        # Check if strict mode is enabled
        strict_mode = os.environ.get('CODEWIKI_STRICT_MODE', 'false').lower() == 'true'
        if strict_mode:
            raise ValueError(
                f"Post-build validation failed: "
                f"{len(missing_in_components)} missing components, "
                f"{len(broken_edges)} broken edges. "
                f"Set CODEWIKI_STRICT_MODE=false to continue with warnings."
            )

    return success


def validate_determinism(
    components: Dict[str, Any],
    graph: Dict[str, Set[str]]
) -> str:
    """
    Generate deterministic hash of graph for validation.

    This hash can be used to verify that repeated runs with the same input
    produce identical output (determinism check).

    Args:
        components: All components
        graph: Dependency graph

    Returns:
        SHA256 hash of the sorted graph structure
    """
    import hashlib
    import json

    # Create deterministic representation
    graph_repr = {}
    for node_id in sorted(graph.keys()):
        graph_repr[node_id] = sorted(list(graph[node_id]))

    # Serialize to JSON with sorted keys
    json_str = json.dumps(graph_repr, sort_keys=True, indent=None)

    # Compute hash
    hash_obj = hashlib.sha256(json_str.encode('utf-8'))
    return hash_obj.hexdigest()
