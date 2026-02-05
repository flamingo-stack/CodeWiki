from typing import List, Dict, Any
from collections import defaultdict
import logging
import traceback
logger = logging.getLogger(__name__)

from codewiki.src.be.dependency_analyzer.models.core import Node
from codewiki.src.be.dependency_analyzer.validation import validate_components_before_clustering
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
    for file, leaf_nodes in sorted(leaf_nodes_by_file.items()):  # ✅ Simplified - no need for dict()
        potential_core_components += f"# {file}\n"
        potential_core_components_with_code += f"# {file}\n"
        for leaf_node in sorted(leaf_nodes):  # ✅ SORT for determinism
            # leaf_node is FQDN format (e.g., "main-repo.src/services/auth.py::AuthService")
            potential_core_components += f"\t{leaf_node}\n"
            potential_core_components_with_code += f"\t{leaf_node}\n"
            potential_core_components_with_code += f"{components[leaf_node].source_code}\n"

    return potential_core_components, potential_core_components_with_code


def _find_best_path_match(llm_id: str, candidates: List[str]) -> str | None:
    """
    Find the best matching FQDN from candidates based on path similarity.

    Args:
        llm_id: Component ID returned by LLM
        candidates: List of potential FQDN matches

    Returns:
        Best matching FQDN or None if ambiguous
    """
    llm_segments = llm_id.split('.')

    # Score each candidate by number of matching path segments
    scores = []
    for candidate in candidates:
        candidate_segments = candidate.split('.')
        # Count matching segments in order
        matches = 0
        for i, llm_seg in enumerate(llm_segments):
            if llm_seg in candidate_segments:
                # Bonus points if segments are in same relative position
                try:
                    candidate_idx = candidate_segments.index(llm_seg)
                    position_diff = abs(i - candidate_idx)
                    matches += 1 + (1.0 / (1 + position_diff))  # Weight by position similarity
                except ValueError:
                    pass
        scores.append((candidate, matches))

    # Sort by score descending
    scores.sort(key=lambda x: x[1], reverse=True)

    # Return best match if it's clearly better than alternatives
    if len(scores) > 1 and scores[0][1] > scores[1][1]:
        logger.debug(f"      Best match score: {scores[0][1]:.2f} vs next: {scores[1][1]:.2f}")
        return scores[0][0]

    return None


def build_short_id_to_fqdn_map(components: Dict[str, Node]) -> Dict[str, str]:
    """
    Enhanced version of build_short_id_to_fqdn_map with partial path support.

    Maps both:
    - Short component names (e.g., "UserService")
    - Partial paths (e.g., "auth.UserService", "services.auth.UserService")

    This helps match LLM outputs that include partial directory paths
    and handles fuzzy matching for complex nested structures.

    Args:
        components: Dictionary with FQDN keys and Node values

    Returns:
        Dictionary mapping short_id → fqdn
    """
    mapping = {}
    collisions = defaultdict(list)

    for fqdn, node in sorted(components.items()):  # ✅ SORT for determinism
        # Strategy 1: Use node's short_id if available
        short_id = getattr(node, 'short_id', None) or ""

        if not short_id:
            # Fallback: extract from FQDN
            if '::' in fqdn:
                short_id = fqdn.split('::')[-1]
            else:
                short_id = fqdn.split('.')[-1]

        # Map short_id → FQDN
        if short_id in mapping:
            collisions[short_id].append(fqdn)
        else:
            mapping[short_id] = fqdn

        # Strategy 2: Map partial paths (last 2-4 segments)
        # This helps match LLM outputs like "services.auth.UserService"
        # when the full FQDN is "main-repo.src.services.auth.UserService"
        segments = fqdn.split('.')
        if len(segments) > 2:
            # Map progressively longer suffixes
            for i in range(2, min(5, len(segments) + 1)):  # Last 2-4 segments
                partial_id = '.'.join(segments[-i:])

                # Only map if unique
                if partial_id not in mapping:
                    mapping[partial_id] = fqdn
                elif mapping[partial_id] != fqdn:
                    # Collision detected
                    if partial_id not in collisions:
                        collisions[partial_id].append(mapping[partial_id])
                    collisions[partial_id].append(fqdn)

    # Log collisions for debugging
    if collisions:
        logger.warning(f"   ⚠️  Found {len(collisions)} short ID collisions:")
        for short_id, fqdns in list(collisions.items())[:5]:
            logger.warning(f"      '{short_id}' → {fqdns[:3]}")

    logger.info(f"   ✅ Built short_id → FQDN mapping with {len(mapping)} entries")
    logger.debug(f"      ({len(collisions)} collisions detected)")

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

    # ✅ Pre-flight validation - check all leaf nodes exist in components
    if not validate_components_before_clustering(components, leaf_nodes):
        logger.warning("⚠️  Pre-flight validation found issues, filtering out missing components...")
        # Filter out missing components
        valid_leaf_nodes = [ln for ln in leaf_nodes if ln in components]
        logger.warning(f"   Filtered from {len(leaf_nodes)} to {len(valid_leaf_nodes)} valid leaf nodes")
        leaf_nodes = valid_leaf_nodes

        if not leaf_nodes:
            logger.error("❌ No valid leaf nodes remaining after filtering")
            return {}

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

    # Build reverse mapping: short_id → FQDN (enhanced version with partial path support)
    logger.info(f"🔄 Normalizing component IDs in clustering response")
    short_to_fqdn = build_short_id_to_fqdn_map(components)

    # Normalize all component IDs in module_tree (enhanced 5-strategy normalization)
    total_normalized = 0
    total_failed = 0

    for module_name, module_data in module_tree.items():
        original_components = module_data.get('components', [])
        normalized_components = []

        for comp_id in original_components:
            # Strategy 1: Exact FQDN match
            if comp_id in components:
                normalized_components.append(comp_id)
                logger.debug(f"   ✅ Exact match: '{comp_id}'")
                continue

            # Strategy 2: Short ID mapping
            if comp_id in short_to_fqdn:
                fqdn = short_to_fqdn[comp_id]
                normalized_components.append(fqdn)
                total_normalized += 1
                logger.debug(f"   ✅ Mapped '{comp_id}' → '{fqdn}'")
                continue

            # Strategy 3: Strip "deps." prefix and retry
            stripped_id = comp_id
            if comp_id.startswith("deps."):
                stripped_id = comp_id[5:]  # Remove "deps." prefix
                logger.debug(f"   🔧 Stripping 'deps.' prefix: '{comp_id}' → '{stripped_id}'")

                # Try exact match with stripped ID
                if stripped_id in components:
                    normalized_components.append(stripped_id)
                    total_normalized += 1
                    logger.info(
                        f"   ✅ Found after stripping 'deps.' prefix:\n"
                        f"      LLM returned: '{comp_id}'\n"
                        f"      Actual FQDN:  '{stripped_id}'"
                    )
                    continue

                # Try short_id mapping with stripped ID
                if stripped_id in short_to_fqdn:
                    fqdn = short_to_fqdn[stripped_id]
                    normalized_components.append(fqdn)
                    total_normalized += 1
                    logger.info(
                        f"   ✅ Mapped after stripping prefix:\n"
                        f"      LLM returned: '{comp_id}'\n"
                        f"      Stripped to:  '{stripped_id}'\n"
                        f"      Mapped to:    '{fqdn}'"
                    )
                    continue

            # Strategy 4: Fuzzy substring matching on component name
            # Extract the likely component name (last segment)
            component_name = comp_id.split('.')[-1]

            # Search for FQDNs ending with this component name
            fuzzy_matches = [
                fqdn for fqdn in components.keys()
                if fqdn.split('.')[-1] == component_name
            ]

            if len(fuzzy_matches) == 1:
                # Unique match found
                normalized_components.append(fuzzy_matches[0])
                total_normalized += 1
                logger.info(
                    f"   ✅ Fuzzy matched by component name:\n"
                    f"      LLM returned:  '{comp_id}'\n"
                    f"      Component:     '{component_name}'\n"
                    f"      Matched FQDN:  '{fuzzy_matches[0]}'"
                )
                continue
            elif len(fuzzy_matches) > 1:
                # Multiple matches - try to find best match by path similarity
                best_match = _find_best_path_match(comp_id, fuzzy_matches)
                if best_match:
                    normalized_components.append(best_match)
                    total_normalized += 1
                    logger.info(
                        f"   ✅ Best fuzzy match from {len(fuzzy_matches)} candidates:\n"
                        f"      LLM returned: '{comp_id}'\n"
                        f"      Matched FQDN: '{best_match}'"
                    )
                    continue
                else:
                    logger.warning(
                        f"   ⚠️  Multiple ambiguous fuzzy matches for '{comp_id}':\n"
                        f"      Component: '{component_name}'\n"
                        f"      Candidates:\n" +
                        '\n'.join(f"        - {m}" for m in fuzzy_matches[:5]) +
                        (f"\n        ... and {len(fuzzy_matches) - 5} more" if len(fuzzy_matches) > 5 else "")
                    )

            # Strategy 5: Try matching by suffix path (last N segments)
            # This handles cases where LLM includes partial path
            # Example: "deps.openframe-oss-lib.src.main.java.Class"
            #          should match "openframe-oss-lib.different.path.java.Class"
            if '.' in comp_id:
                # Try matching last 2-4 segments
                segments = comp_id.split('.')
                suffix_matched = False
                for n in range(2, min(5, len(segments) + 1)):
                    suffix = '.'.join(segments[-n:])
                    suffix_matches = [
                        fqdn for fqdn in components.keys()
                        if fqdn.endswith(suffix)
                    ]
                    if len(suffix_matches) == 1:
                        normalized_components.append(suffix_matches[0])
                        total_normalized += 1
                        logger.info(
                            f"   ✅ Matched by path suffix:\n"
                            f"      LLM returned: '{comp_id}'\n"
                            f"      Suffix:       '{suffix}'\n"
                            f"      Matched FQDN: '{suffix_matches[0]}'"
                        )
                        suffix_matched = True
                        break

                if suffix_matched:
                    continue

            # All strategies failed - keep original (will fail validation)
            normalized_components.append(comp_id)
            total_failed += 1

            # Enhanced failure logging
            similar_short_ids = [
                k for k in short_to_fqdn.keys()
                if component_name.lower() in k.lower()
            ][:5]

            possible_fqdns = [
                fqdn for fqdn in components.keys()
                if component_name.lower() in fqdn.lower()
            ][:5]

            logger.warning(
                f"   ❌ Failed to normalize '{comp_id}' in module '{module_name}'\n"
                f"      ├─ Original ID:      '{comp_id}'\n"
                f"      ├─ Stripped ID:      '{stripped_id}'\n"
                f"      ├─ Component name:   '{component_name}'\n"
                f"      ├─ Fuzzy matches:    {len(fuzzy_matches)}\n"
                f"      ├─ Similar short IDs: {similar_short_ids if similar_short_ids else 'None'}\n"
                f"      ├─ Possible FQDNs:   {possible_fqdns if possible_fqdns else 'None'}\n"
                f"      └─ Reason: Component not found in any normalization strategy\n"
                f"         This could indicate:\n"
                f"         • Component filtered during parsing\n"
                f"         • LLM hallucination (non-existent component)\n"
                f"         • FQDN format mismatch requiring new normalization strategy"
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