# Development Environment Setup

This guide covers the tools and settings recommended for developing CodeWiki itself.

## Required Development Tools

| Tool | Version | Notes |
|---|---|---|
| Python | `>=3.12` | Matches `requires-python` in `pyproject.toml`. |
| pip | Latest | Used to install both runtime and `dev` optional dependencies. |
| Git | Any recent version | CodeWiki's own CLI and web app both shell out to `git` / use GitPython. |
| Node.js | `>=14.0.0` | Required by `mermaid-py`, which validates Mermaid diagrams embedded in generated docs during tests and generation. |
| Docker & Docker Compose | Recent version | Optional, for testing the containerized web app (`docker/docker-compose.yml`, `docker/Dockerfile`). |

## Installing Development Dependencies

CodeWiki defines an optional `dev` dependency group in `pyproject.toml`:

```bash
pip install -e ".[dev]"
```

This installs, in addition to the runtime dependencies:

- `pytest`, `pytest-cov`, `pytest-asyncio` — testing
- `black` — code formatting (line length 100, target `py312`)
- `mypy` — static type checking (`python_version = "3.12"`)
- `ruff` — linting

## IDE Recommendations

Any editor with solid Python tooling works well. If using **VS Code**, the following extensions align with the project's tooling:

- **Python** (Microsoft) — core language support, linting, debugging
- **Pylance** — type-checking assistance (complements `mypy`)
- **Black Formatter** — matches the project's `[tool.black]` configuration (line-length 100, `py312` target)
- **Ruff** — matches the project's linter configuration
- **Mermaid Preview** — useful when reviewing generated architecture diagrams in Markdown output

If using **PyCharm**, enable Black as the external formatter and configure the line length to 100 to match `[tool.black]` in `pyproject.toml`.

## Development Environment Variables

CodeWiki's core CLI configuration lives in `~/.codewiki/config.json` and the OS keyring — it does not require environment variables for normal development use. However, a few areas of the codebase do read environment variables directly:

| Variable | Used By | Purpose |
|---|---|---|
| `OPENAI_API_KEY` | Ad-hoc clustering test scripts (`test_clustering_*.py`) | API key for OpenAI-compatible providers during manual testing. |
| `ANTHROPIC_API_KEY` | Ad-hoc clustering test scripts | API key for Anthropic providers during manual testing. |
| `MAIN_API_KEY` / `CLUSTER_API_KEY` / `FALLBACK_API_KEY` | Ad-hoc clustering test scripts | Per-role overrides used when running the standalone clustering diagnostics. |
| `PYTHONPATH` | Docker image / `run_web_app.py` path setup | Set to `/app` inside the container; locally, `run_web_app.py` inserts `codewiki/src` onto `sys.path` itself. |
| `APP_PORT` | `docker/docker-compose.yml` | Host port mapping for the containerized web app (defaults to `8000`). |

> **Tip:** For scripts that read API keys from the environment, consider using a local `.env.local` file with `python-dotenv` (already a project dependency) rather than exporting secrets into your shell history.

## Next Steps

Continue to [Local Development](local-development.md) to clone the repository, install it in editable mode, and run the CLI or web app locally.
