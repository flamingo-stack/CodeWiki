from pydantic_ai import Agent
from pydantic_ai.usage import UsageLimits
# import logfire
import logging
import os
import traceback
from typing import Dict, List, Any

# Configure logging and monitoring

logger = logging.getLogger(__name__)

# try:
#     # Configure logfire with environment variables for Docker compatibility
#     logfire_token = os.getenv('LOGFIRE_TOKEN')
#     logfire_project = os.getenv('LOGFIRE_PROJECT_NAME', 'default')
#     logfire_service = os.getenv('LOGFIRE_SERVICE_NAME', 'default')
    
#     if logfire_token:
#         # Configure with explicit token (for Docker)
#         logfire.configure(
#             token=logfire_token,
#             project_name=logfire_project,
#             service_name=logfire_service,
#         )
#     else:
#         # Use default configuration (for local development with logfire auth)
#         logfire.configure(
#             project_name=logfire_project,
#             service_name=logfire_service,
#         )
    
#     logfire.instrument_pydantic_ai()
#     logger.debug(f"Logfire configured successfully for project: {logfire_project}")
    
# except Exception as e:
#     logger.warning(f"Failed to configure logfire: {e}")

# Local imports
from codewiki.src.be.agent_tools.deps import CodeWikiDeps
from codewiki.src.be.agent_tools.read_code_components import read_code_components_tool
from codewiki.src.be.agent_tools.str_replace_editor import str_replace_editor_tool
from codewiki.src.be.agent_tools.generate_sub_module_documentations import generate_sub_module_documentation_tool
from codewiki.src.be.llm_services import create_fallback_models, reset_request_counter
from codewiki.src.be.prompt_template import (
    format_user_prompt,
    format_system_prompt,
    format_leaf_system_prompt,
)
from codewiki.src.be.utils import is_complex_module
from codewiki.src.config import (
    Config,
    MODULE_TREE_FILENAME,
    OVERVIEW_FILENAME,
)
from codewiki.src.utils import file_manager
from codewiki.src.be.dependency_analyzer.models.core import Node


class AgentOrchestrator:
    """Orchestrates the AI agents for documentation generation."""

    def __init__(self, config: Config):
        import logging
        logger = logging.getLogger(__name__)

        self.config = config
        self.fallback_models = create_fallback_models(config)
        self.custom_instructions = config.get_prompt_addition() if config else None

        # Log custom instructions status for debugging
        if self.custom_instructions:
            logger.info("🔧 AgentOrchestrator initialized with custom instructions")
            logger.info(f"   ├─ Combined instructions length: {len(self.custom_instructions)} chars")
            logger.info(f"   └─ Preview: {self.custom_instructions[:100]}...")
        else:
            logger.info("🔧 AgentOrchestrator initialized without custom instructions")
    
    def create_agent(self, module_name: str, components: Dict[str, Any],
                    core_component_ids: List[str]) -> Agent:
        """Create an appropriate agent based on module complexity."""
        # FLAMINGO_PATCH: Added retries=3 to fix "Tool exceeded max retries count of 1" errors
        if is_complex_module(components, core_component_ids):
            return Agent(
                self.fallback_models,
                name=module_name,
                deps_type=CodeWikiDeps,
                tools=[
                    read_code_components_tool,
                    str_replace_editor_tool,
                    generate_sub_module_documentation_tool
                ],
                system_prompt=format_system_prompt(module_name, self.custom_instructions),
                retries=3,  # From fork
            )
        else:
            return Agent(
                self.fallback_models,
                name=module_name,
                deps_type=CodeWikiDeps,
                tools=[read_code_components_tool, str_replace_editor_tool],
                system_prompt=format_leaf_system_prompt(module_name, self.custom_instructions),
                retries=3,  # From fork
            )
    
    async def process_module(self, module_name: str, components: Dict[str, Node],
                           core_component_ids: List[str], module_path: List[str], working_dir: str) -> Dict[str, Any]:
        """Process a single module and generate its documentation."""
        logger.info(f"📝 Processing module: {module_name}")
        logger.info(f"   └─ Core components: {len(core_component_ids)}")
        logger.info(f"   └─ Module path: {' > '.join(module_path) if module_path else '(root)'}")
        logger.info(f"   └─ Working directory: {working_dir}")

        # Reset request counter for this module
        reset_request_counter(module_name)

        # Load or create module tree
        # CRITICAL: module_tree.json is ALWAYS in the BASE docs directory,
        # not in the module's subdirectory (working_dir may be a nested path)
        base_docs_dir = os.path.abspath(self.config.docs_dir)
        module_tree_path = os.path.join(base_docs_dir, MODULE_TREE_FILENAME)
        module_tree = file_manager.load_json(module_tree_path)
        
        # Create agent
        is_complex = is_complex_module(components, core_component_ids)
        agent_type = "Complex (with sub-modules)" if is_complex else "Leaf (single module)"
        logger.info(f"   └─ Agent type: {agent_type}")
        agent = self.create_agent(module_name, components, core_component_ids)

        # Create dependencies
        deps = CodeWikiDeps(
            absolute_docs_path=working_dir,
            absolute_repo_path=str(os.path.abspath(self.config.repo_path)),
            registry={},
            components=components,
            path_to_current_module=module_path,
            current_module_name=module_name,
            module_tree=module_tree,
            max_depth=self.config.max_depth,
            current_depth=1,
            config=self.config,
            custom_instructions=self.custom_instructions
        )

        # check if overview docs already exists
        overview_docs_path = os.path.join(working_dir, OVERVIEW_FILENAME)
        if os.path.exists(overview_docs_path):
            logger.info(f"✓ Overview docs already exists at {overview_docs_path}")
            return module_tree

        # check if module docs already exists
        # HIERARCHICAL OUTPUT: ALL modules use subdirectories (module_name/module_name.md)
        # This matches the breaking change from commit 2ac6767
        docs_path = os.path.join(working_dir, module_name, f"{module_name}.md")
        if os.path.exists(docs_path):
            logger.info(f"✓ Module docs already exists at {docs_path}")
            return module_tree
        
        # Run agent
        # FLAMINGO_PATCH: Added usage_limits to prevent "request_limit of 50" exceeded errors
        logger.info(f"   └─ Starting agent execution...")
        logger.info(f"   └─ Usage limits: 1000 requests max")
        logger.info("")

        # Format and log the user prompt
        user_prompt = format_user_prompt(
            module_name=module_name,
            core_component_ids=core_component_ids,
            components=components,
            module_tree=deps.module_tree
        )
        logger.info(f"📨 Agent Execution - User Prompt Ready")
        logger.info(f"   ├─ Module: {module_name}")
        logger.info(f"   ├─ Agent type: {agent_type}")
        logger.info(f"   ├─ User prompt length: {len(user_prompt)} chars (~{len(user_prompt) // 4} tokens)")
        logger.info(f"   └─ 🚀 Invoking agent with formatted prompts...")
        logger.info("")

        try:
            result = await agent.run(
                user_prompt,
                deps=deps,
                usage_limits=UsageLimits(request_limit=1000),
            )

            # Save updated module tree
            file_manager.save_json(deps.module_tree, module_tree_path)
            logger.info(f"✅ Successfully generated documentation for: {module_name}")
            logger.info(f"   └─ Output: {docs_path}")

            return deps.module_tree

        except Exception as e:
            logger.error(f"❌ Error processing module {module_name}: {str(e)}")
            logger.error(f"   └─ Traceback: {traceback.format_exc()}")
            raise