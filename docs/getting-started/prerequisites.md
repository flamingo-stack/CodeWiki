# Prerequisites

Before setting up CodeWiki, make sure your environment meets the following requirements.

## Required Software

| Software | Purpose | Notes |
|---|---|---|
| Python 3 | Runs the CLI and the FastAPI web application | CodeWiki is a pure Python project (`codewiki/` package) |
| pip | Installs Python dependencies | Standard with most Python installations |
| Git | Repository cloning, branch/commit automation (`GitManager`), and repository validation | Required for both the CLI's `--create-branch` workflow and the web app's repository cloning |
| Docker & Docker Compose (optional) | Runs the web application as a container | Only needed if you use `docker/docker-compose.yml` instead of running Python directly |

> CodeWiki analyzes source files across several languages (Python, JavaScript, TypeScript, Java, C, C++, C#, PHP) but CodeWiki itself is implemented entirely in Python — you do not need compilers or runtimes for those languages to run CodeWiki.

## System Requirements

- A machine capable of running Python 3 and cloning git repositories.
- Outbound network access to your configured LLM provider endpoint(s), since documentation generation makes HTTP calls to LLM APIs (OpenAI-compatible endpoints, Anthropic, or a local LiteLLM proxy).
- Sufficient disk space to clone target repositories and store generated documentation under an `output/` directory.

## Account / Access Requirements

- **LLM provider credentials** — CodeWiki requires API keys for its LLM-backed generation stages. The pipeline is split into three provider "slots" — **cluster**, **main**, and **fallback** — each with its own model, API key, and base URL. You need at least one working provider configured for all three slots (they can point to the same provider/model).
- **GitHub access** (optional) — If you plan to use `codewiki generate --create-branch` and open a pull request with generated docs, you'll need push access to the target repository.

## Environment Variables

CodeWiki reads configuration either from CLI-managed local storage (`~/.codewiki/config.json` + system keyring) or from environment variables (used by `Config.from_args()` for the web app / non-interactive contexts). The core variables are:

| Variable | Required | Description |
|---|---|---|
| `MAIN_MODEL` | Optional (has default) | Model used for main documentation generation. Defaults to `claude-sonnet-4`. |
| `CLUSTER_MODEL` | Optional | Model used for the module-clustering stage. Defaults to `MAIN_MODEL`. |
| `FALLBACK_MODEL` | Required (via `from_args`) | Model used when the main model fails. |
| `CLUSTER_API_KEY` | Required (via `from_args`) | API key for the clustering-stage provider. |
| `MAIN_API_KEY` | Required (via `from_args`) | API key for the main generation-stage provider. |
| `FALLBACK_API_KEY` | Required (via `from_args`) | API key for the fallback-stage provider. |
| `LLM_BASE_URL` | Optional | Base URL for the LLM endpoint. Defaults to `http://0.0.0.0:4000/` (e.g. a local LiteLLM proxy). |
| `MAX_OUTPUT_TOKENS` | Optional | Maximum output tokens per LLM call. Defaults to `16384`. |
| `APP_PORT` | Optional | Port the web application listens on when run via Docker Compose. Defaults to `8000`. |

> **Note:** When using the CLI, most of these values are instead collected interactively and persisted via `codewiki config set`, with API keys stored securely in your OS keyring rather than plain environment variables. See `codewiki config set --help` for the full list of per-provider options (cluster/main/fallback model, base URL, max tokens, temperature, API version).

## Verification Commands

Run the following to confirm your environment is ready:

```bash
# Confirm Python is installed
python3 --version

# Confirm pip is available
pip --version

# Confirm Git is installed
git --version

# (Optional) Confirm Docker and Docker Compose are installed
docker --version
docker compose version
```

Once CodeWiki is installed (see [Quick Start](quick-start.md)), verify the CLI is working:

```bash
# Show CLI help
codewiki --help

# Show version info
codewiki version
```

## Next Steps

Continue to the [Quick Start](quick-start.md) guide to install CodeWiki and generate your first documentation set.
