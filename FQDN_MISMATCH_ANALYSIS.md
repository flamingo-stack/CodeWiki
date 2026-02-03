# FQDN Format Mismatch - Root Cause Analysis

## Error Summary

**Failed Component ID:**
```
deps.openframe-oss-lib.openframe-management-service-core.src.main.java.com.openframe.management.config.pinot.PintoConfigInitializer.PinotConfigInitializer
```

**Error Message:**
```
❌ Failed to normalize 'deps.openframe-oss-lib.openframe-management-service-core.src.main.java.com.openframe.management.config.pinot.PintoConfigInitializer.PinotConfigInitializer'
      ├─ Not found as exact FQDN in components
      ├─ Not found in short_id → FQDN mapping
      └─ Available similar short IDs: []
```

## Root Cause Analysis

### Issue A: LLM Adding "deps." Prefix

**Problem:** The LLM is prepending "deps." to component IDs, but the actual FQDN format doesn't include this prefix.

**How FQDN is Actually Constructed:**
```python
# From ast_parser.py:185-196
def _get_namespace_from_path(self, repo_path: str) -> str:
    """Generate a namespace prefix from a repository path."""
    return os.path.basename(repo_path.rstrip(os.sep))

# From ast_parser.py:228-229
# Create FQDN (namespaced component ID)
fqdn = f"{namespace}.{original_id}"
```

**Example:**
- **Repository Path:** `/path/to/deps/openframe-oss-lib`
- **Namespace Extraction:** `os.path.basename()` → `openframe-oss-lib` (NOT "deps")
- **Actual FQDN:** `openframe-oss-lib.{component_path}`
- **LLM Returned:** `deps.openframe-oss-lib.{component_path}` ❌

**Root Cause:** The LLM sees the directory structure (`deps/openframe-oss-lib`) and incorrectly assumes "deps" is part of the namespace.

### Issue B: Nested Repository Directories

**Problem:** The component ID includes intermediate directory layers that may or may not be part of the namespace.

**LLM Returned:**
```
deps.openframe-oss-lib.openframe-management-service-core.src.main.java...
         ^namespace^      ^intermediate directory^    ^Java package path^
```

**Expected Format (Based on Test):**
```
openframe-oss-lib.src.main.java.com.openframe.management.config.pinot.PinotConfigInitializer.PinotConfigInitializer
^namespace^       ^component path (file path + class name)^
```

**Question:** Is `openframe-management-service-core` an intermediate directory, or is it part of the original component ID?

### Issue C: Double Class Name at End

**Observation:** The component ID ends with `PintoConfigInitializer.PinotConfigInitializer`

**Possible Explanations:**
1. **Directory + Class:** A directory named `PintoConfigInitializer` containing a class `PinotConfigInitializer`
2. **Typo in LLM Output:** Should be just one occurrence
3. **Java Inner Class:** Outer class and inner class with similar names

**Note:** This might be valid if the Java file structure is:
```
pinot/PintoConfigInitializer/PinotConfigInitializer.java
```

## Expected vs Actual FQDN Format

### Expected Format (From Test Cases)
```
<namespace>.<component_path>

Examples:
- main-repo.src.services.user_service.UserService
- dep-repo-1.lib.auth.auth_helper.AuthHelper
- dep-repo-2.core.models.base_model.BaseModel
```

**Pattern:** `{repo_basename}.{file_path_as_dots}.{class_or_function_name}`

### Actual LLM Return
```
deps.openframe-oss-lib.openframe-management-service-core.src.main.java.com.openframe.management.config.pinot.PintoConfigInitializer.PinotConfigInitializer
^extra^ ^namespace^      ^may be intermediate dir^          ^Java package path^                                    ^component^
```

## Proposed Fixes

### Fix 1: Strip "deps." Prefix in Normalization

**Location:** `/Users/michaelassraf/Documents/GitHub/CodeWiki/codewiki/src/be/cluster_modules.py:212-224`

**Current Code:**
```python
for comp_id in original_components:
    # Try exact FQDN match first
    if comp_id in components:
        normalized_components.append(comp_id)
    # Try reverse mapping from short ID
    elif comp_id in short_to_fqdn:
        fqdn = short_to_fqdn[comp_id]
        normalized_components.append(fqdn)
        total_normalized += 1
    else:
        # Keep original (will fail validation later)
        normalized_components.append(comp_id)
        total_failed += 1
```

**Proposed Enhancement:**
```python
for comp_id in original_components:
    # Try exact FQDN match first
    if comp_id in components:
        normalized_components.append(comp_id)
        continue

    # Try reverse mapping from short ID
    if comp_id in short_to_fqdn:
        fqdn = short_to_fqdn[comp_id]
        normalized_components.append(fqdn)
        total_normalized += 1
        continue

    # FIX 1: Try stripping "deps." prefix if present
    stripped_id = comp_id
    if comp_id.startswith("deps."):
        stripped_id = comp_id[5:]  # Remove "deps." prefix
        logger.debug(f"   🔧 Stripping 'deps.' prefix: '{comp_id}' → '{stripped_id}'")

        # Try exact match with stripped ID
        if stripped_id in components:
            normalized_components.append(stripped_id)
            total_normalized += 1
            logger.debug(f"   ✅ Found component after stripping prefix")
            continue

        # Try short_id mapping with stripped ID
        if stripped_id in short_to_fqdn:
            fqdn = short_to_fqdn[stripped_id]
            normalized_components.append(fqdn)
            total_normalized += 1
            logger.debug(f"   ✅ Mapped to FQDN: '{fqdn}'")
            continue

    # FIX 2: Try fuzzy substring matching
    # Extract the likely component name (last segment)
    component_name = comp_id.split('.')[-1]

    # Search for FQDNs containing this component name
    fuzzy_matches = [
        fqdn for fqdn in components.keys()
        if component_name in fqdn.split('.')
    ]

    if len(fuzzy_matches) == 1:
        # Unique match found
        normalized_components.append(fuzzy_matches[0])
        total_normalized += 1
        logger.debug(f"   ✅ Fuzzy matched '{comp_id}' → '{fuzzy_matches[0]}'")
        continue
    elif len(fuzzy_matches) > 1:
        logger.warning(
            f"   ⚠️  Multiple fuzzy matches for '{comp_id}':\n"
            f"      {fuzzy_matches[:5]}\n"
            f"      Keeping original (ambiguous)"
        )

    # All attempts failed - keep original (will fail validation)
    normalized_components.append(comp_id)
    total_failed += 1

    # Enhanced debug info
    logger.warning(
        f"   ❌ Failed to normalize '{comp_id}'\n"
        f"      ├─ Not found as exact FQDN in components\n"
        f"      ├─ Not found in short_id → FQDN mapping\n"
        f"      ├─ Stripped version: '{stripped_id}'\n"
        f"      ├─ Component name: '{component_name}'\n"
        f"      ├─ Fuzzy matches: {len(fuzzy_matches)}\n"
        f"      └─ Similar short IDs: {[k for k in short_to_fqdn.keys() if component_name.lower() in k.lower()][:5]}"
    )
```

### Fix 2: Enhanced Short ID Extraction

**Location:** `/Users/michaelassraf/Documents/GitHub/CodeWiki/codewiki/src/be/cluster_modules.py:89-120`

**Problem:** The `build_short_id_to_fqdn_map` function might not handle nested directory structures correctly.

**Current Logic:**
```python
short_id = node.short_id  # Relies on node.short_id being set correctly

if not short_id:
    # Fallback: extract from FQDN
    if '::' in fqdn:
        short_id = fqdn.split('::')[-1]
    else:
        short_id = fqdn.split('.')[-1]
```

**Proposed Enhancement:**
```python
# Extract short ID with multiple fallback strategies
short_id = node.short_id

if not short_id:
    # Strategy 1: Class notation (::)
    if '::' in fqdn:
        short_id = fqdn.split('::')[-1]
    # Strategy 2: Last segment after namespace
    else:
        segments = fqdn.split('.')
        # Skip namespace (first segment) and get component name (last segment)
        short_id = segments[-1] if len(segments) > 1 else fqdn

# ADDITION: Also map intermediate segments for nested structures
# Example: openframe-oss-lib.openframe-management-service-core.src.main.java.Class
# Should map both:
#   - "Class" → full FQDN
#   - "src.main.java.Class" → full FQDN (partial path)
segments = fqdn.split('.')
if len(segments) > 2:
    # Map progressively longer suffixes
    # This helps match LLM outputs that include partial paths
    for i in range(1, min(4, len(segments))):  # Limit to 3 levels deep
        partial_id = '.'.join(segments[-i:])
        if partial_id not in mapping:
            mapping[partial_id] = fqdn
        else:
            collisions[partial_id].append(fqdn)
```

### Fix 3: Update LLM Prompt to Avoid "deps." Prefix

**Location:** `/Users/michaelassraf/Documents/GitHub/CodeWiki/codewiki/src/be/prompt_template.py`

**Add to System Prompt:**
```python
IMPORTANT - Component ID Format:
- Component IDs MUST use the exact FQDN format from the components list
- DO NOT add "deps." or any other prefix to component IDs
- The namespace is already part of the FQDN (e.g., "openframe-oss-lib.path.to.Component")
- CORRECT: "openframe-oss-lib.src.main.java.com.openframe.Class"
- WRONG: "deps.openframe-oss-lib.src.main.java.com.openframe.Class"

Format Examples:
- main-repo.src.services.user_service.UserService
- ui-kit.components.ui.button.Button
- openframe-api.src.main.java.com.openframe.api.service.AuthService

When referencing components from the provided list, use the EXACT ID shown, including:
1. Namespace prefix (repository name)
2. Full file path (using dots as separators)
3. Component name (class/function)
```

## Testing Strategy

### Test Case 1: Strip "deps." Prefix
```python
# Input
comp_id = "deps.openframe-oss-lib.src.main.java.Class"

# Expected behavior
stripped = "openframe-oss-lib.src.main.java.Class"
assert stripped in components
```

### Test Case 2: Fuzzy Substring Match
```python
# Input
comp_id = "deps.openframe-oss-lib.openframe-management-service-core.src.main.java.PinotConfigInitializer.PinotConfigInitializer"

# Extract component name
component_name = "PinotConfigInitializer"

# Search in actual FQDNs
matches = [fqdn for fqdn in components if component_name in fqdn]

# Should find the actual FQDN
assert len(matches) == 1
actual_fqdn = matches[0]  # e.g., "openframe-oss-lib.src.main.java.config.pinot.PinotConfigInitializer"
```

### Test Case 3: Verify Component Exists
```python
# Before applying fixes, verify the component actually exists
# Run CodeWiki and check logs for:
grep -i "pinotconfig" /path/to/logs/output.log

# Expected to find:
# - Component registration line
# - Actual FQDN format
# - Namespace assignment
```

## Next Steps

1. **Verify Component Exists**
   - Run CodeWiki on the actual openframe-oss-lib repository
   - Check if `PinotConfigInitializer` was parsed
   - Get the actual FQDN format from logs

2. **Implement Fix 1**
   - Add "deps." prefix stripping to normalization logic
   - Add fuzzy matching fallback
   - Test with known failing component ID

3. **Implement Fix 2**
   - Enhance short ID mapping with partial paths
   - Handle nested directory structures
   - Test with multi-level Java packages

4. **Update LLM Prompt**
   - Add explicit format requirements
   - Provide correct examples
   - Re-run clustering after prompt update

5. **Add Validation**
   - Log all normalization attempts with details
   - Track which fix strategy succeeded
   - Report statistics on fix effectiveness

## Questions to Answer

1. **Does the component exist?**
   - Need to check actual parsing logs
   - Verify it wasn't filtered during AST analysis

2. **What is the actual FQDN?**
   - Run: `grep -i "pinotconfig" logs/*.log`
   - Check component registration lines

3. **Is "openframe-management-service-core" a directory?**
   - Need to see actual repository structure
   - May be legitimate intermediate directory

4. **Why does LLM add "deps." prefix?**
   - Is it seeing directory names in component descriptions?
   - Is the prompt providing directory context that confuses it?

## Success Criteria

✅ **Fix is successful when:**
1. Zero "Failed to normalize" warnings for valid components
2. LLM-returned component IDs are correctly mapped to actual FQDNs
3. Fuzzy matching successfully resolves partial path matches
4. Detailed logging shows which fix strategy was used
5. No false positives (non-existent components still fail validation)

✅ **Acceptable outcomes:**
- Non-existent components still fail (LLM hallucination)
- Components filtered during parsing still fail (not a normalization issue)
- Ambiguous matches are reported with suggestions (better UX)
