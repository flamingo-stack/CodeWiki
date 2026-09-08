# Development Documentation

Welcome to the CodeWiki development documentation. This section covers everything you need to contribute to, extend, or run CodeWiki in a development environment.

---

## Overview

CodeWiki is a Python-based AI documentation engine. It is structured as a layered system with clearly separated responsibilities across CLI, backend services, dependency analysis, agent orchestration, LLM services, and a FastAPI web frontend.

The project uses:

- **Python** (3.9+) as the primary language
- **Click** for the CLI framework
- **FastAPI + Uvicorn** for the web interface
- **Pydantic AI** for AI agent orchestration
- **Tree-sitter** for multi-language AST parsing
- **VoltAgent** (via `@voltagent/core`) for documentation pipeline tooling
- **Anthropic SDK** and **OpenAI SDK** for LLM provider integration

---

## Quick Navigation

| Document | Description |
|---------|-------------|
| [Environment Setup](setup/environment.md) | IDE setup, tools, editor extensions |
| [Local Development](setup/local-development.md) | Clone, run, debug locally |
| [Architecture Overview](architecture/README.md) | High-level system design and component map |
| [Security Guidelines](security/README.md) | Auth patterns, secrets management, safe coding |
| [Testing Guide](testing/README.md) | Test structure, running tests, writing new tests |
| [Contributing Guidelines](contributing/guidelines.md) | Code style, PRs, commit conventions |

---

## Repository Structure

```text
CodeWiki/
│
├── codewiki/                    → Main Python package
│   ├── __init__.py              → Package entry point (version: 1.0.1)
│   ├── __main__.py              → CLI entry point
│   ├── run_web_app.py           → Web application startup script
│   │
│   ├── cli/                     → CLI Core
│   │   ├── main.py              → Click root command group
│   │   ├── config_manager.py    → Configuration + keyring storage
│   │   ├── git_manager.py       → Git integration
│   │   ├── html_generator.py    → GitHub Pages HTML generation
│   │   ├── adapters/            → CLIDocumentationGenerator
│   │   ├── commands/            → generate, config subcommands
│   │   ├── models/              → CLI data models
│   │   └── utils/               → Logging, progress, validation
│   │
│   └── src/                     → Backend core
│       ├── config.py            → Shared Config dataclass
│       ├── utils.py             → FileManager utilities
│       │
│       ├── be/                  → Backend services
│       │   ├── agent_orchestrator.py    → AI agent lifecycle
│       │   ├── documentation_generator.py → Main orchestration engine
│       │   ├── llm_services.py          → LLM provider factory
│       │   ├── cluster_modules.py       → Module clustering (LLM)
│       │   ├── prompt_template.py       → Prompt construction
│       │   ├── agent_tools/             → AI agent tool implementations
│       │   └── dependency_analyzer/     → Multi-language AST analysis
│       │       ├── analysis/            → AnalysisService, CallGraphAnalyzer
│       │       ├── analyzers/           → Per-language Tree-sitter analyzers
│       │       ├── models/              → Node, CallRelationship, AnalysisResult
│       │       ├── ast_parser.py        → DependencyParser
│       │       ├── dependency_graphs_builder.py → DependencyGraphBuilder
│       │       └── topo_sort.py         → Topological ordering
│       │
│       └── fe/                  → Web frontend (FastAPI)
│           ├── web_app.py       → FastAPI app definition
│           ├── routes.py        → HTTP route handlers
│           ├── background_worker.py → Async job processor
│           ├── cache_manager.py → SHA-256 based doc cache
│           ├── github_processor.py → Repo validation + cloning
│           └── config.py        → WebAppConfig
│
├── docker/
│   ├── Dockerfile               → Container build
│   └── docker-compose.yml       → Docker Compose deployment
│
├── examples/                    → Usage examples
└── test-multi-path/             → Multi-path integration tests
```

---

## Getting Started as a Developer

1. Read the [Environment Setup](setup/environment.md) guide for tool requirements
2. Follow [Local Development](setup/local-development.md) to clone and run locally
3. Study the [Architecture Overview](architecture/README.md) to understand the system
4. Review [Contributing Guidelines](contributing/guidelines.md) before submitting changes
