"""Agent tool for reading the source code of specific CodeWiki components by id.

This module exposes `read_code_components_tool`, a pydantic-ai Tool that the
documentation-generation agent calls to fetch the verbatim source code of one
or more components by their fully-qualified component id (module.path::Name).
It looks up components from the shared `CodeWikiDeps.components` map built
earlier in the pipeline and is used by the agent to ground its explanations
in actual source rather than hallucinated code.
"""

from pydantic_ai import RunContext, Tool
from codewiki.src.be.agent_tools.deps import CodeWikiDeps


async def read_code_components(ctx: RunContext[CodeWikiDeps], component_ids: list[str]) -> str:
    """Read the code of a given component id

    Args:
        component_ids: The ids of the components to read, e.g. ["sweagent.types.AgentRunResult", "sweagent.types.AgentRunResult"] where sweagent.types part is the path to the component and AgentRunResult is the name of the component
    """

    results = []

    for component_id in component_ids:
        if component_id not in ctx.deps.components:
            results.append(f"# Component {component_id} not found")
        else:
            results.append(f"# Component {component_id}:\n{ctx.deps.components[component_id].source_code.strip()}\n\n")

    return "\n".join(results)

read_code_components_tool = Tool(function=read_code_components, name="read_code_components", description="Read the code of a given list of component ids", takes_ctx=True)
