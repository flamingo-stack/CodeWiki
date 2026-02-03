# FQDN Clustering Updates

## Summary
Updated clustering logic to consistently use FQDN (Fully Qualified Domain Name) for component identification throughout the clustering pipeline.

## FQDN Format
The actual FQDN format uses dot notation:
- Format: `namespace.path/to/file.py::ComponentName`
- Main repo example: `main-repo.src/services/auth.py::AuthService`
- Dependency example: `deps/dep-repo-1.lib/auth.py::AuthProvider`

**Note:** The namespace is separated from the file path by a dot (`.`), NOT a slash (`/`).

## Changes Made

### 1. cluster_modules.py - Enhanced Validation and Logging

#### format_potential_core_components() function (lines 14-86)
**Changes:**
- Added comprehensive docstring documenting FQDN format for leaf_nodes and components dictionary
- Added debug logging showing FQDN format expectations at function entry
- Enhanced validation warnings to extract and display:
  - Namespace from FQDN (using dot separator, e.g., "main-repo" from "main-repo.src/...")
  - Source type (dependency repo vs main repo)
  - File path from FQDN (using :: separator)
- Added debug logging showing valid leaf node count and file grouping
- Added comment clarifying that leaf_node variable contains FQDN format

**Key improvements:**
```python
# Before: Generic warning
logger.warning(f"Skipping invalid leaf node '{leaf_node}'...")

# After: Detailed FQDN-aware warning
logger.warning(
    f"Skipping invalid leaf node '{leaf_node}'{file_hint}\n"
    f"   ├─ FQDN format: {leaf_node}\n"
    f"   ├─ Namespace: {namespace or '(unknown)'}\n"
    f"   ├─ Source: {'dependency repo' if is_deps else 'main repo'}\n"
    ...
)
```

**Namespace extraction logic:**
```python
# Extract namespace from FQDN (e.g., "main-repo" from "main-repo.src/...")
namespace = ""
is_deps = False
if '.' in leaf_node:
    namespace = leaf_node.split('.')[0]  # Split on dot, not slash
    is_deps = namespace.startswith('deps/')
```

#### cluster_modules() sub-module validation (lines 173-202)
**Changes:**
- Enhanced sub-module validation to extract namespace from FQDN using dot separator
- Identify dependency repos vs main repo
- Improved warning messages with FQDN context

### 2. prompt_template.py - LLM Instructions for FQDN Preservation

#### CLUSTER_REPO_PROMPT (lines 617-653)
**Changes:**
- Added IMPORTANT section explaining FQDN format with correct examples using dot notation
- Explicitly instructs LLM to preserve exact component IDs from input
- Added example output showing full FQDN format in component lists
- Shows both main repo and dependency repo FQDN examples

**Key addition:**
```
IMPORTANT: Component IDs use FQDN (Fully Qualified Domain Name) format that includes namespace prefixes.
Example formats:
  - Main repo: "main-repo.src/services/auth.py::AuthService"
  - Dependencies: "deps/dep-repo-1.lib/auth.py::AuthProvider"

You MUST preserve the exact component ID format from the input. DO NOT remove namespace prefixes or modify the IDs.
```

#### CLUSTER_MODULE_PROMPT (lines 655-697)
**Changes:**
- Same FQDN preservation instructions as CLUSTER_REPO_PROMPT
- Ensures sub-module clustering also preserves full FQDN format with dot notation

## Architecture Guarantee

### FQDN Creation (ast_parser.py)
```python
# From ast_parser.py line 229
fqdn = f"{namespace}.{original_id}"  # Dot separator!

# Example: "main-repo.src/services/auth.py::AuthService"
# Where:
#   - namespace = "main-repo"
#   - original_id = "src/services/auth.py::AuthService"
```

### Data Flow
1. **Input to clustering**: leaf_nodes list contains FQDN strings (dot-separated namespace)
2. **Components dictionary**: Keys are FQDNs (node.id)
3. **Validation**: `if leaf_node in components` works with FQDN
4. **LLM prompt**: Components sent to LLM include full FQDN
5. **LLM response**: Explicit instructions to preserve FQDN format
6. **Output validation**: Checks returned component IDs against FQDN dictionary

### Key Principle
**All component IDs flowing through clustering use FQDN format with dot-separated namespaces.** No conversion or stripping occurs.

## Benefits

1. **Consistent namespacing**: Main repo vs dependency repos always distinguishable
2. **Better debugging**: Logs show exact FQDN format and source
3. **LLM reliability**: Explicit instructions prevent ID mangling
4. **Validation accuracy**: FQDN-aware error messages help identify issues
5. **Cross-repo support**: Dependencies properly tracked alongside main repo code

## Testing Recommendations

1. Run clustering on multi-repo setup (main + deps)
2. Verify log messages show namespace information
3. Check LLM output preserves full FQDN format with dot notation
4. Confirm validation warnings include deps vs main distinction
5. Verify namespace extraction uses dot separator (`.split('.')`)
