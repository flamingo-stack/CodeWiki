# Prerequisites

Before installing and running CodeWiki, ensure your environment meets the following requirements.

---

## Required Software

| Software | Minimum Version | Purpose |
|---------|-----------------|---------|
| **Python** | 3.9+ | Runtime for all CodeWiki modules |
| **Git** | 2.x | Repository cloning and branch management |
| **pip** | 22+ | Python package installation |

> **Python Version Note:** Python 3.9 is the minimum required version. The security module uses `Path.is_relative_to()` with a compatibility fallback for 3.8, but 3.9+ is recommended for full feature support.

---

## System Requirements

| Resource | Recommended |
|---------|-------------|
| **RAM** | 4 GB minimum; 8 GB recommended for large repositories |
| **Disk** | 2 GB free space for output, caches, and temporary clones |
| **CPU** | Any modern multi-core processor |
| **OS** | Linux, macOS, or Windows (WSL2 recommended on Windows) |
| **Network** | Internet access required for LLM API calls |

---

## LLM Provider Requirements

CodeWiki requires access to at least one LLM provider. You will need API keys for the models you configure:

| Provider | Supported? | Notes |
|---------|------------|-------|
| **Anthropic** (Claude) | ✅ Yes | Default model is `claude-sonnet-4` |
| **OpenAI** | ✅ Yes | GPT-4, GPT-4o, o3, etc. |
| **Azure OpenAI** | ✅ Yes | Requires `api_version` configuration |
| **OpenAI-compatible proxies** | ✅ Yes | Any endpoint following the OpenAI API format |
| **LiteLLM / LLM proxies** | ✅ Yes | Useful for routing across providers |

CodeWiki uses **three model roles**:

| Role | Purpose |
|------|---------|
| **Main model** | Primary documentation generation |
| **Cluster model** | Module grouping and structural reasoning |
| **Fallback model** | Backup if the main model fails |

All three can point to the same provider or different providers.

---

## Environment Variables (Web App Mode)

When running the web application (as opposed to the CLI), CodeWiki reads configuration from environment variables. Create a `.env` file in the repository root:

```bash
# Primary LLM model
MAIN_MODEL=claude-sonnet-4

# Cluster model (defaults to MAIN_MODEL if not set)
CLUSTER_MODEL=claude-sonnet-4

# Base URL for your LLM endpoint
LLM_BASE_URL=https://api.anthropic.com/v1

# Your API keys
MAIN_API_KEY=your_main_api_key_here
CLUSTER_API_KEY=your_cluster_api_key_here
FALLBACK_API_KEY=your_fallback_api_key_here

# Max output tokens (optional, default: 16384)
MAX_OUTPUT_TOKENS=16384

# Token field name for reasoning models (optional)
# Use 'max_completion_tokens' for o3, o3-mini, etc.
CODEWIKI_GENERATION_MAX_TOKEN_FIELD=max_tokens
CODEWIKI_CLUSTER_MAX_TOKEN_FIELD=max_tokens
CODEWIKI_FALLBACK_MAX_TOKEN_FIELD=max_tokens
```

> **Security Note:** Never commit your `.env` file to version control. Add it to `.gitignore`.

---

## Environment Variables (Docker Mode)

When using Docker, the `.env` file is loaded automatically via the `env_file` directive in `docker/docker-compose.yml`. Place the `.env` file in the repository root (one level above the `docker/` directory).

---

## CLI Configuration (CLI Mode)

When using the CLI, API keys are stored securely in your **OS keychain** — not in any file:

- **macOS:** macOS Keychain
- **Windows:** Windows Credential Manager
- **Linux:** Linux Secret Service (via `keyring` library)

Non-sensitive settings (model names, URLs, token limits) are stored at:

```text
~/.codewiki/config.json
```

No manual `.env` file is required for CLI usage. Configuration is set using:

```bash
codewiki config set --main-api-key YOUR_KEY --main-model claude-sonnet-4
```

---

## Optional: Docker

For containerized deployment, Docker and Docker Compose are supported:

| Tool | Version |
|------|---------|
| Docker | 20.x+ |
| Docker Compose | v2.x+ |

---

## Verification Commands

Run these commands to verify your environment is ready:

```bash
# Check Python version (must be 3.9+)
python3 --version

# Check pip version
pip --version

# Check Git version
git --version

# Verify Python can import required packages after installation
python3 -c "import click; print('click OK')"
python3 -c "import fastapi; print('fastapi OK')"
```

---

## Required Python Packages

CodeWiki depends on several key Python packages. These are installed automatically via `pip` during installation:

| Package | Purpose |
|---------|---------|
| `click` | CLI framework |
| `fastapi` + `uvicorn` | Web application framework |
| `pydantic-ai` | AI agent framework |
| `openai` | OpenAI SDK (used for provider-agnostic API calls) |
| `anthropic` | Anthropic SDK |
| `tree-sitter` + language bindings | AST-based code parsing |
| `keyring` | Secure API key storage for CLI |
| `python-dotenv` | `.env` file loading |
| `jinja2` | HTML template rendering |
| `gitpython` | Git repository interaction |

All dependencies are declared in the project's dependency manifests and installed during setup.
