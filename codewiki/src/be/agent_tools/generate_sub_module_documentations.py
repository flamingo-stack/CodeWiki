from pydantic_ai import RunContext, Tool, Agent
from pydantic_ai.usage import UsageLimits

from codewiki.src.be.agent_tools.deps import CodeWikiDeps
from codewiki.src.be.agent_tools.read_code_components import read_code_components_tool
from codewiki.src.be.agent_tools.str_replace_editor import str_replace_editor_tool
from codewiki.src.be.llm_services import create_fallback_models
from codewiki.src.be.prompt_template import SYSTEM_PROMPT, LEAF_SYSTEM_PROMPT, format_user_prompt, format_system_prompt, format_leaf_system_prompt
from codewiki.src.be.utils import is_complex_module, count_tokens
from codewiki.src.be.cluster_modules import format_potential_core_components

import logging
logger = logging.getLogger(__name__)



async def generate_sub_module_documentation(
    ctx: RunContext[CodeWikiDeps],
    sub_module_specs: dict[str, list[str]]
) -> str:
    """Generate detailed description of a given sub-module specs to the sub-agents

    Args:
        sub_module_specs: The specs of the sub-modules to generate documentation for. E.g. {"sub_module_1": ["core_component_1.1", "core_component_1.2"], "sub_module_2": ["core_component_2.1", "core_component_2.2"], ...}
    """

    deps = ctx.deps
    previous_module_name = deps.current_module_name

    # CRITICAL FIX: Use ID-based normalization system
    # The LLM returns integer IDs (e.g., 0, 1, 2) which we need to convert to FQDNs
    logger.info(f"🔄 Normalizing sub-module component IDs (ID-based system)")

    # Get all component IDs from sub_module_specs to create ID mapping
    all_component_ids = []
    for component_ids in sub_module_specs.values():
        all_component_ids.extend(component_ids)

    # Create ID-to-FQDN mapping using the ID-based system
    # This returns (str1, str2, id_to_fqdn, id_descriptions) but we only need id_to_fqdn
    _, _, id_to_fqdn, _ = format_potential_core_components(all_component_ids, deps.components)

    normalized_specs = {}
    total_normalized = 0
    total_failed = 0

    for sub_module_name, component_ids in sub_module_specs.items():
        normalized_ids = []
        for comp_id in component_ids:
            # Try exact FQDN match first (component_ids might already be FQDNs)
            if comp_id in deps.components:
                normalized_ids.append(comp_id)
            # Try converting integer ID to FQDN (ID-based system)
            else:
                try:
                    # LLM should return integer IDs
                    idx = int(comp_id)
                    if idx in id_to_fqdn:
                        fqdn = id_to_fqdn[idx]
                        normalized_ids.append(fqdn)
                        total_normalized += 1
                        logger.debug(f"   ✅ Normalized ID {idx} → '{fqdn}'")
                    else:
                        logger.warning(
                            f"   ⚠️  Failed to normalize ID {idx} in sub-module '{sub_module_name}'\n"
                            f"      ├─ ID out of range (valid: 0-{len(id_to_fqdn)-1})\n"
                            f"      └─ LLM returned invalid integer ID"
                        )
                        total_failed += 1
                except (ValueError, TypeError):
                    # comp_id is not an integer - likely a class name (LLM ignored instructions)
                    similar_fqdns = [fqdn for fqdn in deps.components.keys() if str(comp_id).lower() in fqdn.lower()][:5]
                    logger.warning(
                        f"   ⚠️  Failed to normalize '{comp_id}' in sub-module '{sub_module_name}'\n"
                        f"      ├─ Not an integer ID (type: {type(comp_id).__name__})\n"
                        f"      ├─ LLM returned class name instead of integer ID\n"
                        f"      └─ FQDNs containing '{comp_id}': {similar_fqdns if similar_fqdns else 'None found'}"
                    )
                    total_failed += 1

        normalized_specs[sub_module_name] = normalized_ids

    if total_normalized > 0:
        logger.info(f"   ✅ Normalized {total_normalized} integer IDs to FQDNs")
    if total_failed > 0:
        logger.warning(f"   ⚠️  Failed to normalize {total_failed} component IDs (LLM ignored instructions)")

    # Replace original specs with normalized specs
    sub_module_specs = normalized_specs

    # Create fallback models from config
    fallback_models = create_fallback_models(deps.config)

    # add the sub-module to the module tree
    value = deps.module_tree
    for key in deps.path_to_current_module:
        # Ensure the key exists and has a children dict
        if key not in value:
            logger.warning(f"Module '{key}' not found in tree, creating empty entry")
            value[key] = {"children": {}}
        if "children" not in value[key]:
            logger.warning(f"Module '{key}' missing 'children' key, adding empty dict")
            value[key]["children"] = {}
        value = value[key]["children"]
    for sub_module_name, core_component_ids in sub_module_specs.items():
        value[sub_module_name] = {"components": core_component_ids, "children": {}}
    
    for sub_module_name, core_component_ids in sub_module_specs.items():

        # Create visual indentation for nested modules
        indent = "  " * deps.current_depth
        arrow = "└─" if deps.current_depth > 0 else "→"

        logger.info(f"{indent}{arrow} Generating documentation for sub-module: {sub_module_name}")

        # Get the second element (potential_core_components_with_code) which is a string
        _, potential_core_components_with_code, _, _ = format_potential_core_components(core_component_ids, ctx.deps.components)
        num_tokens = count_tokens(potential_core_components_with_code)

        # FLAMINGO_PATCH: Added retries=3 to fix "Tool exceeded max retries count of 1" errors
        # Use configurable max_token_per_leaf_module instead of hardcoded constant
        if is_complex_module(ctx.deps.components, core_component_ids) and ctx.deps.current_depth < ctx.deps.max_depth and num_tokens >= ctx.deps.config.max_token_per_leaf_module:
            sub_agent = Agent(
                model=fallback_models,
                name=sub_module_name,
                deps_type=CodeWikiDeps,
                system_prompt=format_system_prompt(sub_module_name, ctx.deps.custom_instructions),
                tools=[read_code_components_tool, str_replace_editor_tool, generate_sub_module_documentation_tool],
                retries=3,
            )
        else:
            sub_agent = Agent(
                model=fallback_models,
                name=sub_module_name,
                deps_type=CodeWikiDeps,
                system_prompt=format_leaf_system_prompt(sub_module_name, ctx.deps.custom_instructions),
                tools=[read_code_components_tool, str_replace_editor_tool],
                retries=3,
            )

        deps.current_module_name = sub_module_name
        deps.path_to_current_module.append(sub_module_name)
        deps.current_depth += 1
        # log the current module tree
        # print(f"Current module tree: {json.dumps(deps.module_tree, indent=4)}")

        # FLAMINGO_PATCH: Added usage_limits to prevent "request_limit of 50" exceeded errors
        result = await sub_agent.run(
            format_user_prompt(
                module_name=deps.current_module_name,
                core_component_ids=core_component_ids,
                components=ctx.deps.components,
                module_tree=ctx.deps.module_tree,
            ),
            deps=ctx.deps,
            usage_limits=UsageLimits(request_limit=1000),
        )

        # remove the sub-module name from the path to current module and the module tree
        deps.path_to_current_module.pop()
        deps.current_depth -= 1

    # restore the previous module name
    deps.current_module_name = previous_module_name

    return f"Generate successfully. Documentations: {', '.join([key + '.md' for key in sub_module_specs.keys()])} are saved in the working directory."


generate_sub_module_documentation_tool = Tool(function=generate_sub_module_documentation, name="generate_sub_module_documentation", description="Generate detailed description of a given sub-module specs to the sub-agents", takes_ctx=True)