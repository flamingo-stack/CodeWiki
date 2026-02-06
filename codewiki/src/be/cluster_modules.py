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


def extract_module_hint(fqdn: str) -> str:
    """
    Extract module name from FQDN for human readability.

    Examples:
        "openframe-oss-lib.openframe-api-service-core..." → "api-service"
        "main-repo.src/services/auth.py::AuthService" → "auth"
    """
    # Strategy 1: Look for service-like patterns (openframe-api-service → api-service)
    parts = fqdn.split('.')
    for part in parts:
        if '-service' in part or '-api' in part:
            # Extract meaningful part (e.g., "openframe-api-service" → "api-service")
            segments = part.split('-')
            if len(segments) >= 2:
                return '-'.join(segments[-2:])

    # Strategy 2: Extract from file path (src/services/auth.py → auth)
    if '::' in fqdn:
        file_path = fqdn.split('::')[0]
        # Get last meaningful directory or file name
        path_parts = file_path.replace('\\', '/').split('/')
        for part in reversed(path_parts):
            if part and part not in ['src', 'main', 'java', 'com']:
                return part.replace('.py', '').replace('.java', '').replace('.ts', '')

    # Fallback: Use first segment
    return parts[0] if parts else "unknown"


def extract_package_hint(fqdn: str) -> str:
    """
    Extract package/category from FQDN for human readability.

    Examples:
        "...src.main.java.com.openframe.api.controller.Class" → "controller"
        "main-repo.src/models/device.py::DeviceModel" → "models"
    """
    # Strategy 1: Look for common package patterns
    common_packages = ['controller', 'service', 'repository', 'model', 'dto',
                      'config', 'util', 'helper', 'handler', 'processor']

    fqdn_lower = fqdn.lower()
    for pkg in common_packages:
        if pkg in fqdn_lower:
            return pkg

    # Strategy 2: Extract from file path structure
    if '::' in fqdn:
        file_path = fqdn.split('::')[0]
        path_parts = file_path.replace('\\', '/').split('/')
        # Look for meaningful directory names
        for part in reversed(path_parts[:-1]):  # Skip filename
            if part and part not in ['src', 'main', 'java', 'com', 'org']:
                return part

    # Fallback: Extract from path
    parts = fqdn.split('.')
    if len(parts) >= 2:
        return parts[-2]

    return "core"


def create_component_id_map(components: Dict[str, Node]) -> tuple[Dict[int, str], Dict[str, str]]:
    """
    Create bidirectional ID mapping for components.

    Returns:
        - id_to_fqdn: {0: "full.path.ClassName", 1: ...}
        - id_descriptions: {"0": "ClassName (module-name, package)", ...}
    """
    id_to_fqdn = {}
    id_descriptions = {}

    logger.info("🔢 Creating component ID mapping")

    for idx, (fqdn, component_data) in enumerate(sorted(components.items())):
        id_to_fqdn[idx] = fqdn

        # Extract human-readable parts
        if '::' in fqdn:
            class_name = fqdn.split('::')[-1]
        else:
            class_name = fqdn.split('.')[-1]

        module_hint = extract_module_hint(fqdn)
        package_hint = extract_package_hint(fqdn)

        # Create concise description
        id_descriptions[str(idx)] = f"{class_name} ({module_hint}, {package_hint})"

    logger.info(f"   ✅ Created {len(id_to_fqdn)} component ID mappings")
    logger.debug(f"   Example: 0 → {id_descriptions.get('0', 'N/A')}")

    return id_to_fqdn, id_descriptions


def format_potential_core_components(
    leaf_nodes: List[str],
    components: Dict[str, Node]
) -> tuple[str, str, Dict[int, str], Dict[str, str]]:
    """
    Format the potential core components into a string that can be used in the prompt.
    NOW RETURNS ID-BASED DESCRIPTIONS instead of FQDNs.

    Args:
        leaf_nodes: List of component FQDNs (fully qualified domain names)
        components: Dictionary mapping FQDNs to Node objects

    Returns:
        Tuple of:
        - potential_core_components: ID-based component list (for LLM)
        - potential_core_components_with_code: ID-based with code (for LLM)
        - id_to_fqdn: Mapping from ID to FQDN (for normalization)
        - id_descriptions: Mapping from ID string to human description
    """
    logger.debug(f"📋 Formatting components with ID-based system:")
    logger.debug(f"   ├─ Leaf nodes format: FQDN (e.g., 'main-repo.src/services/auth.py::AuthService')")
    logger.debug(f"   ├─ Components dict keys: FQDN (node.id)")
    logger.debug(f"   └─ Input: {len(leaf_nodes)} leaf nodes, {len(components)} components")

    # Create ID mapping FIRST (before filtering)
    id_to_fqdn, id_descriptions = create_component_id_map(components)

    # Create reverse mapping for quick lookup
    fqdn_to_id = {fqdn: idx for idx, fqdn in id_to_fqdn.items()}

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

    # Group leaf nodes by file
    leaf_nodes_by_file = defaultdict(list)
    for leaf_node in valid_leaf_nodes:
        leaf_nodes_by_file[components[leaf_node].relative_path].append(leaf_node)

    logger.debug(f"   ├─ Valid leaf nodes: {len(valid_leaf_nodes)}")
    logger.debug(f"   └─ Grouped into {len(leaf_nodes_by_file)} files")

    # Build ID-based component lists
    potential_core_components = ""
    potential_core_components_with_code = ""

    for file, leaf_nodes_in_file in sorted(leaf_nodes_by_file.items()):
        potential_core_components += f"# {file}\n"
        potential_core_components_with_code += f"# {file}\n"

        for leaf_node in sorted(leaf_nodes_in_file):
            # Get ID for this FQDN
            comp_id = fqdn_to_id.get(leaf_node)
            if comp_id is None:
                logger.warning(f"   ⚠️  No ID found for {leaf_node}")
                continue

            # Use ID and description instead of FQDN
            comp_desc = id_descriptions[str(comp_id)]
            potential_core_components += f"\t{comp_id}: {comp_desc}\n"
            potential_core_components_with_code += f"\t{comp_id}: {comp_desc}\n"
            potential_core_components_with_code += f"{components[leaf_node].source_code}\n"

    return potential_core_components, potential_core_components_with_code, id_to_fqdn, id_descriptions


def normalize_component_ids_by_lookup(
    module_tree: Dict,
    id_to_fqdn: Dict[int, str]
) -> Dict:
    """
    Replace component IDs with FQDNs using direct lookup.
    This is the CLEAN replacement for 200+ lines of fuzzy matching.

    Args:
        module_tree: LLM clustering response with component IDs
        id_to_fqdn: Mapping from integer ID to FQDN

    Returns:
        Module tree with IDs replaced by FQDNs
    """
    logger.info("🔄 Normalizing component IDs via direct lookup")

    total_normalized = 0
    total_failed = 0
    max_id = len(id_to_fqdn) - 1

    for module_name, module_data in module_tree.items():
        component_ids = module_data.get('components', [])
        normalized_components = []

        for comp_id in component_ids:
            # Convert to int and validate
            try:
                idx = int(comp_id)
                if idx in id_to_fqdn:
                    fqdn = id_to_fqdn[idx]
                    normalized_components.append(fqdn)
                    total_normalized += 1
                    logger.debug(f"   ✅ ID {idx} → {fqdn}")
                else:
                    logger.warning(
                        f"   ❌ Invalid ID {idx} in module '{module_name}'\n"
                        f"      ├─ Valid range: 0-{max_id}\n"
                        f"      └─ LLM returned out-of-range ID"
                    )
                    total_failed += 1
            except (ValueError, TypeError) as e:
                logger.warning(
                    f"   ❌ Non-integer ID in module '{module_name}'\n"
                    f"      ├─ Received: {comp_id} (type: {type(comp_id).__name__})\n"
                    f"      ├─ Error: {e}\n"
                    f"      └─ LLM must return integer IDs only"
                )
                total_failed += 1

        module_data['components'] = normalized_components

    logger.info(f"   ✅ Normalized {total_normalized} component IDs")
    if total_failed > 0:
        logger.warning(f"   ⚠️  Failed to normalize {total_failed} IDs")

    return module_tree


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

    # Get ID-based component formatting
    potential_core_components, potential_core_components_with_code, id_to_fqdn, id_descriptions = \
        format_potential_core_components(leaf_nodes, components)

    token_count = count_tokens(potential_core_components_with_code)
    logger.info(f"   ├─ Potential components (with code): {token_count} tokens")
    logger.info(f"   ├─ Max token per module: {config.max_token_per_module}")
    logger.info(f"   └─ ID-based system: {len(id_to_fqdn)} components mapped")

    if token_count <= config.max_token_per_module:
        logger.info(f"   └─ ⏭️  Skipping clustering - components fit in single module ({token_count} ≤ {config.max_token_per_module})")
        return {}

    logger.info(f"   └─ ✅ Proceeding with clustering - components exceed threshold")
    logger.info("")

    prompt = format_cluster_prompt(potential_core_components, current_module_tree, current_module_name)
    logger.info(f"🤖 Calling clustering LLM")
    logger.info(f"   ├─ Model: {config.cluster_model}")
    logger.info(f"   ├─ Prompt uses ID-based component references")
    logger.info(f"   └─ LLM will return integer IDs (0-{len(id_to_fqdn)-1})")
    logger.info("")

    response = call_llm(prompt, config, model=config.cluster_model)

    logger.info(f"   ✅ Clustering LLM response received")
    logger.info(f"   ├─ Response length: {len(response)} chars")
    logger.info(f"   └─ Preview: {response[:150]}...")
    logger.info("")

    # Parse the response
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

    # Normalize component IDs using simple lookup (replaces 200+ lines of fuzzy matching)
    module_tree = normalize_component_ids_by_lookup(module_tree, id_to_fqdn)

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

                # Show available FQDNs for debugging
                possible_matches = [fqdn for fqdn in components.keys() if node in fqdn][:3]

                logger.warning(
                    f"Skipping invalid sub leaf node '{node}' in module '{module_name}'\n"
                    f"   ├─ FQDN format: {node}\n"
                    f"   ├─ Namespace: {namespace or '(unknown)'}\n"
                    f"   ├─ Source: {'dependency repo' if is_deps else 'main repo'}\n"
                    f"   ├─ Possible matches in components: {possible_matches if possible_matches else 'None'}\n"
                    f"   └─ Reason: Component not found after ID normalization\n"
                    f"   └─ This should not happen with ID-based system - possible LLM error"
                )

        if sub_skipped > 0:
            logger.info(f"📊 Sub-module '{module_name}': {len(valid_sub_leaf_nodes)} valid nodes, {sub_skipped} skipped")

        current_module_path.append(module_name)
        module_info["children"] = {}
        module_info["children"] = cluster_modules(valid_sub_leaf_nodes, components, config, current_module_tree, module_name, current_module_path)
        current_module_path.pop()

    return module_tree