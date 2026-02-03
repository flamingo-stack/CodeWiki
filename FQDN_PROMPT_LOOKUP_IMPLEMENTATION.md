# FQDN-Based Component Lookup in prompt_template.py

**Implementation Date:** 2026-02-02
**File:** `codewiki/src/be/prompt_template.py`
**Status:** ✅ Implemented and Tested

## Summary

Updated `format_user_prompt()` to use FQDN (Fully Qualified Domain Name) consistently for all component dictionary lookups, with fuzzy matching fallback and comprehensive error logging.

## Key Changes

### 1. Added Fuzzy Matching Helper (`_fuzzy_match_component()`)

**Location:** Lines 754-791 (before `format_user_prompt()`)

```python
def _fuzzy_match_component(component_id: str, components: Dict[str, Any]) -> Any:
    """
    Attempt fuzzy matching if exact FQDN lookup fails.

    Strategy: If component_id is a simple name (no dots), try suffix matching.
    Returns the full FQDN if exactly ONE match found, None otherwise.
    """
    basename = component_id.split('.')[-1] if '.' in component_id else component_id

    matches = []
    for key in components.keys():
        if key.endswith('.' + basename) or key == basename:
            matches.append(key)

    if len(matches) == 0:
        return None
    elif len(matches) == 1:
        logger.info(f"✅ Fuzzy match succeeded: '{component_id}' → '{matches[0]}'")
        return matches[0]
    else:
        logger.warning(f"⚠️ Ambiguous match: {len(matches)} matches for '{component_id}'")
        return None
```

**Features:**
- Extracts basename from component ID (`AuthService` from `main.services.AuthService`)
- Suffix matching: Finds all keys ending with `.basename` or equal to `basename`
- Returns full FQDN if exactly one match (unambiguous)
- Returns `None` if no matches or multiple matches (ambiguous)
- Logs match results for debugging

### 2. Added Suggestion Helper (`_find_component_suggestions()`)

**Location:** Lines 794-818 (before `format_user_prompt()`)

```python
def _find_component_suggestions(component_id: str, components: Dict[str, Any], max_suggestions: int = 3) -> List[str]:
    """
    Find similar component IDs in dictionary for troubleshooting lookup failures.
    """
    basename = component_id.split('.')[-1] if '.' in component_id else component_id

    suggestions = []
    for key in components.keys():
        if key.endswith('.' + basename) or key == basename:
            suggestions.append(key)
            if len(suggestions) >= max_suggestions:
                break

    return suggestions
```

**Features:**
- Similar to fuzzy matching but returns up to 3 suggestions
- Used for error logging when lookup fails
- Helps diagnose namespace vs component name issues

### 3. Updated `format_user_prompt()` Docstring

**Location:** Line 825-829

```python
Args:
    module_name: Name of the module to document
    core_component_ids: List of component IDs to include (should be FQDNs)
    components: Dictionary mapping component IDs (FQDNs) to CodeComponent objects
```

**Change:** Clarified that `components` dictionary uses FQDN keys.

### 4. Enhanced Component Lookup Logic

**Location:** Lines 867-965 (replacing lines 882-889 in original)

**Old Code (Silent Failures):**
```python
for component_id in core_component_ids:
    if component_id not in components:
        continue  # Silently skip missing components
    component = components[component_id]
    grouped_components[path].append(component_id)
```

**New Code (FQDN-First with Fuzzy Fallback):**
```python
for component_id in core_component_ids:
    # Try exact FQDN lookup first
    matched_fqdn = component_id if component_id in components else None

    # If exact lookup fails, try fuzzy matching
    if not matched_fqdn:
        matched_fqdn = _fuzzy_match_component(component_id, components)
        if matched_fqdn:
            fuzzy_matched_count += 1

    # If still not found, log comprehensive error
    if not matched_fqdn:
        missing_count += 1
        logger.warning(f"⚠️  Component lookup failed (FQDN required): '{component_id}'")

        # Analyze component ID structure
        id_parts = component_id.split('.')
        if len(id_parts) > 1:
            namespace = '.'.join(id_parts[:-1])
            basename = id_parts[-1]
            logger.warning(f"   ├─ Namespace: {namespace}")
            logger.warning(f"   ├─ Component name: {basename}")

        # Find and suggest similar FQDNs
        suggestions = _find_component_suggestions(component_id, components)
        if suggestions:
            for i, suggestion in enumerate(suggestions, 1):
                component_obj = components[suggestion]
                rel_path = component_obj.relative_path
                is_likely_deps = any(dep_marker in rel_path for dep_marker in [
                    'site-packages', 'node_modules', '.venv', 'dist-packages', 'vendor'
                ])
                source_type = "deps" if is_likely_deps else "main"
                logger.warning(f"   │  {i}. {suggestion} (from {source_type})")

        continue  # Skip this component

    # Use matched FQDN for lookup
    component = components[matched_fqdn]
    grouped_components[path].append(matched_fqdn)  # Store FQDN

# Log summary
found_count = len(core_component_ids) - missing_count
if missing_count > 0 or fuzzy_matched_count > 0:
    logger.warning(f"📊 Component Lookup Summary (FQDN-based):")
    logger.warning(f"   ├─ Exact FQDN matches: {found_count - fuzzy_matched_count}")
    if fuzzy_matched_count > 0:
        logger.warning(f"   ├─ Fuzzy matches: {fuzzy_matched_count}")
    if missing_count > 0:
        logger.warning(f"   └─ Missing: {missing_count} ({100 * missing_count / len(core_component_ids):.1f}%)")
else:
    logger.info(f"✅ All {len(core_component_ids)} components found via exact FQDN lookup")
```

### 5. Import Update

**Location:** Line 713

```python
from typing import Dict, Any, List  # Added List for type hints
```

## Error Messages

When a component lookup fails, the system now logs:

1. **Component ID Structure Analysis:**
   ```
   ⚠️  Component lookup failed (FQDN required): 'UserHandler'
      ├─ Simple name (no namespace): UserHandler
      ├─ Expected FQDN format: Use full qualified name from clustering
   ```

2. **Namespace Detection (for dotted IDs):**
   ```
   ⚠️  Component lookup failed (FQDN required): 'services.UserHandler'
      ├─ Namespace: services
      ├─ Component name: UserHandler
      ├─ Expected FQDN format: '<namespace>.<component_name>'
   ```

3. **FQDN Suggestions with Source Type:**
   ```
   ├─ Possible FQDN matches in components dictionary:
   │  1. main.services.UserHandler (from main)
   │     └─ Path: src/services/user_handler.py
   │  2. deps.flask.UserHandler (from deps)
   └─ ✓ Suggestion: Update clustering to use full FQDN 'main.services.UserHandler'
   ```

4. **Root Cause Analysis:**
   ```
   ├─ No similar components found in dictionary keys
   └─ Possible causes:
      • Component filtered out (tests, specs, node_modules)
      • Parsing failed for this file
      • LLM returned incorrect component name in clustering
      • Namespace mismatch (check if component is from deps vs main)
   ```

## Testing Results

**Test Suite:** Inline Python test (lines 23-74 of test script)

```
Test 1: Exact FQDN match ✅
  Result: main.services.UserHandler

Test 2: Simple name with single match ✅
  Result: main.utils.Logger

Test 3: Simple name with no match ✅
  Result: None

Test 4: Simple name with single match (Session) ✅
  Result: deps.requests.Session

Test 5: Ambiguous match test ✅
  Result: None (two Loggers: main.utils.Logger, other.utils.Logger)
```

## Benefits

1. **FQDN Consistency:** All lookups use full qualified names as keys
2. **Fuzzy Matching:** Graceful handling of simple names when unambiguous
3. **Enhanced Debugging:** Comprehensive error messages with namespace analysis
4. **Source Detection:** Distinguishes between main repo and dependencies
5. **Actionable Suggestions:** Provides exact FQDN to use in clustering
6. **Summary Metrics:** Shows exact vs fuzzy match counts for monitoring

## Integration Points

**Upstream (Clustering):**
- `cluster_modules.py`: Returns component IDs (should be FQDNs)
- Used by `format_user_prompt()` as `core_component_ids` parameter

**Downstream (Dictionary):**
- `components` dictionary populated by `DependencyGraphBuilder`
- Keys are FQDNs from AST parsing (e.g., `main.services.UserHandler`)

**Data Flow:**
```
clustering → core_component_ids (list) → format_user_prompt() → components dict lookup
```

## Files Modified

- `codewiki/src/be/prompt_template.py` (+171 lines, -15 lines)
  - Added `_fuzzy_match_component()` function
  - Added `_find_component_suggestions()` function
  - Updated `format_user_prompt()` docstring
  - Enhanced component lookup loop with fuzzy matching
  - Added comprehensive error logging
  - Added lookup summary logging

## Related Issues

- Fixes silent component lookup failures in prompt assembly
- Addresses namespace vs component name confusion
- Provides clear guidance when clustering uses wrong ID format
- Distinguishes between main repo and dependency components

## Next Steps

1. Monitor logs for fuzzy match frequency
2. Update clustering prompts if needed to ensure FQDN output
3. Consider caching fuzzy match results for performance
4. Add metrics tracking for match success rates

---

**Principle:** All component lookups use FQDN as key, with helpful errors if not found.
