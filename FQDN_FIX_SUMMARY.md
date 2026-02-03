# FQDN Format Mismatch - Complete Fix Summary

## Executive Summary

**Problem:** LLM-returned component IDs fail normalization because they include a "deps." prefix that doesn't exist in actual FQDNs.

**Root Cause:** The LLM sees directory structure (`deps/openframe-oss-lib`) and incorrectly includes "deps" as part of the namespace, but the actual FQDN construction only uses the repository basename (`openframe-oss-lib`).

**Solution:** Implement multi-strategy normalization with prefix stripping, fuzzy matching, and enhanced logging.

## Error Analysis

### Failed Component ID
```
deps.openframe-oss-lib.openframe-management-service-core.src.main.java.com.openframe.management.config.pinot.PintoConfigInitializer.PinotConfigInitializer
```

### Breaking Down the Issue

| Component | Source | Status |
|-----------|--------|--------|
| `deps` | LLM-added prefix | ❌ Should not exist |
| `openframe-oss-lib` | Actual namespace | ✅ Correct |
| `openframe-management-service-core` | Intermediate directory? | ❓ Unknown |
| `src.main.java.com.openframe...` | Java package path | ✅ Expected |
| `PintoConfigInitializer.PinotConfigInitializer` | Directory + Class? | ❓ Needs verification |

## How FQDN is Actually Constructed

```python
# From ast_parser.py:185-196
def _get_namespace_from_path(self, repo_path: str) -> str:
    """Generate a namespace prefix from a repository path."""
    return os.path.basename(repo_path.rstrip(os.sep))

# Example:
# Input:  /path/to/deps/openframe-oss-lib
# Output: openframe-oss-lib  (NOT "deps.openframe-oss-lib")

# From ast_parser.py:228-229
fqdn = f"{namespace}.{original_id}"

# Result: openframe-oss-lib.src.main.java.Class
# NOT:    deps.openframe-oss-lib.src.main.java.Class
```

## Proposed Fix Strategy

### 1. Enhanced Normalization (5 Strategies)

**Implementation:** Replace `cluster_modules.py:212-233`

```python
# Strategy 1: Exact FQDN match (existing)
if comp_id in components:
    return comp_id

# Strategy 2: Short ID mapping (existing)
if comp_id in short_to_fqdn:
    return short_to_fqdn[comp_id]

# Strategy 3: Strip "deps." prefix (NEW)
if comp_id.startswith("deps."):
    stripped = comp_id[5:]
    if stripped in components or stripped in short_to_fqdn:
        return normalize(stripped)

# Strategy 4: Fuzzy match by component name (NEW)
component_name = comp_id.split('.')[-1]
matches = [fqdn for fqdn in components if fqdn.endswith(component_name)]
if len(matches) == 1:
    return matches[0]

# Strategy 5: Match by path suffix (NEW)
# Try last 2-4 segments: "config.pinot.Class" matches "*.config.pinot.Class"
for n in range(2, 5):
    suffix = '.'.join(comp_id.split('.')[-n:])
    matches = [fqdn for fqdn in components if fqdn.endswith(suffix)]
    if len(matches) == 1:
        return matches[0]
```

### 2. Enhanced Short ID Mapping

**Implementation:** Replace `build_short_id_to_fqdn_map()`

```python
# Current: Maps only final component name
mapping["UserService"] = "main-repo.src.services.UserService"

# Enhanced: Maps partial paths too
mapping["UserService"] = "main-repo.src.services.UserService"
mapping["services.UserService"] = "main-repo.src.services.UserService"
mapping["src.services.UserService"] = "main-repo.src.services.UserService"

# Helps match LLM outputs with partial paths
```

### 3. LLM Prompt Enhancement

**Add to `prompt_template.py`:**

```python
IMPORTANT - Component ID Format Rules:
• Use EXACT FQDNs from the provided component list
• DO NOT add "deps." prefix (namespace already included)
• CORRECT: "openframe-oss-lib.src.main.java.Class"
• WRONG:   "deps.openframe-oss-lib.src.main.java.Class"

Format: <namespace>.<file_path>.<component_name>
- namespace: Repository basename (e.g., "openframe-oss-lib")
- file_path: Dot-separated path (e.g., "src.main.java.config")
- component: Class or function name

Examples:
✓ main-repo.src.services.user_service.UserService
✓ ui-kit.components.ui.button.Button
✓ openframe-api.src.main.java.com.openframe.api.AuthService
✗ deps.openframe-api.src.main.java.com.openframe.api.AuthService
```

## Files to Modify

### 1. `/codewiki/src/be/cluster_modules.py`

**Lines 89-120:** Replace `build_short_id_to_fqdn_map()`
```python
# Use: build_short_id_to_fqdn_map_enhanced() from FQDN_NORMALIZATION_FIX.py
```

**Lines 212-241:** Replace normalization loop
```python
# Use: normalize_component_ids_enhanced() from FQDN_NORMALIZATION_FIX.py
```

### 2. `/codewiki/src/be/prompt_template.py`

**Add to all clustering prompts:**
- `CLUSTER_REPO_PROMPT` (line ~30)
- `CLUSTER_MODULE_PROMPT` (line ~90)
- Any other prompts that reference component IDs

### 3. Test Files

**Create:** `test_fqdn_normalization.py`
- Unit tests for all 5 normalization strategies
- Test cases for edge cases (collisions, non-existent components)
- Regression tests for existing functionality

## Testing Plan

### Step 1: Verify Component Exists

```bash
# Run CodeWiki on actual repository
cd /Users/michaelassraf/Documents/GitHub/CodeWiki
python -m codewiki.src.be.workflow \
  --repo-path /path/to/openframe-oss-lib \
  --output /tmp/test-output

# Check if PinotConfigInitializer was parsed
grep -i "pinotconfig" /tmp/test-output/*.log

# Expected output:
# ✅ Registering component: openframe-oss-lib.src.main.java.config.pinot.PinotConfigInitializer
# or similar (shows actual FQDN format)
```

### Step 2: Test Normalization Fix

```bash
# Run unit tests
cd /Users/michaelassraf/Documents/GitHub/CodeWiki
python -m pytest test_fqdn_normalization.py -v

# Expected: All tests pass
# ✅ test_strip_deps_prefix PASSED
# ✅ test_fuzzy_component_name_match PASSED
# ✅ test_path_suffix_matching PASSED
# etc.
```

### Step 3: Integration Test

```bash
# Run full workflow with multi-path
cd /private/tmp/test-codewiki-fqdn
/tmp/test-codewiki-fqdn.sh

# Monitor normalization messages
grep "Failed to normalize" logs/*.log

# Expected: Zero failures for valid components
```

### Step 4: Verify LLM Prompt Works

```bash
# Re-run clustering with updated prompt
# Should see fewer "deps." prefixes in LLM output

# Check normalization statistics
grep "Normalized .* short IDs" logs/*.log
grep "Failed to normalize .* component IDs" logs/*.log

# Expected:
# ✅ Normalized 150 short IDs to FQDNs
# ⚠️  Failed to normalize 0 component IDs  (or very few)
```

## Success Criteria

### ✅ Fix is Successful When:

1. **Zero normalization failures for existing components**
   - Components that exist in the parsed data are successfully matched
   - "Failed to normalize" warnings only appear for LLM hallucinations

2. **Enhanced logging provides actionable debugging**
   - Shows which normalization strategy succeeded
   - Provides suggestions for ambiguous matches
   - Clearly identifies non-existent components

3. **All normalization strategies tested**
   - Unit tests pass for all 5 strategies
   - Integration tests show successful normalization
   - Edge cases (collisions, duplicates) handled gracefully

4. **LLM prompt reduces "deps." prefix usage**
   - After prompt update, fewer IDs have incorrect prefix
   - Remaining cases are handled by Strategy 3 (prefix stripping)

5. **Performance remains acceptable**
   - Normalization adds < 1 second to workflow
   - Fuzzy matching doesn't cause excessive iterations
   - Logging provides enough detail without overwhelming

## Next Steps

1. **Verify Component Exists** ⏳
   ```bash
   # Run CodeWiki on openframe-oss-lib
   # Confirm PinotConfigInitializer is parsed
   # Get actual FQDN format
   ```

2. **Implement Fix 1** ⏳
   ```bash
   # Copy enhanced functions from FQDN_NORMALIZATION_FIX.py
   # Replace normalization code in cluster_modules.py
   # Test with known failing case
   ```

3. **Run Unit Tests** ⏳
   ```bash
   pytest test_fqdn_normalization.py -v
   ```

4. **Update LLM Prompt** ⏳
   ```bash
   # Add format rules to prompt_template.py
   # Provide clear examples
   ```

5. **Integration Test** ⏳
   ```bash
   # Run full workflow
   # Verify normalization success rate improves
   ```

6. **Documentation** ⏳
   ```bash
   # Update README with normalization behavior
   # Document known edge cases
   # Add troubleshooting guide
   ```

## Questions to Answer

### Q1: Does PinotConfigInitializer exist in parsed components?

**How to check:**
```bash
# Run CodeWiki and grep for component
grep -i "pinotconfig" /path/to/output.log
```

**Possible outcomes:**
- ✅ Found → Normalization issue (fix will work)
- ❌ Not found → Parsing issue or LLM hallucination (won't fix)

### Q2: What is the actual FQDN format?

**Expected format:** `openframe-oss-lib.src.main.java.com.openframe.management.config.pinot.PinotConfigInitializer`

**Check:** Look at component registration logs

### Q3: Is "openframe-management-service-core" a directory?

**Check repository structure:**
```bash
ls -la /path/to/openframe-oss-lib/
# Look for nested directories
```

**Impact:**
- If it's a directory, might need to adjust normalization
- If not, confirms LLM is adding extra path segments

### Q4: Why is component name duplicated?

**Check:** `PintoConfigInitializer.PinotConfigInitializer`

**Possible causes:**
- Directory and file have same name
- Inner class with similar name
- Java naming convention (outer.inner class)

## Implementation Checklist

- [ ] Read `FQDN_MISMATCH_ANALYSIS.md` for detailed breakdown
- [ ] Copy `FQDN_NORMALIZATION_FIX.py` functions to `cluster_modules.py`
- [ ] Run `test_fqdn_normalization.py` to verify logic
- [ ] Update `prompt_template.py` with format rules
- [ ] Test on actual openframe-oss-lib repository
- [ ] Run integration tests (`/tmp/test-codewiki-fqdn.sh`)
- [ ] Verify normalization success rate improves
- [ ] Document new normalization strategies
- [ ] Update troubleshooting guide

## References

- **Analysis:** `FQDN_MISMATCH_ANALYSIS.md` - Detailed root cause analysis
- **Fix Code:** `FQDN_NORMALIZATION_FIX.py` - Complete implementation
- **Tests:** `test_fqdn_normalization.py` - Unit tests for all strategies
- **Expected Output:** `/tmp/test-codewiki-fqdn/EXPECTED_OUTPUT.md` - Valid FQDN examples
- **AST Parser:** `codewiki/src/be/dependency_analyzer/ast_parser.py:185-196` - Namespace construction
- **Current Normalization:** `codewiki/src/be/cluster_modules.py:200-241` - Code to replace
