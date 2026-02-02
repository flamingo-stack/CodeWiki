# Multi-Path Support - Quick Reference

## Basic Usage

### Single Path (Backward Compatible)
```python
from codewiki.src.be.dependency_analyzer.ast_parser import DependencyParser

parser = DependencyParser("/path/to/repo")
components = parser.parse_repository()
# Component IDs: "src.module.Component"
```

### Multiple Paths
```python
parser = DependencyParser([
    "/path/to/openframe-frontend",
    "/path/to/ui-kit"
])
components = parser.parse_repository()
# Component IDs: "openframe-frontend.src.module.Component"
#                "ui-kit.components.Button"
```

## Component ID Format

| Mode | Format | Example |
|------|--------|---------|
| Single | `{module}.{component}` | `src.components.Button` |
| Multi | `{namespace}.{module}.{component}` | `ui-kit.src.components.Button` |

## Key Methods

### DependencyParser

```python
parser = DependencyParser(
    repo_path: Union[str, List[str]],  # Single or multiple paths
    include_patterns: List[str] = None,  # ["*.py", "*.ts"]
    exclude_patterns: List[str] = None   # ["*test*"]
)

# Parse repositories
components: Dict[str, Node] = parser.parse_repository()

# Save to JSON
parser.save_dependency_graph("/path/to/output.json")

# Access namespace info (multi-path only)
namespace = parser._get_namespace_from_path("/path/to/repo")
```

### RepoAnalyzer

```python
analyzer = RepoAnalyzer(
    include_patterns: List[str] = None,
    exclude_patterns: List[str] = None
)

# Single path
result = analyzer.analyze_repository_structure("/path/to/repo")

# Multiple paths
result = analyzer.analyze_repository_structure([
    "/path/to/repo1",
    "/path/to/repo2"
])

# Result structure:
{
    "file_tree": {...},
    "summary": {
        "total_files": int,
        "total_size_kb": float,
        "repositories": int,        # Multi-path only
        "namespaces": List[str]     # Multi-path only
    }
}
```

## Component Object (Node)

```python
component = components["namespace.module.Component"]

# Core attributes
component.id                  # Namespaced ID
component.name                # Original component name
component.component_type      # "function", "class", "method"
component.file_path          # Absolute path
component.relative_path      # Relative to repo
component.depends_on         # Set of dependency IDs (namespaced)

# Code details
component.source_code        # Full source code
component.start_line         # Starting line number
component.end_line           # Ending line number
component.docstring          # Component docstring
component.parameters         # List of parameters

# Additional info
component.node_type          # AST node type
component.class_name         # Parent class (if method)
component.base_classes       # Inheritance (if class)
```

## Dependencies

### Intra-Namespace (Same Repository)
```python
{
    "id": "openframe-frontend.src.App.main",
    "depends_on": [
        "openframe-frontend.src.utils.logger",
        "openframe-frontend.src.config.settings"
    ]
}
```

### Cross-Namespace (Different Repositories)
```python
{
    "id": "openframe-frontend.src.App.main",
    "depends_on": [
        "openframe-frontend.src.utils.logger",  # Same namespace
        "ui-kit.components.Button",             # Cross-namespace
        "shared-lib.api.fetchData"              # Cross-namespace
    ]
}
```

## Common Patterns

### Filtering Components by Namespace
```python
parser = DependencyParser(["/repo1", "/repo2"])
components = parser.parse_repository()

# Get components from specific namespace
repo1_components = {
    comp_id: comp for comp_id, comp in components.items()
    if comp_id.startswith("repo1.")
}
```

### Finding Cross-Namespace Dependencies
```python
for comp_id, component in components.items():
    comp_namespace = comp_id.split('.')[0]
    cross_deps = [
        dep for dep in component.depends_on
        if dep.split('.')[0] != comp_namespace
    ]
    if cross_deps:
        print(f"{comp_id} has {len(cross_deps)} cross-namespace deps")
```

### Grouping by Namespace
```python
from collections import defaultdict

by_namespace = defaultdict(list)
for comp_id in components.keys():
    namespace = comp_id.split('.')[0]
    by_namespace[namespace].append(comp_id)

for namespace, comp_ids in by_namespace.items():
    print(f"{namespace}: {len(comp_ids)} components")
```

## File Patterns

### Include Patterns
```python
# Python only
include_patterns = ["*.py"]

# TypeScript/JavaScript
include_patterns = ["*.ts", "*.tsx", "*.js", "*.jsx"]

# Multiple languages
include_patterns = ["*.py", "*.ts", "*.tsx", "*.cs", "*.java"]
```

### Exclude Patterns
```python
exclude_patterns = [
    "*test*",           # Test files
    "*spec*",           # Spec files
    "node_modules/*",   # Dependencies
    "build/*",          # Build output
    "dist/*",           # Distribution files
    ".git/*",           # Git directory
    "__pycache__/*"     # Python cache
]
```

## Error Handling

```python
try:
    parser = DependencyParser(["/repo1", "/repo2"])
    components = parser.parse_repository()
except FileNotFoundError as e:
    print(f"Repository not found: {e}")
except PermissionError as e:
    print(f"Permission denied: {e}")
except Exception as e:
    print(f"Parsing error: {e}")
```

## Performance Tips

1. **Use Specific Include Patterns**: Only analyze relevant file types
2. **Aggressive Exclude Patterns**: Skip test files, dependencies, build outputs
3. **Limit Number of Paths**: More paths = longer analysis time
4. **Filter Early**: Use `filtered_folders` parameter when possible

## Output Format (JSON)

```json
{
  "namespace.module.Component": {
    "id": "namespace.module.Component",
    "name": "Component",
    "component_type": "class",
    "file_path": "/absolute/path/to/file.py",
    "relative_path": "src/module/file.py",
    "source_code": "class Component:\n    ...",
    "start_line": 10,
    "end_line": 50,
    "depends_on": [
      "namespace.module.Dependency1",
      "other-namespace.utils.Helper"
    ],
    "docstring": "Component docstring",
    "parameters": [],
    "node_type": "class",
    "has_docstring": true
  }
}
```

## Backward Compatibility

All existing single-path code works without changes:

```python
# ✅ Still works
parser = DependencyParser("/path/to/repo")
parser.repo_path  # Still available
components = parser.parse_repository()  # Same behavior
```

## Migration Checklist

- [ ] Update `DependencyParser` constructor calls to use list of paths
- [ ] Update code that assumes non-namespaced component IDs
- [ ] Update dependency resolution logic for cross-namespace refs
- [ ] Update JSON output parsing if used downstream
- [ ] Test with actual multi-path repositories
- [ ] Update documentation/examples

## Common Issues

### Issue: "Component not found"
**Cause**: Cross-namespace dependency resolution failed
**Solution**: Check component names match exactly, verify both repos were parsed

### Issue: "Duplicate component IDs"
**Cause**: Two repos with same directory name
**Solution**: Rename one repository directory or use unique paths

### Issue: "Performance degradation"
**Cause**: Too many files being analyzed
**Solution**: Add more exclude patterns, use specific include patterns

### Issue: "Missing dependencies"
**Cause**: Component exists but not in dependency graph
**Solution**: Check include/exclude patterns, verify file was parsed

## Examples Location

See `/examples/multi_path_example.py` for complete working examples.

## Documentation

- Full Implementation: `MULTI_PATH_IMPLEMENTATION.md`
- API Reference: Component docstrings in source files
- Examples: `examples/multi_path_example.py`
