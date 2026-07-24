# Development Documentation

Welcome to the CodeWiki development documentation. This section covers everything you need to contribute to or extend CodeWiki — from setting up your local environment to understanding the architecture and contributing code.

---

## Quick Navigation

| Document | Description |
|---|---|
| [Environment Setup](setup/environment.md) | IDE configuration, editor extensions, dev tools |
| [Local Development](setup/local-development.md) | Clone, install, run locally, debug |
| [Architecture Overview](architecture/README.md) | System design, component map, data flows |
| [Security Guidelines](security/README.md) | Auth patterns, secrets management, threat mitigations |
| [Testing Guide](testing/README.md) | Test structure, running tests, writing new tests |
| [Contributing Guidelines](contributing/guidelines.md) | Code style, PR process, commit conventions |

---

## Technology Stack

CodeWiki is a **Python-first** project with a Node.js layer for VoltAgent-based orchestration tooling.

### Backend (Python)

| Layer | Technology |
|---|---|
| CLI framework | [Click](https://click.palletsprojects.com/) |
| AI agent framework | [pydantic-ai](https://ai.pydantic.dev/) |
| Web application | [FastAPI](https://fastapi.tiangolo.com/) + [Uvicorn](https://www.uvicorn.org/) |
| LLM providers | OpenAI-compatible APIs (Anthropic, OpenAI, local models) |
| Git operations | [GitPython](https://gitpython.readthedocs.io/) |
| Secrets storage | [keyring](https://pypi.org/project/keyring/) |
| AST analysis | Python `ast`, language-specific parsers |
| Schema validation | [Pydantic](https://docs.pydantic.dev/) |

### Tooling (Node.js)

| Package | Purpose |
|---|---|
| `@voltagent/core` | Agent orchestration framework |
| `@ai-sdk/anthropic` | Anthropic AI SDK adapter |
| `@anthropic-ai/sdk` | Anthropic SDK |
| `zod` | Schema validation |

---

## Repository Layout

```text
CodeWiki/
├── codewiki/                  # Main Python package
│   ├── cli/                   # CLI commands, config, git manager
│   │   ├── adapters/          # CLIDocumentationGenerator adapter
│   │   ├── commands/          # Click commands: generate, config
│   │   ├── models/            # Config and Job dataclasses
│   │   └── utils/             # Validation, logging, errors
│   ├── src/
│   │   ├── be/                # Backend: agents, LLM, dependency analysis
│   │   │   ├── agent_tools/   # pydantic-ai tool implementations
│   │   │   ├── dependency_analyzer/  # AST parsing + graph building
│   │   │   └── ...
│   │   ├── fe/                # FastAPI web application
│   │   │   ├── web_app.py     # Main FastAPI app
│   │   │   ├── background_worker.py
│   │   │   ├── cache_manager.py
│   │   │   └── ...
│   │   └── config.py          # Central Config dataclass
│   └── run_web_app.py         # Web app startup script
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── examples/                  # Usage examples
├── package.json               # Node.js dependencies
└── test_*.py                  # Test files
```

---

## Development Philosophy

1. **Idempotent outputs** — Re-running documentation generation is always safe. Existing files are skipped.
2. **Leaf-first processing** — Child modules are documented before parents, so overviews are accurate.
3. **Provider-agnostic LLM** — All model interactions go through OpenAI-compatible APIs. Swap providers without code changes.
4. **Security by default** — File reads use path traversal guards. API keys are stored in the system keychain, never in plain text.
5. **Separation of concerns** — CLI, web app, and backend are clearly separated. The backend `DocumentationGenerator` has no CLI or web-app dependencies.
