# Contributing to CodeWiki

Thank you for your interest in contributing to CodeWiki — the AI-powered documentation generator for source code repositories! This guide covers everything you need to develop, test, and contribute to CodeWiki itself (not a repository you're documenting *with* CodeWiki).

CodeWiki is a Python package (`pyproject.toml`, Python `>=3.12`) organized around a CLI (`codewiki/cli`), a backend documentation pipeline (`codewiki/src/be`), a FastAPI web application (`codewiki/src/fe`), and a shared runtime configuration model (`codewiki/src/config.py`).

## Getting Started

1. Read the [Architecture Overview](./docs/development/architecture/README.md) to understand how the CLI, backend, and frontend modules fit together.
2. Follow [Environment Setup](./docs/development/setup/environment.md) and [Local Development](./docs/development/setup/local-development.md) to get a working local copy of CodeWiki.
3. Review the [Documentation index](./docs/README.md) for links to further guides as they become available.

## Development Environment Setup

### Required Tools

| Tool | Version | Notes |
|---|---|---|
| Python | `>=3.12` | Matches `requires-python` in `pyproject.toml`. |
| pip | Latest | Used to install both runtime and `dev` optional dependencies. |
| Git | Any recent version | CodeWiki's own CLI and web app both shell out to `git` / use GitPython. |
| Node.js | `>=14.0.0` | Required by `mermaid-py`, which validates Mermaid diagrams embedded in generated docs during tests and generation. |
| Docker & Docker Compose | Recent version | Optional, for testing the containerized web app (`docker/docker-compose.yml`, `docker/Dockerfile`). |

### Installing Development Dependencies

```bash
pip install -e ".[dev]"
```

This installs, in addition to the runtime dependencies:

- `pytest`, `pytest-cov`, `pytest-asyncio` — testing
- `black` — code formatting (line length 100, target `py312`)
- `mypy` — static type checking (`python_version = "3.12"`)
- `ruff` — linting

### IDE Recommendations

If using **VS Code**, the following extensions align with the project's tooling:

- **Python** (Microsoft) — core language support, linting, debugging
- **Pylance** — type-checking assistance (complements `mypy`)
- **Black Formatter** — matches the project's `[tool.black]` configuration (line-length 100, `py312` target)
- **Ruff** — matches the project's linter configuration
- **Mermaid Preview** — useful when reviewing generated architecture diagrams in Markdown output

If using **PyCharm**, enable Black as the external formatter and configure the line length to 100 to match `[tool.black]` in `pyproject.toml`.

## Clone and Install

```bash
git clone https://github.com/flamingo-stack/CodeWiki.git
cd CodeWiki

# Editable install with development dependencies
pip install -e ".[dev]"
```

Editable installs (`-e`) mean changes to `codewiki/` source files take effect immediately without reinstalling — ideal for iterating on the CLI, backend pipeline, or web app.

Verify the CLI is on your `$PATH` and pointing at your local checkout:

```bash
codewiki --version
```

## Running the CLI Locally

```bash
codewiki config set \
  --cluster-api-key "sk-..." --main-api-key "sk-..." \
  --cluster-model "your-model" --main-model "your-model" \
  --cluster-base-url "https://api.your-provider.com/v1" \
  --main-base-url "https://api.your-provider.com/v1"

cd /path/to/some/repo
codewiki generate --verbose
```

You can also invoke the CLI as a module without relying on the installed console script:

```bash
python -m codewiki --help
python -m codewiki generate
```

## Running the Web Application Locally

```bash
python codewiki/run_web_app.py
```

This inserts `codewiki/src` onto `sys.path` and delegates to `fe.web_app.main()`. By default it listens on `127.0.0.1:8000`.

Alternatively, run it in a container using Docker Compose:

```bash
cd docker
docker compose up --build
```

The container maps port `8000` (overridable with the `APP_PORT` environment variable) and mounts `../output` for persistent cache/output storage, plus your `~/.ssh` directory (read-only) for cloning private repositories over SSH.

## Testing Your Changes Against Sample Fixtures

The repository includes a self-contained multi-path test fixture at `test-multi-path/` (with `main/`, `deps/`, `external/` subdirectories) specifically designed to exercise multi-root dependency analysis. Use it to sanity-check changes to the dependency analyzer without needing a large external repository:

```bash
python test-multi-path/test_multi_path.py
python test-multi-path/integration_test.py
```

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

## Code Style

- Format code with `black` (line length 100, `py312` target) before committing.
- Run `ruff` for linting and `mypy` for static type checking.
- Match the existing patterns in `codewiki/cli/`, `codewiki/src/be/`, and `codewiki/src/fe/` for module organization.

## Architecture Overview

CodeWiki is organized into six core layers: CLI Core, Frontend Core, the Documentation Generator, Agent Orchestration, LLM Services, and Dependency Analysis. See the [Architecture Overview](./docs/development/architecture/README.md) for the full data-flow diagrams and design rationale.

## Submitting Changes

1. Fork the repository and create a feature branch.
2. Make your changes, following the code style guidance above.
3. Test your changes locally, including against the `test-multi-path/` fixture where relevant.
4. Open a pull request against `https://github.com/flamingo-stack/CodeWiki`.

## Getting Help

This project does not use GitHub Issues or GitHub Discussions. For questions, feedback, or community discussion, join the OpenMSP Slack community:

- [https://www.openmsp.ai/](https://www.openmsp.ai/)
- [Slack invite link](https://join.slack.com/t/openmsp/shared_invite/zt-36bl7mx0h-3~U2nFH6nqHqoTPXMaHEHA)

---
<div align="center">
  Built with 💛 by the <a href="https://www.flamingo.run/about"><b>Flamingo</b></a> team
</div>
