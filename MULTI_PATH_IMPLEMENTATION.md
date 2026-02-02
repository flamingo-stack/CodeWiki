# Multi-Path Support Implementation

## Overview

This document describes the implementation of multi-path support in `DependencyParser` and `RepoAnalyzer`, allowing the analysis of multiple source directories with proper component namespacing and cross-repository dependency resolution.

## Architecture

### Component Namespacing

When parsing multiple repositories, each component is namespaced to prevent ID collisions:

```
Format: {namespace}.{original_component_id}

Example:
  Single path:  "src.components.Button.render"
  Multi-path:   "openframe-frontend.src.components.Button.render"
```

The namespace is derived from the repository directory name (e.g., `openframe-frontend`, `ui-kit`).

### Dependency Resolution

Dependencies are resolved in three stages:

1. **Intra-namespace**: Dependencies within the same repository use namespaced IDs
2. **Cross-namespace**: Dependencies between repositories are resolved by component name matching
3. **Fallback**: Unresolved dependencies retain their original ID for debugging

## DependencyParser Changes

### Constructor (`__init__`)

**Before:**
```python
def __init__(self, repo_path: str, include_patterns: List[str] = None, exclude_patterns: List[str] = None):
    self.repo_path = os.path.abspath(repo_path)
```

**After:**
```python
def __init__(self, repo_path: Union[str, List[str]], include_patterns: List[str] = None, exclude_patterns: List[str] = None):
    if isinstance(repo_path, str):
        self.repo_paths = [os.path.abspath(repo_path)]
        self.repo_path = self.repo_paths[0]  # Backward compatibility
    else:
        self.repo_paths = [os.path.abspath(p) for p in repo_path]
        self.repo_path = self.repo_paths[0]
```

**Backward Compatibility:**
- Single string path: Works exactly as before
- List of paths: New multi-path functionality
- `self.repo_path` maintained for legacy code

### New Methods

#### `_parse_single_repository(repo_path, filtered_folders)`
- Extracts original `parse_repository` logic
- Maintains backward compatibility
- No changes to component IDs

#### `_parse_multiple_repositories(filtered_folders)`
- Orchestrates parsing of multiple repositories
- Creates namespace for each repository
- Merges components with namespaced IDs
- Resolves cross-namespace dependencies

#### `_get_namespace_from_path(repo_path)`
- Generates namespace from directory name
- Example: `/path/to/ui-kit` → `"ui-kit"`

#### `_build_namespaced_components(call_graph_result, namespace, namespace_mapping)`
- Builds components with namespace prefix
- Maintains mapping of original → namespaced IDs
- Tracks modules with namespaced paths

#### `_resolve_cross_namespace_dependencies(all_components, namespace_mapping)`
- Resolves dependencies across repository boundaries
- Uses name matching for cross-namespace resolution
- Preserves unresolved dependencies for debugging

### Updated Method

#### `parse_repository(filtered_folders)`
- Now dispatches to single or multi-path parsing
- Returns unified component dictionary

## RepoAnalyzer Changes

### Constructor (`__init__`)

**Added:**
```python
self._namespace_roots: Dict[str, str] = {}  # namespace -> repo_path
```

Tracks which namespace corresponds to which repository path.

### Updated Methods

#### `analyze_repository_structure(repo_dir)`

**Before:**
```python
def analyze_repository_structure(self, repo_dir: str) -> Dict:
    file_tree = self._build_file_tree(repo_dir)
    return {
        "file_tree": file_tree,
        "summary": {...}
    }
```

**After:**
```python
def analyze_repository_structure(self, repo_dir: Union[str, List[str]]) -> Dict:
    if isinstance(repo_dir, str):
        # Single path - backward compatible
        return self._analyze_single_repository(repo_dir)
    else:
        # Multiple paths
        return self._analyze_multiple_repositories(repo_dir)
```

### New Methods

#### `_analyze_multiple_repositories(repo_dirs)`
- Analyzes each repository separately
- Wraps each tree with namespace prefix
- Merges trees into single structure
- Combines summary statistics

#### `_get_namespace_from_path(repo_path)`
- Same as DependencyParser implementation
- Ensures consistent namespacing

## Usage Examples

### Single Path (Backward Compatible)

```python
from codewiki.src.be.dependency_analyzer.ast_parser import DependencyParser

# Old code continues to work
parser = DependencyParser("/path/to/repo")
components = parser.parse_repository()

# Component IDs unchanged
# "src.utils.helpers.formatDate"
```

### Multiple Paths

```python
from codewiki.src.be.dependency_analyzer.ast_parser import DependencyParser

# New multi-path support
paths = [
    "/path/to/openframe-frontend",
    "/path/to/ui-kit",
    "/path/to/shared-lib"
]

parser = DependencyParser(paths, include_patterns=["*.py", "*.ts"])
components = parser.parse_repository()

# Component IDs are namespaced
# "openframe-frontend.src.utils.helpers.formatDate"
# "ui-kit.components.Button.render"
# "shared-lib.utils.api.fetchData"
```

### With RepoAnalyzer

```python
from codewiki.src.be.dependency_analyzer.analysis.repo_analyzer import RepoAnalyzer

analyzer = RepoAnalyzer(
    include_patterns=["*.py", "*.ts"],
    exclude_patterns=["*test*", "*spec*"]
)

# Single path
result = analyzer.analyze_repository_structure("/path/to/repo")

# Multiple paths
result = analyzer.analyze_repository_structure([
    "/path/to/repo1",
    "/path/to/repo2"
])

# File tree structure
{
    "file_tree": {
        "type": "directory",
        "name": "multi-repo",
        "children": [
            {
                "type": "directory",
                "name": "repo1",
                "_namespace": "repo1",
                "children": [...]
            },
            {
                "type": "directory",
                "name": "repo2",
                "_namespace": "repo2",
                "children": [...]
            }
        ]
    },
    "summary": {
        "total_files": 150,
        "total_size_kb": 2048.5,
        "repositories": 2,
        "namespaces": ["repo1", "repo2"]
    }
}
```

## Component ID Format

### Single Path Mode
```
{module_path}.{component_name}

Examples:
- src.components.Button.render
- lib.utils.helpers.formatDate
- services.api.UserService.getUser
```

### Multi-Path Mode
```
{namespace}.{module_path}.{component_name}

Examples:
- openframe-frontend.src.components.Button.render
- ui-kit.lib.utils.helpers.formatDate
- shared-lib.services.api.UserService.getUser
```

## Cross-Namespace Dependencies

When a component in one namespace depends on a component in another:

```python
# Component in openframe-frontend
{
    "id": "openframe-frontend.src.App.main",
    "depends_on": [
        "openframe-frontend.src.utils.logger",  # Same namespace
        "ui-kit.components.Button"              # Cross-namespace
    ]
}
```

Resolution process:
1. Check if dependency ID exists in `all_components`
2. If not found, extract component name and search by name across namespaces
3. If still not found, keep original ID for debugging

## Data Structures

### DependencyParser

```python
class DependencyParser:
    repo_paths: List[str]           # All repository paths
    repo_path: str                   # First path (backward compat)
    components: Dict[str, Node]      # All components (namespaced in multi-path)
    modules: Set[str]                # All module paths (namespaced in multi-path)
    include_patterns: List[str]      # File include patterns
    exclude_patterns: List[str]      # File exclude patterns
    analysis_service: AnalysisService
```

### RepoAnalyzer

```python
class RepoAnalyzer:
    include_patterns: List[str]
    exclude_patterns: List[str]
    _namespace_roots: Dict[str, str]  # Maps namespace to repo_path
```

## Edge Cases Handled

1. **Empty repositories**: Skipped in multi-path mode
2. **Duplicate namespaces**: Last one wins (deterministic)
3. **Circular dependencies**: Preserved as-is, no cycle detection
4. **Missing dependencies**: Kept with original ID for debugging
5. **Relative paths**: Maintained relative to original repository

## Performance Characteristics

- **Time Complexity**: O(n * m) where n = number of repos, m = avg components per repo
- **Space Complexity**: O(n * m) for component storage
- **Namespace Mapping**: O(k) where k = total unique component IDs

## Testing

### Test Single Path Compatibility
```python
parser = DependencyParser("/path/to/repo")
assert len(parser.repo_paths) == 1
assert parser.repo_path == parser.repo_paths[0]
```

### Test Multiple Paths
```python
paths = ["/repo1", "/repo2"]
parser = DependencyParser(paths)
assert len(parser.repo_paths) == 2
components = parser.parse_repository()
# Check namespaced IDs
assert any("repo1." in comp_id for comp_id in components.keys())
assert any("repo2." in comp_id for comp_id in components.keys())
```

### Test Namespace Generation
```python
parser = DependencyParser(["/path/to/openframe-frontend"])
namespace = parser._get_namespace_from_path("/path/to/openframe-frontend")
assert namespace == "openframe-frontend"
```

## Migration Guide

### Existing Code
```python
# No changes needed - works as before
parser = DependencyParser(repo_path)
components = parser.parse_repository()
```

### New Multi-Path Code
```python
# Update to use list of paths
parser = DependencyParser([repo_path1, repo_path2])
components = parser.parse_repository()

# Component IDs now include namespace prefix
for comp_id, component in components.items():
    print(f"Component: {comp_id}")  # e.g., "ui-kit.components.Button"
```

## Implementation Files

- `/Users/michaelassraf/Documents/GitHub/CodeWiki/codewiki/src/be/dependency_analyzer/ast_parser.py` (355 lines)
- `/Users/michaelassraf/Documents/GitHub/CodeWiki/codewiki/src/be/dependency_analyzer/analysis/repo_analyzer.py` (178 lines)

## Key Decisions

1. **Namespace from directory name**: Simple, predictable, human-readable
2. **Backward compatibility preserved**: Single string path works unchanged
3. **Cross-namespace resolution by name**: Flexible but may match wrong component in ambiguous cases
4. **No breaking changes**: All existing code continues to work

## Future Enhancements

1. Custom namespace mapping (instead of directory name)
2. More sophisticated cross-namespace dependency resolution
3. Namespace aliases for shorter IDs
4. Component visibility controls (public/private across namespaces)
5. Performance optimization for very large multi-repo setups
