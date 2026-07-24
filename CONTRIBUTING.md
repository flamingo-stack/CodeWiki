# Contributing to CodeWiki

Thank you for your interest in contributing to CodeWiki! This guide covers everything you need to get started — from setting up your development environment to submitting your first pull request.

> **Community-first**: We don't use GitHub Issues or GitHub Discussions. All questions, feedback, and collaboration happen on the **OpenMSP Slack Community**. [Join us here](https://join.slack.com/t/openmsp/shared_invite/zt-36bl7mx0h-3~U2nFH6nqHqoTPXMaHEHA).

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Environment](#development-environment)
- [Project Structure](#project-structure)
- [Development Workflow](#development-workflow)
- [Code Style](#code-style)
- [Submitting a Pull Request](#submitting-a-pull-request)
- [Community](#community)

---

## Code of Conduct

CodeWiki is part of the OpenFrame open-source ecosystem. We are committed to fostering a welcoming, inclusive community. Please be respectful in all interactions — on Slack, in pull requests, and in code reviews.

---

## Getting Started

### Prerequisites

Before contributing, make sure you have:

| Tool | Minimum Version |
|---|---|
| Python | 3.9+ |
| pip | 22.0+ |
| Git | 2.30+ |
| Node.js | 18.0+ (optional, for VoltAgent tooling) |
| Docker | 24.0+ (optional, for container testing) |

### Fork and Clone

```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/flamingo-stack/CodeWiki.git
cd CodeWiki
```

---

## Development Environment

### 1. Create a Virtual Environment

```bash
python -m venv .venv

# Activate on Linux / macOS
source .venv/bin/activate

# Activate on Windows PowerShell
.venv\Scripts\Activate.ps1
```

### 2. Install in Editable Mode

```bash
pip install -e .

# Verify the CLI is available
codewiki --version
# Expected: CodeWiki CLI v1.0.1
```

### 3. Install Node.js Dependencies (Optional)

Required only if working on the VoltAgent orchestration layer:

```bash
npm install
```

### 4. Configure Environment Variables

Create a `.env` file in the project root. **Never commit this file.**

```bash
# .env — DO NOT COMMIT
MAIN_API_KEY=sk-your-main-key
FALLBACK_API_KEY=sk-your-fallback-key
CLUSTER_API_KEY=sk-your-cluster-key

MAIN_MODEL=claude-sonnet-4-5
CLUSTER_MODEL=claude-3-haiku-20240307
FALLBACK_MODEL=gpt-3.5-turbo

LLM_BASE_URL=https://api.anthropic.com/v1
MAX_OUTPUT_TOKENS=16384
APP_PORT=8000
```

### 5. Configure API Keys for CLI

```bash
codewiki config set \
  --cluster-api-key sk-your-key \
  --main-api-key sk-your-key \
  --fallback-api-key sk-your-key \
  --cluster-base-url https://api.anthropic.com/v1 \
  --main-base-url https://api.anthropic.com/v1 \
  --fallback-base-url https://api.anthropic.com/v1 \
  --cluster-model claude-3-haiku-20240307 \
  --main-model claude-sonnet-4-5 \
  --fallback-model claude-3-haiku-20240307
```

### Recommended IDE: VS Code

**Recommended Extensions:**

| Extension | ID | Purpose |
|---|---|---|
| Python | `ms-python.python` | Python language support |
| Pylance | `ms-python.vscode-pylance` | Type checking and IntelliSense |
| Ruff | `charliermarsh.ruff` | Linter and formatter |
| Docker | `ms-azuretools.vscode-docker` | Docker file management |
| GitLens | `eamodio.gitlens` | Enhanced Git integration |
| Markdown All in One | `yzhang.markdown-all-in-one` | Markdown preview |

**Workspace settings (`.vscode/settings.json`):**

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

---

## Project Structure

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

## Development Workflow

### Running the CLI Locally

```bash
# Generate docs for the CodeWiki repo itself (a great "hello world" test)
codewiki generate --output ./docs --doc-type architecture

# Verbose mode — see detailed logs including LLM requests
codewiki generate --verbose
```

### Running the Web App Locally

```bash
# Default: http://127.0.0.1:8000
python codewiki/run_web_app.py

# With hot reload and debug output
python -m codewiki.src.fe.web_app --host 0.0.0.0 --port 8080 --reload --debug
```

### Running with Docker Compose

```bash
cp .env.example .env
# Edit .env with your keys

cd docker
docker compose up --build

# View logs
docker compose logs -f

# Stop
docker compose down
```

### VS Code Debugger

Add to `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "CodeWiki CLI Generate",
      "type": "debugpy",
      "request": "launch",
      "module": "codewiki.cli.main",
      "args": ["generate", "--output", "./docs", "--doc-type", "architecture"],
      "cwd": "${workspaceFolder}",
      "env": {
        "PYTHONPATH": "${workspaceFolder}"
      },
      "justMyCode": false
    },
    {
      "name": "CodeWiki Web App",
      "type": "debugpy",
      "request": "launch",
      "module": "codewiki.src.fe.web_app",
      "args": ["--host", "127.0.0.1", "--port", "8000", "--debug"],
      "cwd": "${workspaceFolder}",
      "envFile": "${workspaceFolder}/.env"
    }
  ]
}
```

---

## Code Style

CodeWiki uses **Ruff** for linting and formatting.

```bash
# Install ruff
pip install ruff

# Lint all files
ruff check .

# Auto-fix fixable issues
ruff check --fix .

# Format code
ruff format .
```

### Pre-commit Hooks (Recommended)

```bash
pip install pre-commit
pre-commit install
```

Create `.pre-commit-config.yaml` if it doesn't exist:

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.4.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
```

### Development Philosophy

Please follow these principles when writing code for CodeWiki:

1. **Idempotent outputs** — Re-running documentation generation must always be safe. Existing files should be skipped.
2. **Leaf-first processing** — Child modules must be documented before parents so overviews are accurate.
3. **Provider-agnostic LLM** — All model interactions go through OpenAI-compatible APIs. No provider lock-in.
4. **Security by default** — File reads must use path traversal guards. API keys stay in the system keychain, never in plain text.
5. **Separation of concerns** — CLI, web app, and backend must remain clearly separated. `DocumentationGenerator` should have no CLI or web-app dependencies.

---

## Submitting a Pull Request

1. **Create a feature branch** from `main`:

```bash
git checkout -b feat/your-feature-name
```

2. **Make your changes** — follow the code style guidelines above.

3. **Test your changes** — run the CLI against a real repository and confirm output is correct.

4. **Lint before pushing**:

```bash
ruff check --fix .
ruff format .
```

5. **Commit with a clear message**:

```bash
git commit -m "feat: add support for Rust language analysis"
```

6. **Push and open a Pull Request** on GitHub:

```bash
git push origin feat/your-feature-name
```

Then open a PR at [https://github.com/flamingo-stack/CodeWiki/pulls](https://github.com/flamingo-stack/CodeWiki/pulls).

### PR Guidelines

- Keep PRs focused — one feature or fix per PR
- Include a clear description of what changed and why
- Reference any related Slack discussion if applicable
- Ensure the CLI still works end-to-end before requesting review

---

## Troubleshooting

| Issue | Likely Cause | Fix |
|---|---|---|
| `codewiki: command not found` | Package not installed | Run `pip install -e .` |
| `ConfigurationError: API key not found` | Keys not set | Run `codewiki config set --main-api-key ...` |
| `RepositoryError: Not a git repository` | Running outside a git repo | Run `git init` or navigate to a git repo |
| Port 8000 already in use | Another process using the port | Use `--port 8080` or stop the conflicting process |

---

## Community

All support, questions, and discussion happen on **Slack** — not GitHub Issues.

- 💬 **Join OpenMSP Slack**: [https://join.slack.com/t/openmsp/shared_invite/zt-36bl7mx0h-3~U2nFH6nqHqoTPXMaHEHA](https://join.slack.com/t/openmsp/shared_invite/zt-36bl7mx0h-3~U2nFH6nqHqoTPXMaHEHA)
- 🌐 **Community Hub**: [https://www.openmsp.ai/](https://www.openmsp.ai/)
- 🦩 **Flamingo**: [https://flamingo.run](https://flamingo.run)
- 🖥️ **OpenFrame**: [https://openframe.ai](https://openframe.ai)

---

<div align="center">
  Built with 💛 by the <a href="https://www.flamingo.run/about"><b>Flamingo</b></a> team
</div>
