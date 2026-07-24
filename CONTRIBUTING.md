# Contributing to CodeWiki

Thank you for your interest in contributing to CodeWiki! CodeWiki is an open-source project maintained by the [Flamingo](https://flamingo.run) team and the [OpenMSP community](https://www.openmsp.ai/).

---

## Community

All contributions, discussions, and support happen in the **OpenMSP Slack community** — we do not use GitHub Issues or GitHub Discussions.

- **Join OpenMSP Slack:** [Join here](https://join.slack.com/t/openmsp/shared_invite/zt-36bl7mx0h-3~U2nFH6nqHqoTPXMaHEHA)
- **Community portal:** [openmsp.ai](https://www.openmsp.ai/)

Before opening a pull request, please discuss your proposed change in Slack first.

---

## Development Setup

### Prerequisites

| Tool | Minimum Version |
|------|----------------|
| Python | 3.9+ |
| pip | 22+ |
| Git | 2.x |

### Clone and install

```bash
git clone https://github.com/flamingo-stack/CodeWiki.git
cd CodeWiki

# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate        # Linux / macOS
# .venv\Scripts\Activate.ps1    # Windows PowerShell

# Install in editable mode
pip install -e .

# Verify installation
codewiki --version
```

### Configure LLM credentials (for testing)

```bash
codewiki config set \
  --main-model claude-sonnet-4 \
  --main-api-key YOUR_API_KEY \
  --main-base-url https://api.anthropic.com/v1 \
  --cluster-model claude-sonnet-4 \
  --cluster-api-key YOUR_API_KEY \
  --cluster-base-url https://api.anthropic.com/v1 \
  --fallback-model claude-sonnet-4 \
  --fallback-api-key YOUR_API_KEY \
  --fallback-base-url https://api.anthropic.com/v1
```

---

## Project Structure

```text
CodeWiki/
│
├── codewiki/                    → Main Python package
│   ├── cli/                     → CLI Core (commands, config, git, html)
│   └── src/
│       ├── be/                  → Backend (doc generator, agent orchestrator, LLM services)
│       │   └── dependency_analyzer/  → Multi-language AST analysis
│       └── fe/                  → Web frontend (FastAPI)
│
├── docker/                      → Dockerfile and docker-compose.yml
└── examples/                    → Usage examples
```

Key files to understand:

- `codewiki/src/be/documentation_generator.py` — Main orchestration engine
- `codewiki/src/be/agent_orchestrator.py` — AI agent lifecycle
- `codewiki/src/be/llm_services.py` — LLM provider factory
- `codewiki/src/be/dependency_analyzer/` — Multi-language AST parsing
- `codewiki/cli/commands/generate.py` — The `codewiki generate` command
- `codewiki/cli/config_manager.py` — Configuration and keyring management

---

## Code Style

CodeWiki follows standard Python conventions:

- **PEP 8** style guidelines
- **88-character** line length (Ruff/Black defaults)
- Type annotations encouraged for all function signatures
- Standard Python docstring format

### Linting and formatting

```bash
# Install ruff
pip install ruff

# Lint
ruff check codewiki/

# Auto-fix
ruff check --fix codewiki/

# Format
ruff format codewiki/
```

### Recommended VS Code extensions

| Extension | Purpose |
|-----------|---------|
| `ms-python.python` | Python language support |
| `ms-python.vscode-pylance` | Type checking and IntelliSense |
| `charliermarsh.ruff` | Linting and formatting |
| `bierner.markdown-mermaid` | Mermaid diagram preview |

---

## Making Changes

### Working on CLI commands

CLI commands are in `codewiki/cli/commands/`:

- `generate.py` — The `codewiki generate` command
- `config.py` — The `codewiki config` command group

The editable install (`pip install -e .`) picks up changes immediately — no reinstall needed.

```bash
codewiki generate --help
```

### Working on backend logic

Core backend files:

- `codewiki/src/be/documentation_generator.py` — Main orchestration
- `codewiki/src/be/agent_orchestrator.py` — AI agent lifecycle
- `codewiki/src/be/llm_services.py` — LLM provider factory
- `codewiki/src/be/cluster_modules.py` — Module clustering

### Working on language analyzers

Analyzer files follow a per-language pattern:

```text
codewiki/src/be/dependency_analyzer/analyzers/
├── python.py       ← PythonASTAnalyzer
├── javascript.py   ← TreeSitterJSAnalyzer
├── typescript.py   ← TreeSitterTSAnalyzer
├── java.py         ← TreeSitterJavaAnalyzer
├── csharp.py       ← TreeSitterCSharpAnalyzer
├── c.py            ← TreeSitterCAnalyzer
├── cpp.py          ← TreeSitterCppAnalyzer
└── php.py          ← TreeSitterPHPAnalyzer
```

### Running the web app locally

```bash
# Create a .env file in the project root
MAIN_MODEL=claude-sonnet-4
LLM_BASE_URL=https://api.anthropic.com/v1
MAIN_API_KEY=your_dev_api_key

# Start with hot reload
python -m codewiki.run_web_app --reload
```

The app starts at `http://localhost:8000`.

---

## Docker Development

For fully containerized local testing:

```bash
# Build the Docker image
docker build -f docker/Dockerfile -t codewiki:0.0.1 .

# Create the Docker network
docker network create codewiki-network

# Create output directory
mkdir -p output

# Start with Docker Compose
cd docker
docker-compose up
```

Stop the service:

```bash
docker-compose down
```

---

## Debugging

### CLI verbose mode

```bash
codewiki generate --verbose
```

### Web app debug mode

```bash
python -m codewiki.run_web_app --debug --reload
```

### VS Code launch configuration

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "CodeWiki CLI",
      "type": "debugpy",
      "request": "launch",
      "module": "codewiki",
      "args": ["generate", "--output", "/tmp/test-docs"],
      "cwd": "/path/to/some-repo",
      "env": {
        "PYTHONPATH": "${workspaceFolder}"
      }
    },
    {
      "name": "CodeWiki Web App",
      "type": "debugpy",
      "request": "launch",
      "module": "codewiki.run_web_app",
      "args": ["--reload", "--debug"],
      "cwd": "${workspaceFolder}",
      "envFile": "${workspaceFolder}/.env"
    }
  ]
}
```

---

## Pull Request Guidelines

1. **Discuss first** — Open a thread in [OpenMSP Slack](https://join.slack.com/t/openmsp/shared_invite/zt-36bl7mx0h-3~U2nFH6nqHqoTPXMaHEHA) before starting large changes
2. **One concern per PR** — Keep pull requests focused and minimal
3. **Follow code style** — Run `ruff check` and `ruff format` before submitting
4. **Test your change** — Run `codewiki generate` against a real repository to verify end-to-end behaviour
5. **Describe your change** — Write a clear PR description explaining what changed and why
6. **Keep secrets out** — Never commit API keys, `.env` files, or credentials

---

## Security

- **API keys** are stored in the OS keychain via the `keyring` library — never in any file
- **Never commit** `.env` files, API keys, or any credentials to the repository
- `.env` must be listed in `.gitignore`

---

## Architecture Reference

Before making significant changes, review the architecture documentation:

- [Architecture Overview](./docs/development/architecture/README.md)
- [Full Reference Documentation](./docs/README.md)

---

## License

By contributing to CodeWiki, you agree that your contributions will be licensed under the same license as the project. See [LICENSE.md](./LICENSE.md) for details.

---

<div align="center">
  Built with 💛 by the <a href="https://www.flamingo.run/about"><b>Flamingo</b></a> team
</div>
