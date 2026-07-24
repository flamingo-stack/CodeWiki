# Development Environment Setup

This guide covers IDE recommendations, required development tools, environment variables, and editor extensions for contributing to CodeWiki.

---

## IDE Recommendations

### VS Code (Recommended)

[Visual Studio Code](https://code.visualstudio.com/) provides the best experience for CodeWiki development.

**Recommended Extensions:**

| Extension | ID | Purpose |
|---|---|---|
| Python | `ms-python.python` | Python language support |
| Pylance | `ms-python.vscode-pylance` | Type checking and IntelliSense |
| Ruff | `charliermarsh.ruff` | Fast Python linter and formatter |
| YAML | `redhat.vscode-yaml` | YAML file support (docker-compose) |
| Docker | `ms-azuretools.vscode-docker` | Docker file editing and management |
| GitLens | `eamodio.gitlens` | Enhanced Git integration |
| Markdown All in One | `yzhang.markdown-all-in-one` | Markdown preview and editing |

**Workspace Settings (`.vscode/settings.json`):**

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": "explicit"
  },
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff"
  },
  "python.analysis.typeCheckingMode": "basic"
}
```

### PyCharm

PyCharm Professional or Community Edition also works well:

1. Open the `CodeWiki` directory as a project
2. Configure the Python interpreter to point to your virtual environment
3. Enable the **Pydantic** plugin for better dataclass support
4. Install the **Docker** plugin for `docker-compose.yml` editing

---

## Required Development Tools

### Python Virtual Environment

Always develop inside a virtual environment:

```bash
# Create a virtual environment
python -m venv .venv

# Activate it
# On Linux / macOS:
source .venv/bin/activate
# On Windows (PowerShell):
.venv\Scripts\Activate.ps1

# Install CodeWiki in editable mode with all dependencies
pip install -e .

# Verify
python -c "import codewiki; print(codewiki.__version__)"
# Expected: 1.0.1
```

### Node.js (for VoltAgent tooling)

```bash
# Install Node.js dependencies
npm install

# Verify
node --version   # v18.x.x or higher
npm --version    # 9.x.x or higher
```

### Git Configuration

Configure your git identity before contributing:

```bash
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

---

## Environment Variables for Development

Create a `.env` file in the project root for local development. This is used by Docker Compose and can also be sourced manually.

```bash
# .env — DO NOT COMMIT THIS FILE

# API keys for LLM providers
MAIN_API_KEY=sk-your-main-key
FALLBACK_API_KEY=sk-your-fallback-key
CLUSTER_API_KEY=sk-your-cluster-key

# Model names (optional — defaults to env var or hardcoded fallback)
MAIN_MODEL=claude-sonnet-4-5
CLUSTER_MODEL=claude-3-haiku-20240307
FALLBACK_MODEL=gpt-3.5-turbo

# Base URLs (set for non-OpenAI providers)
LLM_BASE_URL=https://api.anthropic.com/v1

# Token limits (optional)
MAX_OUTPUT_TOKENS=16384

# Web app port (Docker)
APP_PORT=8000
```

> **Security:** The `.env` file is for local development only. In production, inject secrets via your container runtime or secrets manager. Never commit `.env` to source control.

---

## Python Path Configuration

For running backend scripts directly without the CLI entrypoint, set `PYTHONPATH`:

```bash
# From the repo root
export PYTHONPATH=$(pwd)

# Then you can run backend modules directly
python -m codewiki.src.be.main --repo-path /path/to/repo
```

---

## Linting and Formatting

CodeWiki uses **Ruff** for linting and formatting:

```bash
# Install ruff if not already available
pip install ruff

# Lint all files
ruff check .

# Auto-fix fixable issues
ruff check --fix .

# Format code
ruff format .
```

---

## Pre-commit Hooks (Optional)

To automatically lint before each commit:

```bash
pip install pre-commit
pre-commit install
```

Create a `.pre-commit-config.yaml` if one doesn't exist:

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.4.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
```

---

## Docker Development Setup

For working on the web application in a containerized environment:

```bash
# Build the image
cd docker
docker compose build

# Start with environment file
docker compose --env-file ../.env up

# Tail logs
docker compose logs -f codewiki
```

The web app will be available at `http://localhost:8000`.
