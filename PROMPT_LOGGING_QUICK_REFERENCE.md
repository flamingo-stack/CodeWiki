# CodeWiki Prompt Logging - Quick Reference

## Log Symbols Reference

| Symbol | Meaning | Used For |
|--------|---------|----------|
| 📝 | Prompt Assembly | Template selection and prompt building |
| 🤖 | LLM API Call | API invocations to language models |
| ✅ | Success | Completed operations |
| 📨 | Agent Execution | Agent system running with prompts |
| 🗂️ | Clustering | Module clustering operations |
| 📄 | Documentation | Document generation events |
| 📚 | Repository | Repository-level operations |
| 🚀 | Sending | Data being sent to API |
| ⏭️ | Skipped | Operation skipped (not needed) |
| ⚠️ | Warning | Non-fatal issues |
| ❌ | Error | Failed operations |

## Files with Logging

### Core Prompt Files
```
codewiki/src/be/prompt_template.py    - 7 functions enhanced
codewiki/src/be/llm_services.py       - 1 function enhanced
codewiki/src/be/agent_orchestrator.py - 1 function enhanced
codewiki/src/be/cluster_modules.py    - 1 function enhanced
codewiki/src/be/documentation_generator.py - 1 function enhanced
```

## Quick Grep Commands

### Find all prompt assembly logs
```bash
grep "📝 Prompt Assembly" codewiki/src/be/*.py
```

### Find all LLM API calls
```bash
grep "🤖 LLM API" codewiki/src/be/*.py
```

### Find all template selections
```bash
grep "Template:" codewiki/src/be/*.py
```

### Find all token estimates
```bash
grep "~.*tokens" codewiki/src/be/*.py
```

### Find all prompt previews
```bash
grep "Preview:" codewiki/src/be/*.py
```

## Template Quick Reference

| Template | File | Function | Purpose |
|----------|------|----------|---------|
| SYSTEM_PROMPT | prompt_template.py:16 | format_system_prompt() | Complex module system prompt |
| LEAF_SYSTEM_PROMPT | prompt_template.py:335 | format_leaf_system_prompt() | Leaf module system prompt |
| USER_PROMPT | prompt_template.py:536 | format_user_prompt() | Module documentation request |
| REPO_OVERVIEW_PROMPT | prompt_template.py:549 | format_repo_overview_prompt() | Repository overview generation |
| MODULE_OVERVIEW_PROMPT | prompt_template.py:583 | format_module_overview_prompt() | Parent module overview |
| CLUSTER_REPO_PROMPT | prompt_template.py:617 | format_cluster_prompt() | Repository-level clustering |
| CLUSTER_MODULE_PROMPT | prompt_template.py:648 | format_cluster_prompt() | Sub-module clustering |

## Prompt Assembly Locations

### System Prompts (Agent Configuration)
- **Function:** `AgentOrchestrator.create_agent()` in `agent_orchestrator.py:68`
- **Calls:**
  - `format_system_prompt()` - For complex modules
  - `format_leaf_system_prompt()` - For leaf modules

### User Prompts (Agent Execution)
- **Function:** `AgentOrchestrator.process_module()` in `agent_orchestrator.py:95`
- **Calls:** `format_user_prompt()`

### Clustering Prompts
- **Function:** `cluster_modules()` in `cluster_modules.py:67`
- **Calls:** `format_cluster_prompt()`

### Overview Prompts
- **Function:** `DocumentationGenerator.generate_parent_module_docs()` in `documentation_generator.py:231`
- **Calls:**
  - `format_repo_overview_prompt()` - For repository level
  - `format_module_overview_prompt()` - For parent modules

## LLM API Invocation Points

### Direct LLM Calls
```python
# File: llm_services.py
# Function: call_llm(prompt, config, model, temperature)
# Line: ~336

# Logs:
# - Before: Stage, model, base URL, prompt details, temperature, max tokens
# - After: Response length and preview
```

### Agent-Based Calls (Automatic)
```python
# File: agent_orchestrator.py
# Function: process_module()
# Line: ~149

# Uses Pydantic AI Agent which calls LLMs internally
# Logs show user prompt preparation before agent.run()
```

## Token Estimation Formula

All logs use this approximation:
```python
estimated_tokens = len(text) // 4
```

This is a rough estimate. Actual tokenization varies by model:
- GPT models: ~4 chars/token (English)
- Claude models: ~4 chars/token (English)
- Actual values: Use tiktoken or model-specific tokenizers

## Injected Content Sources

### Flamingo Custom Instructions
- **Environment Variable:** `CODEWIKI_CUSTOM_INSTRUCTIONS_PATH`
- **Loaded in:** `flamingo_guidelines.py:get_custom_instructions_section()`
- **Injected into:** All SYSTEM_PROMPT and LEAF_SYSTEM_PROMPT templates
- **Logged as:** "Flamingo custom instructions section"

### Flamingo Guidelines
- **Environment Variable:** `CODEWIKI_GUIDELINES_PATH`
- **Loaded in:** `flamingo_guidelines.py:get_guidelines_section()`
- **Injected into:** All documentation generation prompts
- **Logged as:** "Flamingo guidelines section"

## Example Log Flow

### 1. Module Processing Starts
```
📝 Processing module: openframe-api
   └─ Core components: 12
```

### 2. System Prompt Assembly
```
📝 Prompt Assembly Stage - SYSTEM_PROMPT (complex modules)
   ├─ Module name: openframe-api
   ├─ Custom instructions: None
   ├─ Flamingo custom instructions section: 2,456 chars
   ├─ Flamingo guidelines section: 3,890 chars
   ├─ Total assembled prompt: 21,580 chars (~5,395 tokens)
   └─ ✅ Prompt ready for LLM invocation
```

### 3. User Prompt Assembly
```
📝 Prompt Assembly Stage - USER_PROMPT
   ├─ Module name: openframe-api
   ├─ Core component IDs: 12 components
   ├─ Core component codes: 45,678 chars
   ├─ Total assembled prompt: 46,923 chars (~11,730 tokens)
   └─ ✅ Prompt ready for LLM invocation
```

### 4. Agent Execution
```
📨 Agent Execution - User Prompt Ready
   ├─ Module: openframe-api
   ├─ Agent type: Complex (with sub-modules)
   ├─ User prompt length: 46,923 chars (~11,730 tokens)
   └─ 🚀 Invoking agent with formatted prompts...
```

### 5. LLM API Call
```
🤖 LLM API Invocation
   ├─ Stage: main/generation
   ├─ Model: claude-sonnet-4-5-20250514
   ├─ Prompt length: 68,503 chars (~17,125 tokens)
   ├─ Temperature: 0.0
   ├─ Max tokens: 128000 (field: max_tokens)
   └─ 🚀 Sending request to LLM API...
```

### 6. Response Received
```
   ✅ LLM Response Received
   ├─ Response length: 12,345 chars (~3,086 tokens)
   └─ Preview: # OpenFrame API Service...
```

## Debugging Tips

### Check if prompt assembly is working
```bash
python -m codewiki.cli.main generate ... 2>&1 | grep "📝 Prompt Assembly"
```

### Check all LLM calls
```bash
python -m codewiki.cli.main generate ... 2>&1 | grep "🤖 LLM"
```

### Check token usage
```bash
python -m codewiki.cli.main generate ... 2>&1 | grep "tokens)"
```

### Check for errors
```bash
python -m codewiki.cli.main generate ... 2>&1 | grep "❌"
```

### Extract all prompt previews
```bash
python -m codewiki.cli.main generate ... 2>&1 | grep "Preview:" | cut -d: -f2-
```

## Common Issues

### Issue: No prompt logs appearing
**Cause:** Logger level set too high
**Fix:** Ensure `--verbose` flag is used or set logging level to INFO

### Issue: Token estimates seem wrong
**Cause:** Using character-based approximation (4 chars/token)
**Fix:** This is expected - it's an approximation. For exact counts, use tiktoken

### Issue: Too many logs
**Cause:** Verbose logging enabled
**Fix:** Remove `--verbose` flag for production runs

### Issue: Missing Flamingo sections
**Cause:** Environment variables not set
**Check:**
```bash
echo $CODEWIKI_CUSTOM_INSTRUCTIONS_PATH
echo $CODEWIKI_GUIDELINES_PATH
```

## Performance Impact

The logging additions have minimal performance impact:
- **String length calculations:** O(1) in Python
- **String slicing (previews):** O(n) but limited to 100-150 chars
- **Token estimation:** Simple division operation
- **Log I/O:** Async write to console/file

Estimated overhead: < 0.1% of total execution time

## Testing the Logging

```bash
# Test with a small repository
cd /path/to/small-repo
python -m codewiki.cli.main generate \
  --repo-path . \
  --output-dir ./docs \
  --main-model claude-sonnet-4-5-20250514 \
  --cluster-model gpt-4o-mini \
  --verbose 2>&1 | tee codewiki.log

# Analyze the log
grep "📝 Prompt Assembly" codewiki.log | wc -l  # Count prompt assemblies
grep "🤖 LLM API" codewiki.log | wc -l         # Count LLM calls
grep "tokens)" codewiki.log                     # View all token estimates
```

---

**Last Updated:** 2025-02-02
**CodeWiki Version:** Current fork with SYNTHETIC_MODULE_PATCH
