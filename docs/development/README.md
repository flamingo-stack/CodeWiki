# Development Documentation

This section covers everything you need to develop, test, and contribute to **CodeWiki** itself — the AI-powered documentation generator, not a repository you're documenting *with* CodeWiki.

CodeWiki is a Python package (`pyproject.toml`, Python `>=3.12`) organized around a CLI (`codewiki/cli`), a backend documentation pipeline (`codewiki/src/be`), a FastAPI web application (`codewiki/src/fe`), and a shared runtime configuration model (`codewiki/src/config.py`).

## Quick Navigation

| Guide | Description |
|---|---|
| [Environment Setup](setup/environment.md) | IDE recommendations, required tools, and development environment variables. |
| [Local Development](setup/local-development.md) | Cloning the repo, installing in editable mode, running the CLI and web app locally, and debugging. |
| [Architecture Overview](architecture/README.md) | High-level module architecture, core components, and data flow through the documentation pipeline. |
| [Security](security/README.md) | Credential storage, safe file access, input validation, and secure coding practices used in CodeWiki. |
| [Testing](testing/README.md) | Structure of the diagnostic/validation scripts, how to run them, and expectations for new tests. |
| [Contributing Guidelines](contributing/guidelines.md) | Code style, branch naming, commit format, and the review checklist for pull requests. |

## Where to Start

1. Read the [Architecture Overview](architecture/README.md) to understand how the CLI, backend, and frontend modules fit together.
2. Follow [Environment Setup](setup/environment.md) and [Local Development](setup/local-development.md) to get a working local copy of CodeWiki.
3. Review [Security](security/README.md) and [Testing](testing/README.md) before submitting changes.
4. Read [Contributing Guidelines](contributing/guidelines.md) before opening a pull request.
