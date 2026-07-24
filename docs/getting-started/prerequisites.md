# Prerequisites

Before installing and running CodeWiki, ensure your environment meets the following requirements.

---

## Required Software

| Tool | Minimum Version | Purpose |
|---|---|---|
| **Python** | 3.9+ | Core runtime for all CodeWiki components |
| **pip** | 22.0+ | Python package installation |
| **Git** | 2.30+ | Repository cloning and branch management |
| **Node.js** | 18.0+ | VoltAgent-based tooling (optional, for doc orchestration) |
| **Docker** | 24.0+ | Container-based deployment (optional) |
| **Docker Compose** | v2.0+ | Web app container orchestration (optional) |

> **Note:** Node.js and Docker are only required if you plan to use the VoltAgent orchestration layer or run the web application via Docker Compose. The core CLI works with Python only.

---

## System Requirements

| Resource | Minimum | Recommended |
|---|---|---|
| **RAM** | 2 GB | 4 GB+ |
| **Disk** | 500 MB free | 2 GB+ (for cloned repos and doc output) |
| **OS** | Linux, macOS, Windows (WSL2) | Linux or macOS |
| **Internet** | Required | Stable connection for LLM API calls |

---

## LLM API Access

CodeWiki uses **three configurable LLM model roles**: `cluster`, `main`, and `fallback`. Each requires an API key from an OpenAI-compatible provider.

| Role | Purpose | Recommended Default |
|---|---|---|
| `main` | Documentation generation (primary) | `claude-sonnet-4`, `gpt-4o` |
| `fallback` | Fallback if main model fails | `claude-3-haiku`, `gpt-3.5-turbo` |
| `cluster` | Module clustering / grouping | `gpt-4o-mini`, `claude-3-haiku` |

Supported providers include:

- [Anthropic](https://console.anthropic.com/) — Claude models
- [OpenAI](https://platform.openai.com/) — GPT models
- Any **OpenAI-compatible** REST API (local models, Azure OpenAI, etc.)

You will need:
- **API keys** for each of the three roles (can reuse the same key)
- **Base URLs** for each provider endpoint

---

## Environment Variables

CodeWiki reads the following environment variables. These are required for the web application mode and the backend documentation generator.

| Variable | Required | Description |
|---|---|---|
| `MAIN_API_KEY` | Yes | API key for the primary documentation model |
| `FALLBACK_API_KEY` | Yes | API key for the fallback model |
| `CLUSTER_API_KEY` | Yes | API key for the clustering model |
| `MAIN_MODEL` | No | Model name override for main (e.g., `claude-sonnet-4`) |
| `CLUSTER_MODEL` | No | Model name override for cluster |
| `LLM_BASE_URL` | No | Base URL for OpenAI-compatible API |
| `MAX_OUTPUT_TOKENS` | No | Max tokens for LLM output (default: `16384`) |
| `APP_PORT` | No | Port for Docker web app (default: `8000`) |

> **CLI Mode:** When using the `codewiki` CLI, API keys are stored securely in the **system keychain** via the `keyring` library and managed through `codewiki config set`. You do not need to set environment variables manually for CLI usage.

---

## Python Dependencies

CodeWiki's Python backend uses the following key libraries (installed automatically via `pip install`):

| Package | Purpose |
|---|---|
| `pydantic-ai` | AI agent framework for documentation generation |
| `click` | CLI framework |
| `fastapi` | Web application server |
| `uvicorn` | ASGI server |
| `gitpython` | Git operations |
| `keyring` | Secure API key storage |
| `glob` | File pattern matching |

---

## Node.js Dependencies (VoltAgent Tooling)

The `package.json` in the root includes VoltAgent-based orchestration utilities:

| Package | Version | Purpose |
|---|---|---|
| `@voltagent/core` | ^2.9.0 | Agent orchestration framework |
| `@ai-sdk/anthropic` | ^2.0.91 | Anthropic AI SDK adapter |
| `@anthropic-ai/sdk` | ^0.115.0 | Anthropic SDK |
| `zod` | ^4.4.3 | Schema validation |
| `glob` | ^13.0.6 | File pattern matching |

---

## Verifying Your Environment

Run these commands to confirm your environment is ready:

```bash
# Python version
python --version
# Expected: Python 3.9.x or higher

# pip version
pip --version
# Expected: pip 22.x or higher

# Git version
git --version
# Expected: git version 2.30.x or higher

# Node.js version (optional)
node --version
# Expected: v18.x.x or higher

# Docker version (optional)
docker --version
# Expected: Docker version 24.x.x or higher

# Docker Compose version (optional)
docker compose version
# Expected: Docker Compose version v2.x.x
```

---

## Next Steps

Once your environment is verified, proceed to the [Quick Start guide](quick-start.md) to install CodeWiki and generate your first documentation.
