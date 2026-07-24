# Multi-Path Architecture Diagram

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    DependencyParser                              │
│                                                                  │
│  Constructor:                                                    │
│    repo_path: Union[str, List[str]]                             │
│                                                                  │
│  ┌──────────────────────────────────────────────────────┐      │
│  │ Single Path Mode (Backward Compatible)                │      │
│  │                                                        │      │
│  │  Input: "/path/to/repo"                               │      │
│  │     ↓                                                  │      │
│  │  _parse_single_repository()                           │      │
│  │     ↓                                                  │      │
│  │  Component IDs: "src.module.Component"                │      │
│  └──────────────────────────────────────────────────────┘      │
│                                                                  │
│  ┌──────────────────────────────────────────────────────┐      │
│  │ Multi-Path Mode (New)                                 │      │
│  │                                                        │      │
│  │  Input: ["/repo1", "/repo2", "/repo3"]                │      │
│  │     ↓                                                  │      │
│  │  _parse_multiple_repositories()                       │      │
│  │     ↓                                                  │      │
│  │  For each repo:                                       │      │
│  │    1. Generate namespace from directory name          │      │
│  │    2. Analyze structure (_analyze_structure)          │      │
│  │    3. Analyze call graph (_analyze_call_graph)        │      │
│  │    4. Build namespaced components                     │      │
│  │       (_build_namespaced_components)                  │      │
│  │     ↓                                                  │      │
│  │  Merge all components                                 │      │
│  │     ↓                                                  │      │
│  │  Resolve cross-namespace dependencies                 │      │
│  │     ↓                                                  │      │
│  │  Component IDs: "repo1.src.module.Component"          │      │
│  │                 "repo2.lib.utils.Helper"              │      │
│  └──────────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────┘
```

## Component Namespacing Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                   Component ID Generation                        │
└─────────────────────────────────────────────────────────────────┘

Single Path Mode:
┌──────────────────┐     ┌──────────────────┐     ┌──────────────┐
│  File Path       │ ──> │  Module Path     │ ──> │ Component ID │
│  src/utils.py    │     │  src.utils       │     │ src.utils.fn │
└──────────────────┘     └──────────────────┘     └──────────────┘

Multi-Path Mode:
┌──────────────────┐     ┌──────────────────┐     ┌──────────────┐
│  Repo Path       │     │  Namespace       │     │              │
│  /path/ui-kit    │ ──> │  ui-kit          │ ──> │              │
└──────────────────┘     └──────────────────┘     │              │
                                                   │              │
┌──────────────────┐     ┌──────────────────┐     │              │
│  File Path       │ ──> │  Module Path     │ ──> │ Component ID │
│  src/utils.py    │     │  src.utils       │     │ ui-kit.      │
└──────────────────┘     └──────────────────┘     │ src.utils.fn │
                                                   └──────────────┘
```

## Dependency Resolution Process

```
┌─────────────────────────────────────────────────────────────────┐
│                  Dependency Resolution Strategy                  │
└─────────────────────────────────────────────────────────────────┘

Step 1: Parse Component A (namespace: "frontend")
┌───────────────────────────────────────┐
│ Component: frontend.src.App.main      │
│ Dependencies found in AST:            │
│   - utils.logger                      │
│   - Button                            │
│   - api.fetchData                     │
└───────────────────────────────────────┘
                ↓
Step 2: Intra-Namespace Resolution
┌───────────────────────────────────────┐
│ Check if exists in same namespace:    │
│   ✓ utils.logger → frontend.utils.   │
│                     logger            │
│   ✗ Button → not found               │
│   ✗ api.fetchData → not found        │
└───────────────────────────────────────┘
                ↓
Step 3: Cross-Namespace Resolution
┌───────────────────────────────────────┐
│ Search by name in all namespaces:    │
│   ✓ Button → ui-kit.components.      │
│               Button                  │
│   ✓ fetchData → shared-lib.api.      │
│                 fetchData             │
└───────────────────────────────────────┘
                ↓
Step 4: Final Dependencies
┌───────────────────────────────────────┐
│ Component: frontend.src.App.main      │
│ Dependencies:                         │
│   - frontend.utils.logger             │
│   - ui-kit.components.Button          │
│   - shared-lib.api.fetchData          │
└───────────────────────────────────────┘
```

## RepoAnalyzer Multi-Path Structure

```
┌─────────────────────────────────────────────────────────────────┐
│                    RepoAnalyzer Multi-Path                       │
└─────────────────────────────────────────────────────────────────┘

Input: ["/path/to/repo1", "/path/to/repo2"]

Step 1: Analyze Each Repository
┌─────────────────────────────────────┐
│ Repo 1: /path/to/repo1              │
│   ├─ src/                           │
│   │  ├─ module.py                   │
│   │  └─ utils.py                    │
│   └─ tests/                         │
└─────────────────────────────────────┘
                ↓
        Namespace: "repo1"

┌─────────────────────────────────────┐
│ Repo 2: /path/to/repo2              │
│   ├─ lib/                           │
│   │  └─ helpers.py                  │
│   └─ config/                        │
└─────────────────────────────────────┘
                ↓
        Namespace: "repo2"

Step 2: Merge File Trees
┌─────────────────────────────────────┐
│ Root: multi-repo                    │
│   ├─ repo1/                         │
│   │  ├─ src/                        │
│   │  │  ├─ module.py                │
│   │  │  └─ utils.py                 │
│   │  └─ tests/                      │
│   │                                 │
│   └─ repo2/                         │
│      ├─ lib/                        │
│      │  └─ helpers.py               │
│      └─ config/                     │
└─────────────────────────────────────┘

Step 3: Combined Summary
┌─────────────────────────────────────┐
│ Summary:                            │
│   - total_files: 5                  │
│   - total_size_kb: 123.4            │
│   - repositories: 2                 │
│   - namespaces: ["repo1", "repo2"]  │
└─────────────────────────────────────┘
```

## Data Flow Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                        Multi-Path Data Flow                       │
└──────────────────────────────────────────────────────────────────┘

                          Input Repositories
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        │                         │                         │
        ▼                         ▼                         ▼
   /repo/frontend          /repo/ui-kit            /repo/shared
        │                         │                         │
        └─────────────────────────┴─────────────────────────┘
                                  │
                                  ▼
                        DependencyParser.__init__
                                  │
                    repo_paths: [str, str, str]
                                  │
                                  ▼
                        parse_repository()
                                  │
                 ┌────────────────┴────────────────┐
                 │                                 │
                 ▼                                 ▼
    _parse_single_repository()      _parse_multiple_repositories()
         (1 path only)                     (multiple paths)
                                                  │
                      ┌───────────────────────────┴───────────┐
                      │                                       │
                      ▼                                       ▼
              For each repository:                  Merge all results:
                                                              │
        1. _get_namespace_from_path()                        │
        2. _analyze_structure()                              │
        3. _analyze_call_graph()                             │
        4. _build_namespaced_components()                    │
                      │                                       │
                      └───────────────────────────────────────┘
                                      │
                                      ▼
                  _resolve_cross_namespace_dependencies()
                                      │
                                      ▼
                          Final Component Graph
                                      │
        ┌─────────────────────────────┼─────────────────────────┐
        │                             │                         │
        ▼                             ▼                         ▼
  frontend.src.*              ui-kit.components.*      shared.api.*
```

## Namespace Mapping Example

```
┌──────────────────────────────────────────────────────────────────┐
│                     Namespace Mapping Table                       │
├────────────────────┬──────────────────┬──────────────────────────┤
│ Repository Path    │ Namespace        │ Example Component ID     │
├────────────────────┼──────────────────┼──────────────────────────┤
│ /repos/openframe-  │ openframe-       │ openframe-frontend.src.  │
│ frontend           │ frontend         │ components.Button.render │
├────────────────────┼──────────────────┼──────────────────────────┤
│ /repos/ui-kit      │ ui-kit           │ ui-kit.components.       │
│                    │                  │ Button.render            │
├────────────────────┼──────────────────┼──────────────────────────┤
│ /repos/shared-lib  │ shared-lib       │ shared-lib.utils.api.    │
│                    │                  │ fetchData                │
├────────────────────┼──────────────────┼──────────────────────────┤
│ /proj/backend      │ backend          │ backend.services.auth.   │
│                    │                  │ login                    │
└────────────────────┴──────────────────┴──────────────────────────┘
```

## Cross-Namespace Dependency Example

```
┌──────────────────────────────────────────────────────────────────┐
│              Cross-Namespace Dependency Resolution                │
└──────────────────────────────────────────────────────────────────┘

Repository Structure:
┌─────────────────────────────────────────────────────────────────┐
│  openframe-frontend/                                            │
│    └─ src/App.tsx                                               │
│         import { Button } from 'ui-kit/components'              │
│         import { fetchData } from 'shared-lib/api'              │
└─────────────────────────────────────────────────────────────────┘

Component Graph After Parsing:
┌─────────────────────────────────────────────────────────────────┐
│  Component: openframe-frontend.src.App                          │
│  Dependencies:                                                  │
│    ✓ openframe-frontend.src.utils.logger  (same namespace)     │
│    ✓ ui-kit.components.Button             (cross-namespace)    │
│    ✓ shared-lib.api.fetchData             (cross-namespace)    │
└─────────────────────────────────────────────────────────────────┘

Dependency Resolution Path:
1. AST finds: "Button", "fetchData"
2. Intra-namespace search: Not found in openframe-frontend.*
3. Cross-namespace search:
   - "Button" → found in ui-kit.components.Button ✓
   - "fetchData" → found in shared-lib.api.fetchData ✓
4. Final dependencies include both namespace types
```

## Class Hierarchy

```
┌──────────────────────────────────────────────────────────────────┐
│                        Class Hierarchy                            │
└──────────────────────────────────────────────────────────────────┘

DependencyParser
├─ Attributes:
│  ├─ repo_paths: List[str]              # NEW: All repository paths
│  ├─ repo_path: str                     # Maintained for backward compat
│  ├─ components: Dict[str, Node]        # All components (namespaced)
│  ├─ modules: Set[str]                  # All modules (namespaced)
│  ├─ include_patterns: List[str]        # File include patterns
│  ├─ exclude_patterns: List[str]        # File exclude patterns
│  └─ analysis_service: AnalysisService  # Service for analysis
│
└─ Methods:
   ├─ __init__(repo_path, include, exclude)
   ├─ parse_repository(filtered_folders) → Dict[str, Node]
   │
   ├─ _parse_single_repository(repo_path, ...) → Dict[str, Node]  # NEW
   ├─ _parse_multiple_repositories(...) → Dict[str, Node]         # NEW
   ├─ _get_namespace_from_path(repo_path) → str                   # NEW
   ├─ _build_namespaced_components(...) → Dict[str, Node]         # NEW
   ├─ _resolve_cross_namespace_dependencies(...)                  # NEW
   │
   ├─ _build_components_from_analysis(call_graph)
   ├─ _determine_component_type(func_dict) → str
   ├─ _file_to_module_path(file_path) → str
   └─ save_dependency_graph(output_path)

RepoAnalyzer
├─ Attributes:
│  ├─ include_patterns: List[str]
│  ├─ exclude_patterns: List[str]
│  └─ _namespace_roots: Dict[str, str]   # NEW: Maps namespace → repo_path
│
└─ Methods:
   ├─ __init__(include, exclude)
   ├─ analyze_repository_structure(repo_dir) → Dict
   │
   ├─ _analyze_multiple_repositories(repo_dirs) → Dict            # NEW
   ├─ _get_namespace_from_path(repo_path) → str                   # NEW
   │
   ├─ _build_file_tree(repo_dir) → Dict
   ├─ _should_exclude_path(path, filename) → bool
   ├─ _should_include_file(path, filename) → bool
   ├─ _count_files(tree) → int
   └─ _calculate_size(tree) → float
```

## Legend

```
┌──────────────────────────────────────────────────────────────────┐
│                            Legend                                 │
├──────────────────────────────────────────────────────────────────┤
│  →   Data flow / Process flow                                    │
│  ├─  Tree structure / Hierarchy                                  │
│  ✓   Successful resolution / Match found                         │
│  ✗   Failed resolution / No match                                │
│  NEW: New feature/method in this implementation                  │
└──────────────────────────────────────────────────────────────────┘
```
