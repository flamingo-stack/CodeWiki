# CodeWiki Prompt Logging Implementation

**Date:** 2025-02-02
**Repository:** `/Users/michaelassraf/Documents/GitHub/CodeWiki`

## Overview

Added comprehensive logging for prompt injection and assembly throughout the CodeWiki documentation generation pipeline. Every prompt that goes to an LLM is now logged with full visibility into:

- Prompt template selection
- Component lengths and previews
- Variable substitutions
- Token estimates
- LLM API invocations
- Response details

## Logging Format

All logs follow a consistent tree-based format for readability:

```
📝 Prompt Assembly Stage - TEMPLATE_NAME
   ├─ Template: TEMPLATE_NAME
   ├─ Module name: example_module
   ├─ Component 1: 1,234 chars
   │  └─ Preview: First 100 characters...
   ├─ Component 2: 5,678 chars
   ├─ Total assembled prompt: 10,000 chars (~2,500 tokens)
   └─ ✅ Prompt ready for LLM invocation

🤖 LLM API Invocation
   ├─ Stage: main/generation
   ├─ Model: claude-sonnet-4.5
   ├─ Base URL: https://api.anthropic.com
   ├─ Prompt length: 10,000 chars (~2,500 tokens)
   │  └─ Preview: First 150 characters...
   ├─ Temperature: 0.0
   ├─ Max tokens: 16384 (field: max_tokens)
   ├─ Temperature supported: True
   └─ 🚀 Sending request to LLM API...

   ✅ LLM Response Received
   ├─ Response length: 4,321 chars (~1,080 tokens)
   └─ Preview: First 150 characters...
```

## Files Modified

### 1. `/codewiki/src/be/prompt_template.py` (7 functions enhanced)

All prompt formatting functions now log detailed assembly information:

#### `format_system_prompt(module_name, custom_instructions)`
- **Template:** SYSTEM_PROMPT (complex modules)
- **Logs:**
  - Module name
  - Custom instructions length + preview
  - Flamingo custom instructions section length + preview
  - Flamingo guidelines section length + preview
  - Base system prompt length
  - Total assembled prompt length + token estimate

#### `format_leaf_system_prompt(module_name, custom_instructions)`
- **Template:** LEAF_SYSTEM_PROMPT (leaf modules)
- **Logs:** Same as `format_system_prompt`

#### `format_user_prompt(module_name, core_component_ids, components, module_tree)`
- **Template:** USER_PROMPT
- **Logs:**
  - Module name
  - Core component IDs count + list preview
  - Module tree context length + preview
  - Core component codes length
  - Number of files included
  - Base USER_PROMPT length
  - Total assembled prompt length + token estimate

#### `format_repo_overview_prompt(repo_name, repo_structure)`
- **Template:** REPO_OVERVIEW_PROMPT
- **Logs:**
  - Repository name
  - Repository structure (JSON) length + preview
  - Flamingo sections lengths
  - Base prompt length
  - Total assembled prompt length + token estimate

#### `format_module_overview_prompt(module_name, repo_structure)`
- **Template:** MODULE_OVERVIEW_PROMPT
- **Logs:** Same as `format_repo_overview_prompt`

#### `format_cluster_prompt(potential_core_components, module_tree, module_name)`
- **Templates:** CLUSTER_REPO_PROMPT or CLUSTER_MODULE_PROMPT
- **Logs:**
  - Template selection (repo-level vs module-level)
  - Module name (if applicable)
  - Potential core components length + preview
  - Module tree context length + preview (if module-level)
  - Base prompt length
  - Total assembled prompt length + token estimate

### 2. `/codewiki/src/be/llm_services.py` (1 function enhanced)

#### `call_llm(prompt, config, model, temperature)`
- **Logs Before Request:**
  - Stage identification (cluster/main/fallback)
  - Model name
  - Base URL
  - Prompt length + token estimate + preview
  - Temperature value
  - Max tokens configuration (value + field name)
  - Temperature support status

- **Logs After Response:**
  - Response length + token estimate
  - Response preview

### 3. `/codewiki/src/be/agent_orchestrator.py` (1 function enhanced)

#### `process_module(module_name, components, core_component_ids, module_path, working_dir)`
- **New Logs:**
  - Agent execution section header
  - Module name
  - Agent type (Complex vs Leaf)
  - User prompt length + token estimate
  - Agent invocation indicator

### 4. `/codewiki/src/be/cluster_modules.py` (1 function enhanced)

#### `cluster_modules(leaf_nodes, components, config, ...)`
- **New Logs:**
  - Module clustering operation header
  - Current module name
  - Module path
  - Leaf nodes count
  - Components dictionary size
  - Potential components token count
  - Max token per module threshold
  - Clustering decision (skip or proceed)
  - LLM model used
  - Response length + preview

### 5. `/codewiki/src/be/documentation_generator.py` (1 function enhanced)

#### `generate_parent_module_docs(module_path, working_dir)`
- **New Logs:**
  - Parent documentation generation header
  - Module name
  - Module path
  - Repository structure JSON length
  - Prompt type (MODULE_OVERVIEW vs REPO_OVERVIEW)
  - LLM model used
  - Generation status

## Prompt Template Catalog

### Documentation Generation Templates

1. **SYSTEM_PROMPT** - Complex modules with sub-modules
   - Used for: Multi-file modules requiring sub-module generation
   - Logged in: `format_system_prompt()`

2. **LEAF_SYSTEM_PROMPT** - Simple leaf modules
   - Used for: Single-file or simple modules without sub-modules
   - Logged in: `format_leaf_system_prompt()`

3. **USER_PROMPT** - Module documentation request
   - Used for: Providing module context and code to agents
   - Logged in: `format_user_prompt()`

### Overview Generation Templates

4. **REPO_OVERVIEW_PROMPT** - Repository-level overview
   - Used for: Generating top-level repository documentation
   - Logged in: `format_repo_overview_prompt()`

5. **MODULE_OVERVIEW_PROMPT** - Parent module overview
   - Used for: Generating aggregated parent module documentation
   - Logged in: `format_module_overview_prompt()`

### Clustering Templates

6. **CLUSTER_REPO_PROMPT** - Repository-level clustering
   - Used for: Grouping components into modules at repository level
   - Logged in: `format_cluster_prompt()` when `module_tree == {}`

7. **CLUSTER_MODULE_PROMPT** - Sub-module clustering
   - Used for: Grouping components within an existing module
   - Logged in: `format_cluster_prompt()` when `module_tree != {}`

### Non-Markdown Prompts (No Logging Added)

These prompts return JSON, not markdown, so they don't need markdown validation rules:

- **CLUSTER_REPO_PROMPT** - Returns JSON grouping
- **CLUSTER_MODULE_PROMPT** - Returns JSON grouping
- **FILTER_FOLDERS_PROMPT** - Returns JSON file list

## Injected Components Tracking

All prompts that include Flamingo-specific content now log:

1. **Flamingo Custom Instructions Section** (`_CUSTOM_INSTRUCTIONS_SECTION`)
   - Length in characters
   - Preview of first 100 characters
   - Source: `codewiki/src/be/flamingo_guidelines.py`

2. **Flamingo Guidelines Section** (`_GUIDELINES_SECTION`)
   - Length in characters
   - Preview of first 100 characters
   - Source: `codewiki/src/be/flamingo_guidelines.py`

These sections are dynamically loaded from environment variables:
- `CODEWIKI_CUSTOM_INSTRUCTIONS_PATH`
- `CODEWIKI_GUIDELINES_PATH`

## Log Examples

### Example 1: Complex Module Processing

```
📝 Prompt Assembly Stage - SYSTEM_PROMPT (complex modules)
   ├─ Template: SYSTEM_PROMPT (complex modules)
   ├─ Module name: openframe-api
   ├─ Custom instructions: None
   ├─ Flamingo custom instructions section: 2,456 chars
   │  └─ Preview: You are working on the OpenFrame project...
   ├─ Flamingo guidelines section: 3,890 chars
   │  └─ Preview: ## Markdown Validation Rules...
   ├─ Base system prompt length: 15,234 chars
   ├─ Total assembled prompt: 21,580 chars (~5,395 tokens)
   └─ ✅ Prompt ready for LLM invocation

📝 Prompt Assembly Stage - USER_PROMPT
   ├─ Template: USER_PROMPT
   ├─ Module name: openframe-api
   ├─ Core component IDs: 12 components
   │  └─ Components: UserController, AuthService, JwtTokenProvider, UserRepository, SecurityConfig ... and 7 more
   ├─ Module tree context: 456 chars
   │  └─ Preview: openframe-api (current module)...
   ├─ Core component codes: 45,678 chars
   │  └─ Files included: 8 files
   ├─ Base USER_PROMPT length: 789 chars
   ├─ Total assembled prompt: 46,923 chars (~11,730 tokens)
   └─ ✅ Prompt ready for LLM invocation

📨 Agent Execution - User Prompt Ready
   ├─ Module: openframe-api
   ├─ Agent type: Complex (with sub-modules)
   ├─ User prompt length: 46,923 chars (~11,730 tokens)
   └─ 🚀 Invoking agent with formatted prompts...

🤖 LLM API Invocation
   ├─ Stage: main/generation
   ├─ Model: claude-sonnet-4-5-20250514
   ├─ Base URL: https://api.anthropic.com
   ├─ Prompt length: 68,503 chars (~17,125 tokens)
   │  └─ Preview: You are working on the OpenFrame project. This is a multi-platform system...
   ├─ Temperature: 0.0
   ├─ Max tokens: 128000 (field: max_tokens)
   ├─ Temperature supported: True
   └─ 🚀 Sending request to LLM API...

   ✅ LLM Response Received
   ├─ Response length: 12,345 chars (~3,086 tokens)
   └─ Preview: # OpenFrame API Service\n\nThe OpenFrame API Service is the central...
```

### Example 2: Module Clustering

```
🗂️  Module Clustering Operation
   ├─ Current module: openframe-services
   ├─ Module path: openframe-services
   ├─ Leaf nodes to cluster: 45
   └─ Components dictionary size: 234 components

   ├─ Potential components (with code): 48,000 tokens
   ├─ Max token per module: 36,369
   └─ ✅ Proceeding with clustering - components exceed threshold

📝 Prompt Assembly Stage - CLUSTER_MODULE_PROMPT
   ├─ Template: CLUSTER_MODULE_PROMPT
   ├─ Module name: openframe-services
   ├─ Potential core components: 120,000 chars
   │  └─ Preview: # openframe-gateway/src/main/java/Gateway.java...
   ├─ Module tree context: 2,345 chars
   │  └─ Preview: openframe-services (current module)...
   ├─ Base CLUSTER_MODULE_PROMPT length: 1,234 chars
   ├─ Total assembled prompt: 123,579 chars (~30,894 tokens)
   └─ ✅ Prompt ready for LLM invocation

🤖 Calling clustering LLM
   ├─ Model: gpt-4o-mini
   └─ Prompt assembled via format_cluster_prompt()

🤖 LLM API Invocation
   ├─ Stage: cluster
   ├─ Model: gpt-4o-mini
   ├─ Base URL: https://api.openai.com/v1
   ├─ Prompt length: 123,579 chars (~30,894 tokens)
   │  └─ Preview: Here is list of all potential core components...
   ├─ Temperature: 0.0
   ├─ Max tokens: 16384 (field: max_tokens)
   ├─ Temperature supported: True
   └─ 🚀 Sending request to LLM API...

   ✅ LLM Response Received
   ├─ Response length: 2,890 chars (~722 tokens)
   └─ Preview: <GROUPED_COMPONENTS>\n{\n    "gateway": {...
```

## Benefits

1. **Full Visibility**: Every prompt assembly and LLM call is logged with complete context
2. **Debugging**: Easy to trace prompt construction issues and identify which template is being used
3. **Token Tracking**: Approximate token counts help prevent context overflow
4. **Performance Monitoring**: Track prompt and response sizes across the pipeline
5. **Injection Tracking**: Clear visibility into custom instructions and guidelines injection
6. **Variable Substitution**: All variable replacements are logged with previews

## Testing

To see the logs in action:

```bash
# Enable verbose logging
export PYTHONUNBUFFERED=1

# Run documentation generation
python -m codewiki.cli.main generate \
  --repo-path /path/to/repo \
  --output-dir /path/to/output \
  --main-model claude-sonnet-4-5-20250514 \
  --cluster-model gpt-4o-mini \
  --verbose

# Logs will show:
# - All prompt template selections
# - Component lengths and previews
# - Variable substitutions
# - LLM API calls with full context
# - Response details
```

## Log Levels

- **INFO**: All prompt assembly and LLM invocation logs
- **WARNING**: Skipped clustering operations, missing components
- **ERROR**: LLM API failures with full context

## Future Enhancements

Potential improvements for the logging system:

1. Add structured logging (JSON format) for machine parsing
2. Track cumulative token usage per module
3. Log timing information for performance profiling
4. Add log filtering by prompt template type
5. Create visualization dashboard for token usage patterns
6. Export logs to external monitoring systems (Logfire, etc.)

---

**Implementation Status:** ✅ Complete
**Location:** CodeWiki repository at `/Users/michaelassraf/Documents/GitHub/CodeWiki`
