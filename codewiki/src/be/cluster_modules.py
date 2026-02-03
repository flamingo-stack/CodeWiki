from typing import List, Dict, Any
from collections import defaultdict
import logging
import traceback
logger = logging.getLogger(__name__)

from codewiki.src.be.dependency_analyzer.models.core import Node
from codewiki.src.be.llm_services import call_llm
from codewiki.src.be.utils import count_tokens
from codewiki.src.config import Config
from codewiki.src.be.prompt_template import format_cluster_prompt


def format_potential_core_components(leaf_nodes: List[str], components: Dict[str, Node]) -> tuple[str, str]:
    """
    Format the potential core components into a string that can be used in the prompt.

    Args:
        leaf_nodes: List of component FQDNs (fully qualified domain names)
        components: Dictionary mapping FQDNs to Node objects

    Returns:
        Tuple of (potential_core_components, potential_core_components_with_code)
    """
    logger.debug(f"📋 Formatting components:")
    logger.debug(f"   ├─ Leaf nodes format: FQDN (e.g., 'main-repo.src/services/auth.py::AuthService')")
    logger.debug(f"   ├─ Components dict keys: FQDN (node.id)")
    logger.debug(f"   └─ Input: {len(leaf_nodes)} leaf nodes, {len(components)} components")

    # Filter out any invalid leaf nodes that don't exist in components
    valid_leaf_nodes = []
    skipped_count = 0
    for leaf_node in leaf_nodes:
        if leaf_node in components:
            valid_leaf_nodes.append(leaf_node)
        else:
            skipped_count += 1
            # Extract namespace from FQDN (e.g., "main-repo" from "main-repo.src/...")
            namespace = ""
            is_deps = False
            if '.' in leaf_node:
                namespace = leaf_node.split('.')[0]
                is_deps = namespace.startswith('deps/')

            # Extract file path if present
            file_hint = ""
            if '::' in leaf_node:
                file_part = leaf_node.split('::')[0]
                file_hint = f" (from {file_part})"

            logger.warning(
                f"Skipping invalid leaf node '{leaf_node}'{file_hint}\n"
                f"   ├─ FQDN format: {leaf_node}\n"
                f"   ├─ Namespace: {namespace or '(unknown)'}\n"
                f"   ├─ Source: {'dependency repo' if is_deps else 'main repo'}\n"
                f"   └─ Reason: Component not found in components dictionary\n"
                f"   └─ Possible causes:\n"
                f"      • File was excluded by filters (tests, specs, node_modules, etc.)\n"
                f"      • Parsing failed for this component\n"
                f"      • Component is from a dependency/external library\n"
                f"      • File extension not supported"
            )

    if skipped_count > 0:
        logger.info(f"📊 Leaf node filtering: {len(valid_leaf_nodes)} valid, {skipped_count} skipped ({len(leaf_nodes)} total)")
    
    #group leaf nodes by file
    leaf_nodes_by_file = defaultdict(list)
    for leaf_node in valid_leaf_nodes:
        leaf_nodes_by_file[components[leaf_node].relative_path].append(leaf_node)

    logger.debug(f"   ├─ Valid leaf nodes: {len(valid_leaf_nodes)}")
    logger.debug(f"   └─ Grouped into {len(leaf_nodes_by_file)} files")

    potential_core_components = ""
    potential_core_components_with_code = ""
    for file, leaf_nodes in dict(sorted(leaf_nodes_by_file.items())).items():
        potential_core_components += f"# {file}\n"
        potential_core_components_with_code += f"# {file}\n"
        for leaf_node in leaf_nodes:
            # leaf_node is FQDN format (e.g., "main-repo.src/services/auth.py::AuthService")
            potential_core_components += f"\t{leaf_node}\n"
            potential_core_components_with_code += f"\t{leaf_node}\n"
            potential_core_components_with_code += f"{components[leaf_node].source_code}\n"

    return potential_core_components, potential_core_components_with_code


def build_short_id_to_fqdn_map(components: Dict[str, Node]) -> Dict[str, str]:
    """
    Build mapping from short component IDs to FQDNs.

    This handles cases where LLM returns short IDs (e.g., "AuthService")
    instead of full FQDNs (e.g., "main-repo.src/auth.py::AuthService").

    Creates MULTIPLE mapping entries for each component to handle various
    LLM output formats (class name, package.class, full path, etc.).

    Args:
        components: Dictionary with FQDN keys and Node values

    Returns:
        Dictionary mapping short_id → fqdn
    """
    mapping = {}
    collisions = defaultdict(list)

    # DIAGNOSTIC: Track sample variants for debugging
    sample_variants = {}
    sample_count = 0

    for fqdn, node in components.items():
        # Strategy: Create multiple mapping entries for each component
        # This handles LLM returning different levels of specificity

        # Get base short_id from node
        short_id = getattr(node, 'short_id', None) or ""

        if not short_id:
            # Fallback: extract from FQDN
            # Handle both :: (file::class) and . (package.class) separators
            if '::' in fqdn:
                # Format: "namespace.path/file.ext::ClassName"
                after_colon = fqdn.split('::')[-1]
                # Handle nested classes: "ClassName.InnerClass" → "InnerClass"
                short_id = after_colon.split('.')[-1] if '.' in after_colon else after_colon
            else:
                # Format: "namespace.package.class.method"
                short_id = fqdn.split('.')[-1]

        # ENHANCEMENT: Create mappings for multiple formats
        # This significantly improves LLM output matching

        mapping_variants = set()
        mapping_variants.add(short_id)  # 1. Just class name: "LogDetails"

        # 2. Extract additional variants from FQDN
        parts = fqdn.replace('::', '.').split('.')

        # Add last 2 segments: "dto.LogDetails"
        if len(parts) >= 2:
            mapping_variants.add('.'.join(parts[-2:]))

        # Add last 3 segments: "openframe.dto.LogDetails"
        if len(parts) >= 3:
            mapping_variants.add('.'.join(parts[-3:]))

        # Add last 4 segments for deeply nested packages
        if len(parts) >= 4:
            mapping_variants.add('.'.join(parts[-4:]))

        # DIAGNOSTIC: Capture first 3 examples for debugging
        if sample_count < 3:
            sample_variants[fqdn] = list(mapping_variants)
            sample_count += 1

        # Add all variants to mapping
        for variant in mapping_variants:
            if variant and variant != fqdn:  # Don't map FQDN to itself
                if variant in mapping:
                    # Collision detected
                    collisions[variant].append(fqdn)
                    if mapping[variant] not in collisions[variant]:
                        collisions[variant].insert(0, mapping[variant])
                else:
                    mapping[variant] = fqdn

    # Log sample mappings for debugging
    logger.debug(f"📝 Sample mapping variants created:")
    for fqdn, variants in sample_variants.items():
        logger.debug(f"   FQDN: {fqdn}")
        for v in variants:
            logger.debug(f"      → '{v}'")

    # Log collisions
    if collisions:
        logger.debug(f"🔀 Short ID collisions detected:")
        for short_id, fqdns in collisions.items():
            logger.debug(f"   ├─ '{short_id}' maps to {len(fqdns)} components:")
            for fqdn in fqdns[:3]:  # Show first 3 only
                logger.debug(f"   │  └─ {fqdn}")
            if len(fqdns) > 3:
                logger.debug(f"   │  └─ ... and {len(fqdns) - 3} more")
        logger.debug(f"   └─ Using first match for each collision")

    logger.debug(f"📋 Built short_id → FQDN mapping: {len(mapping)} entries (from {len(components)} components)")
    return mapping


def cluster_modules(
    leaf_nodes: List[str],
    components: Dict[str, Node],
    config: Config,
    current_module_tree: dict[str, Any] = {},
    current_module_name: str = None,
    current_module_path: List[str] = []
) -> Dict[str, Any]:
    """
    Cluster the potential core components into modules.
    """
    logger.info("🗂️  Module Clustering Operation")
    logger.info(f"   ├─ Current module: {current_module_name or '(repository level)'}")
    logger.info(f"   ├─ Module path: {' > '.join(current_module_path) if current_module_path else '(root)'}")
    logger.info(f"   ├─ Leaf nodes to cluster: {len(leaf_nodes)}")
    logger.info(f"   └─ Components dictionary size: {len(components)} components")
    logger.info("")

    potential_core_components, potential_core_components_with_code = format_potential_core_components(leaf_nodes, components)

    token_count = count_tokens(potential_core_components_with_code)
    logger.info(f"   ├─ Potential components (with code): {token_count} tokens")
    logger.info(f"   ├─ Max token per module: {config.max_token_per_module}")

    if token_count <= config.max_token_per_module:
        logger.info(f"   └─ ⏭️  Skipping clustering - components fit in single module ({token_count} ≤ {config.max_token_per_module})")
        return {}

    logger.info(f"   └─ ✅ Proceeding with clustering - components exceed threshold")
    logger.info("")

    prompt = format_cluster_prompt(potential_core_components, current_module_tree, current_module_name)
    logger.info(f"🤖 Calling clustering LLM")
    logger.info(f"   ├─ Model: {config.cluster_model}")
    logger.info(f"   └─ Prompt assembled via format_cluster_prompt()")
    logger.info("")

    response = call_llm(prompt, config, model=config.cluster_model)

    logger.info(f"   ✅ Clustering LLM response received")
    logger.info(f"   ├─ Response length: {len(response)} chars")
    logger.info(f"   └─ Preview: {response[:150]}...")
    logger.info("")

    #parse the response
    try:
        if "<GROUPED_COMPONENTS>" not in response or "</GROUPED_COMPONENTS>" not in response:
            logger.error(f"Invalid LLM response format - missing component tags: {response[:200]}...")
            return {}

        response_content = response.split("<GROUPED_COMPONENTS>")[1].split("</GROUPED_COMPONENTS>")[0]
        module_tree = eval(response_content)

        if not isinstance(module_tree, dict):
            logger.error(f"Invalid module tree format - expected dict, got {type(module_tree)}")
            return {}

    except Exception as e:
        logger.error(f"Failed to parse LLM response: {e}. Response: {response[:200]}...")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {}

    # Build reverse mapping: short_id → FQDN
    logger.info(f"🔄 Normalizing component IDs in clustering response")
    short_to_fqdn = build_short_id_to_fqdn_map(components)

    # Normalize all component IDs in module_tree
    total_normalized = 0
    total_failed = 0

    for module_name, module_data in module_tree.items():
        original_components = module_data.get('components', [])
        normalized_components = []

        for comp_id in original_components:
            # Try exact FQDN match first
            if comp_id in components:
                normalized_components.append(comp_id)
            # Try reverse mapping from short ID
            elif comp_id in short_to_fqdn:
                fqdn = short_to_fqdn[comp_id]
                normalized_components.append(fqdn)
                total_normalized += 1
                logger.debug(f"   ✅ Normalized '{comp_id}' → '{fqdn}'")
            else:
                # Keep original (will fail validation later with helpful error)
                normalized_components.append(comp_id)
                total_failed += 1

                # ENHANCED DIAGNOSTICS: Search for similar components
                similar_mapping_keys = [k for k in short_to_fqdn.keys() if comp_id.lower() in k.lower()][:5]
                similar_fqdns = [fqdn for fqdn in components.keys() if comp_id.lower() in fqdn.lower()][:5]

                # Show helpful debug info
                logger.warning(
                    f"   ❌ Failed to normalize '{comp_id}' in module '{module_name}'\n"
                    f"      ├─ Not found as exact FQDN in components dictionary\n"
                    f"      ├─ Not found in short_id → FQDN mapping ({len(short_to_fqdn)} entries)\n"
                    f"      ├─ Similar mapping keys: {similar_mapping_keys if similar_mapping_keys else 'None found'}\n"
                    f"      └─ FQDNs containing '{comp_id}': {similar_fqdns if similar_fqdns else 'None found'}"
                )

        module_data['components'] = normalized_components

    if total_normalized > 0:
        logger.info(f"   ✅ Normalized {total_normalized} short IDs to FQDNs")
    if total_failed > 0:
        logger.warning(f"   ⚠️  Failed to normalize {total_failed} component IDs")
    logger.info("")

    # check if the module tree is valid
    if len(module_tree) <= 1:
        logger.debug(f"Skipping clustering for {current_module_name} because the module tree is too small: {len(module_tree)} modules")
        return {}

    if current_module_tree == {}:
        current_module_tree = module_tree
    else:
        value = current_module_tree
        for key in current_module_path:
            # Ensure the key exists and has a children dict
            if key not in value:
                logger.warning(f"Module '{key}' not found in tree during clustering")
                value[key] = {"children": {}}
            if "children" not in value[key]:
                logger.warning(f"Module '{key}' missing 'children' key during clustering")
                value[key]["children"] = {}
            value = value[key]["children"]
        for module_name, module_info in module_tree.items():
            del module_info["path"]
            value[module_name] = module_info

    for module_name, module_info in module_tree.items():
        sub_leaf_nodes = module_info.get("components", [])

        # Filter sub_leaf_nodes to ensure they exist in components
        valid_sub_leaf_nodes = []
        sub_skipped = 0
        for node in sub_leaf_nodes:
            if node in components:
                valid_sub_leaf_nodes.append(node)
            else:
                sub_skipped += 1
                # Extract namespace from FQDN
                namespace = ""
                is_deps = False
                if '.' in node:
                    namespace = node.split('.')[0]
                    is_deps = namespace.startswith('deps/')

                # Check if normalization was attempted (short_to_fqdn should still be in scope)
                attempted_mapping = node in short_to_fqdn
                mapping_result = f"Mapped to: {short_to_fqdn[node]}" if attempted_mapping else "No mapping found"

                # Show available FQDNs with same short ID for debugging
                possible_matches = [fqdn for fqdn in components.keys() if node in fqdn][:3]

                logger.warning(
                    f"Skipping invalid sub leaf node '{node}' in module '{module_name}'\n"
                    f"   ├─ FQDN format: {node}\n"
                    f"   ├─ Namespace: {namespace or '(unknown)'}\n"
                    f"   ├─ Source: {'dependency repo' if is_deps else 'main repo'}\n"
                    f"   ├─ Normalization: {mapping_result}\n"
                    f"   ├─ Possible matches in components: {possible_matches if possible_matches else 'None'}\n"
                    f"   └─ Reason: Component not found after normalization\n"
                    f"   └─ This node was suggested by LLM clustering but doesn't exist\n"
                    f"   └─ Possible causes: Parsing failure, excluded file, or LLM hallucination"
                )

        if sub_skipped > 0:
            logger.info(f"📊 Sub-module '{module_name}': {len(valid_sub_leaf_nodes)} valid nodes, {sub_skipped} skipped")

        current_module_path.append(module_name)
        module_info["children"] = {}
        module_info["children"] = cluster_modules(valid_sub_leaf_nodes, components, config, current_module_tree, module_name, current_module_path)
        current_module_path.pop()

    return module_tree