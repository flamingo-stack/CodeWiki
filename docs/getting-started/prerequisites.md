# Prerequisites

Before installing CodeWiki, make sure your environment meets the following requirements.

## Required Software

| Software | Minimum Version | Why It's Needed |
|---|---|---|
| Python | `>=3.12` | CodeWiki is a Python package (`pyproject.toml` requires `requires-python = ">=3.12"`). |
| pip | Bundled with Python 3.12 | Used to install the `codewiki` package and its dependencies from `requirements.txt` / `pyproject.toml`. |
| Git | Any recent version | Required for repository cloning (web app), git-branch workflows (`--create-branch`), and commit-hash/branch detection. |
| Node.js | `>=14.0.0` | Declared as a build requirement in `pyproject.toml` (`[external] build-requires`) — used by `mermaid-py` to validate Mermaid diagrams embedded in generated documentation. |
| Docker & Docker Compose | Recent version | Optional — only needed if you want to run the web application via `docker/docker-compose.yml` instead of running it directly with Python. |

## System Requirements

- **OS**: Linux, macOS, or Windows. Keyring-backed credential storage uses the OS-native secret store: macOS Keychain, Windows Credential Manager, or a Linux Secret Service implementation (e.g., GNOME Keyring). If no keyring backend is available, CodeWiki degrades gracefully (API keys must then be supplied another way each run).
- **Disk space**: Sufficient space to clone the target repository plus generated output (`output/cache`, `output/temp`, `output/docs`, `output/dependency_graphs`).
- **Network access**: Outbound HTTPS access to your configured LLM provider endpoint(s) (e.g., OpenAI, Anthropic, or an OpenAI-compatible base URL) is required at generation time.

## Account / Access Requirements

CodeWiki does not include a bundled LLM — you must bring your own provider credentials for **each** of the three configurable model roles:

| Role | Purpose |
|---|---|
| **Cluster model** | Groups discovered code components into a hierarchical module tree. Recommended: a strong/top-tier model, since clustering quality drives overall documentation structure. |
| **Main model** | Writes the actual Markdown documentation for each module. |
| **Fallback model** | Used automatically if the main model call fails or is rate-limited. |

Each role has its own API key, base URL, API version (for Anthropic-style APIs), max-token setting, and temperature setting — they do not need to be the same provider.

## Environment Variables

CodeWiki's CLI does **not** rely on ad-hoc environment variables for normal operation — persistent configuration is stored in `~/.codewiki/config.json` (non-secret settings) and the OS keyring (API keys), managed via `codewiki config set`.

For the **test/diagnostic scripts** included in the repository (e.g., `test_clustering_*.py`), the following environment variables (or a local `.env.local` file) may be read directly:

| Variable | Purpose |
|---|---|
| `OPENAI_API_KEY` | API key for OpenAI-compatible providers used by ad-hoc clustering test scripts. |
| `ANTHROPIC_API_KEY` | API key for Anthropic providers used by ad-hoc clustering test scripts. |
| `MAIN_API_KEY` / `CLUSTER_API_KEY` / `FALLBACK_API_KEY` | Per-role overrides used by the same test scripts. |

For the **Docker Compose** deployment of the web application, environment values are loaded from an `.env` file referenced in `docker/docker-compose.yml` (`env_file: ../.env`), and `APP_PORT` controls the host port mapping (defaults to `8000`).

## Verification Commands

Run these commands to confirm your environment is ready before installing CodeWiki:

```bash
# Check Python version (must be 3.12 or higher)
python3 --version

# Check pip is available
pip3 --version

# Check Git is installed
git --version

# Check Node.js is installed (required by mermaid-py for diagram validation)
node --version

# Optional: check Docker and Docker Compose (only needed for the web app container)
docker --version
docker compose version
```

> **Note:** If `python3 --version` reports an older version than 3.12, install a compatible Python before proceeding — CodeWiki's `pyproject.toml` will refuse to install otherwise.

Once these checks pass, continue to the [Quick Start](quick-start.md) guide to install and run CodeWiki for the first time.
