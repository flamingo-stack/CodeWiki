# Multi-Path Implementation - Example Log Outputs

## Example 1: OpenFrame Frontend + UI-Kit (2 Paths)

### Command
```bash
codewiki generate \
  --repo-path=/Users/michaelassraf/Documents/GitHub/openframe-oss-tenant/openframe/services/openframe-frontend/multi-platform-hub \
  --output-dir=output \
  --additional-paths=ui-kit \
  --verbose
```

### Expected Log Output

```
🔍 CLI received 1 additional path(s):
   ├─ Path #1: ui-kit
   │  └─ Normalized: /Users/michaelassraf/Documents/GitHub/openframe-oss-tenant/openframe/services/openframe-frontend/multi-platform-hub/ui-kit
   └─ Normalized 1 additional path(s)

📋 Generation Configuration:
   ├─ Cluster Model: claude-sonnet-4
   ├─ Main Model: claude-sonnet-4
   ├─ Fallback Model: gpt-4o-mini
   ├─ Module Settings:
   │  ├─ Max tokens/module: 36369
   │  ├─ Max tokens/leaf: 16000
   │  └─ Max depth: 2
   ├─ Additional Paths (1):
   │  └─ /Users/michaelassraf/Documents/GitHub/openframe-oss-tenant/openframe/services/openframe-frontend/multi-platform-hub/ui-kit
   └─ Agent Instructions: Configured

🔍 Validating source paths...
   ├─ ✓ Primary path valid: /Users/.../multi-platform-hub
   ├─ Validating 1 additional path(s)...
   │  ├─ ✓ Additional path #1 valid: /Users/.../ui-kit
   └─ ✓ All 1 additional path(s) validated

===== Stage 1/5: Dependency Analysis =====

🔍 Multi-path mode enabled: analyzing 2 source paths
   ├─ Primary: /Users/.../multi-platform-hub
   └─ Additional #1: /Users/.../ui-kit

🔍 Analyzing 2 repository paths...
   ├─ [1/2] Building file tree for: /Users/.../multi-platform-hub
   │  └─ Namespace: 'multi-platform-hub'
   │  └─ Found 487 files (8542.35 KB)
   ├─ [2/2] Building file tree for: /Users/.../ui-kit
   │  └─ Namespace: 'ui-kit'
   │  └─ Found 328 files (5123.89 KB)
   └─ ✓ Merged 2 repositories:
      ├─ Total files: 815
      ├─ Total size: 13666.24 KB
      └─ Namespaces: multi-platform-hub, ui-kit

🔍 Parsing repository files...

🔍 Multi-path mode detected: analyzing 2 source directories
   ├─ Primary: /Users/.../multi-platform-hub
   └─ Additional #1: /Users/.../ui-kit

📂 Analyzing path 1/2: /Users/.../multi-platform-hub
   └─ Namespace: 'multi-platform-hub'
📊 Namespace 'multi-platform-hub': found 1243 components
   └─ Component types:
      • function: 789
      • class: 234
      • interface: 156
      • method: 64

📂 Analyzing path 2/2: /Users/.../ui-kit
   └─ Namespace: 'ui-kit'
📊 Namespace 'ui-kit': found 856 components
   └─ Component types:
      • function: 512
      • class: 198
      • interface: 123
      • method: 23

🔗 Resolving cross-namespace dependencies...
   ├─ Cross-namespace dependency: multi-platform-hub.app.components.Button → ui-kit.components.ui.Button
   ├─ Cross-namespace dependency: multi-platform-hub.app.hooks.useToast → ui-kit.hooks.useToast
   ├─ Cross-namespace dependency: multi-platform-hub.lib.utils.cn → ui-kit.utils.cn
   ... (12 more)
   └─ ✓ Resolved 15 cross-namespace dependencies

📊 Multi-path analysis complete:
   ├─ Total components: 2099
   ├─ Total modules: 45
   └─ Namespaces: 2

   └─ Parsed 2099 components total
   └─ Component types found:
      • function: 1301
      • class: 432
      • interface: 279
      • method: 87

   └─ Saved dependency graph to: output/temp/dependency_graphs/multi-platform-hub_dependency_graph.json

🌿 Filtering leaf nodes (total: 2099)...
   └─ Valid types for this codebase: class, interface

📊 Leaf node filtering complete:
   ├─ Kept: 711 nodes
   ├─ Skipped (invalid identifier): 0
   ├─ Skipped (wrong type): 1301
   └─ Skipped (not found): 87

   ├─ Total components: 2099
   ├─ Leaf nodes: 711
   └─ Files analyzed: 815

✓ Stage 1/5 complete (45.2s)

===== Stage 2/5: Module Clustering =====

   ├─ Leaf nodes to cluster: 711
   ├─ Using model: claude-sonnet-4
   └─ Calling LLM for clustering...

   ├─ Total modules: 18
   └─ Module names: auth, dashboard, devices, logs, admin ... (13 more)

✓ Stage 2/5 complete (23.7s)
```

---

## Example 2: Single Path (Backward Compatibility)

### Command
```bash
codewiki generate \
  --repo-path=/Users/michaelassraf/Documents/GitHub/CodeWiki \
  --output-dir=output \
  --verbose
```

### Expected Log Output

```
📋 Generation Configuration:
   ├─ Cluster Model: claude-sonnet-4
   ├─ Main Model: claude-sonnet-4
   ├─ Fallback Model: gpt-4o-mini
   ├─ Module Settings:
   │  ├─ Max tokens/module: 36369
   │  ├─ Max tokens/leaf: 16000
   │  └─ Max depth: 2

🔍 Validating source paths...
   ├─ ✓ Primary path valid: /Users/.../CodeWiki
   └─ No additional paths to validate (single-path mode)

===== Stage 1/5: Dependency Analysis =====

📁 Single-path mode: analyzing /Users/.../CodeWiki

   ├─ Repository: /Users/.../CodeWiki
   └─ Output: output/temp

🔍 Parsing repository files...
   └─ Parsed 234 components total
   └─ Component types found:
      • function: 145
      • class: 67
      • method: 22

   └─ Saved dependency graph to: output/temp/dependency_graphs/CodeWiki_dependency_graph.json

🌿 Filtering leaf nodes (total: 234)...
   └─ Valid types for this codebase: class, function

📊 Leaf node filtering complete:
   ├─ Kept: 212 nodes
   ├─ Skipped (invalid identifier): 0
   ├─ Skipped (wrong type): 22
   └─ Skipped (not found): 0

   ├─ Total components: 234
   ├─ Leaf nodes: 212
   └─ Files analyzed: 156

✓ Stage 1/5 complete (12.3s)
```

---

## Example 3: Three Paths (Complex Multi-Repo)

### Command
```bash
codewiki generate \
  --repo-path=/app/backend \
  --output-dir=output \
  --additional-paths=../shared-lib,../ui-components \
  --verbose
```

### Expected Log Output

```
🔍 CLI received 2 additional path(s):
   ├─ Path #1: ../shared-lib
   │  └─ Normalized: /app/shared-lib
   ├─ Path #2: ../ui-components
   │  └─ Normalized: /app/ui-components
   └─ Normalized 2 additional path(s)

🔍 Validating source paths...
   ├─ ✓ Primary path valid: /app/backend
   ├─ Validating 2 additional path(s)...
   │  ├─ ✓ Additional path #1 valid: /app/shared-lib
   │  ├─ ✓ Additional path #2 valid: /app/ui-components
   └─ ✓ All 2 additional path(s) validated

🔍 Multi-path mode enabled: analyzing 3 source paths
   ├─ Primary: /app/backend
   ├─ Additional #1: /app/shared-lib
   └─ Additional #2: /app/ui-components

🔍 Analyzing 3 repository paths...
   ├─ [1/3] Building file tree for: /app/backend
   │  └─ Namespace: 'backend'
   │  └─ Found 312 files (5623.12 KB)
   ├─ [2/3] Building file tree for: /app/shared-lib
   │  └─ Namespace: 'shared-lib'
   │  └─ Found 89 files (1234.56 KB)
   ├─ [3/3] Building file tree for: /app/ui-components
   │  └─ Namespace: 'ui-components'
   │  └─ Found 156 files (2345.67 KB)
   └─ ✓ Merged 3 repositories:
      ├─ Total files: 557
      ├─ Total size: 9203.35 KB
      └─ Namespaces: backend, shared-lib, ui-components

🔍 Multi-path mode detected: analyzing 3 source directories
   ├─ Primary: /app/backend
   ├─ Additional #1: /app/shared-lib
   └─ Additional #2: /app/ui-components

📂 Analyzing path 1/3: /app/backend
   └─ Namespace: 'backend'
📊 Namespace 'backend': found 456 components
   └─ Component types:
      • class: 234
      • function: 145
      • interface: 67
      • method: 10

📂 Analyzing path 2/3: /app/shared-lib
   └─ Namespace: 'shared-lib'
📊 Namespace 'shared-lib': found 123 components
   └─ Component types:
      • function: 78
      • class: 34
      • interface: 11

📂 Analyzing path 3/3: /app/ui-components
   └─ Namespace: 'ui-components'
📊 Namespace 'ui-components': found 234 components
   └─ Component types:
      • function: 156
      • class: 67
      • interface: 11

🔗 Resolving cross-namespace dependencies...
   ├─ Cross-namespace dependency: backend.api.UserController → shared-lib.models.User
   ├─ Cross-namespace dependency: backend.api.AuthController → shared-lib.utils.jwt
   ├─ Cross-namespace dependency: ui-components.Button → shared-lib.themes.colors
   ├─ Cross-namespace dependency: ui-components.Modal → shared-lib.utils.portal
   ... (18 more)
   └─ ✓ Resolved 22 cross-namespace dependencies

📊 Multi-path analysis complete:
   ├─ Total components: 813
   ├─ Total modules: 28
   └─ Namespaces: 3
```

---

## Example 4: Error Case - Invalid Path

### Command
```bash
codewiki generate \
  --repo-path=/app/backend \
  --output-dir=output \
  --additional-paths=../nonexistent \
  --verbose
```

### Expected Log Output

```
🔍 CLI received 1 additional path(s):
   ├─ Path #1: ../nonexistent
   │  └─ Normalized: /app/nonexistent
   └─ Normalized 1 additional path(s)

🔍 Validating source paths...
   ├─ ✓ Primary path valid: /app/backend
   ├─ Validating 1 additional path(s)...
   │  └─ Checking additional path #1: /app/nonexistent

ERROR: Additional source path #1 does not exist: /app/nonexistent

Validation failed. Please check your path configuration.
```

---

## Example 5: Warning - No Files Found

### Command
```bash
codewiki generate \
  --repo-path=/app/backend \
  --output-dir=output \
  --additional-paths=../empty-dir \
  --include-patterns="*.py" \
  --verbose
```

### Expected Log Output

```
🔍 Analyzing 2 repository paths...
   ├─ [1/2] Building file tree for: /app/backend
   │  └─ Namespace: 'backend'
   │  └─ Found 312 files (5623.12 KB)
   ├─ [2/2] Building file tree for: /app/empty-dir
   │  └─ Namespace: 'empty-dir'
   │  └─ ⚠️  No files found matching patterns
   └─ ✓ Merged 2 repositories:
      ├─ Total files: 312
      ├─ Total size: 5623.12 KB
      └─ Namespaces: backend, empty-dir

⚠️  WARNING: Namespace 'empty-dir' has no components
```

---

## Debugging Tips

### Enable Verbose Logging
```bash
# Show all DEBUG level logs
codewiki generate --repo-path=. --output-dir=output --verbose

# Show all logs including component details
export CODEWIKI_LOG_LEVEL=DEBUG
codewiki generate --repo-path=. --output-dir=output
```

### Filter Logs by Layer
```bash
# Show only multi-path related logs
codewiki generate ... 2>&1 | grep "🔍\|📂\|📊\|🔗"

# Show only errors and warnings
codewiki generate ... 2>&1 | grep "ERROR\|WARNING\|⚠️"

# Show only namespace information
codewiki generate ... 2>&1 | grep "Namespace"
```

### Capture Logs to File
```bash
# Full log capture
codewiki generate --repo-path=. --output-dir=output --verbose 2>&1 | tee codewiki.log

# Time-stamped logs
codewiki generate ... 2>&1 | ts '[%Y-%m-%d %H:%M:%S]' | tee codewiki.log
```

---

## Key Log Patterns to Look For

### Success Pattern
```
✓ Primary path valid
✓ All X additional path(s) validated
✓ Merged X repositories
✓ Resolved X cross-namespace dependencies
📊 Multi-path analysis complete
```

### Progress Pattern
```
[1/3] Building file tree
[2/3] Building file tree
[3/3] Building file tree
📂 Analyzing path 1/3
📂 Analyzing path 2/3
📂 Analyzing path 3/3
```

### Error Pattern
```
ERROR: Additional source path #X does not exist
ERROR: Additional source path #X is not a directory
ERROR: Additional source path #X is not readable
```

### Warning Pattern
```
⚠️  No files found matching patterns
⚠️  Namespace 'X' has no components
⚠️  Leaf node 'X' not found in components
```

---

## Performance Monitoring

### Time Tracking
Each log line includes implicit timing through stage progress:
```
===== Stage 1/5: Dependency Analysis =====
... (operations)
✓ Stage 1/5 complete (45.2s)

===== Stage 2/5: Module Clustering =====
... (operations)
✓ Stage 2/5 complete (23.7s)
```

### Component Counting
Track component growth across namespaces:
```
📊 Namespace 'primary': found 1243 components
📊 Namespace 'ui-kit': found 856 components
📊 Multi-path analysis complete:
   ├─ Total components: 2099  ← Sum of all namespaces
```

### Memory Usage
Monitor file counts and sizes:
```
   │  └─ Found 487 files (8542.35 KB)  ← Per namespace
   └─ ✓ Merged 2 repositories:
      ├─ Total files: 815              ← Combined
      ├─ Total size: 13666.24 KB       ← Combined
```
