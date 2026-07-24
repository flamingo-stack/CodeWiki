# Development Environment Setup

This guide covers the tools, IDE configuration, and editor extensions recommended for contributing to CodeWiki.

---

## Required Development Tools

| Tool | Version | Purpose |
|------|---------|---------|
| **Python** | 3.9+ | Primary runtime |
| **pip** | 22+ | Package management |
| **Git** | 2.x+ | Version control |
| **virtualenv** or **venv** | Any | Isolated Python environments |

---

## Recommended IDE

### Visual Studio Code

VS Code is the recommended IDE for CodeWiki development.

**Recommended extensions:**

| Extension | ID | Purpose |
|-----------|-----|---------|
| Python | `ms-python.python` | Python language support |
| Pylance | `ms-python.vscode-pylance` | Type checking and IntelliSense |
| Ruff | `charliermarsh.ruff` | Fast Python linter and formatter |
| GitLens | `eamodio.gitlens` | Enhanced Git history views |
| Mermaid Preview | `bierner.markdown-mermaid` | Preview Mermaid diagrams in Markdown |
| YAML | `redhat.vscode-yaml` | YAML support for config files |
| Docker | `ms-azuretools.vscode-docker` | Docker file editing and container management |

**Suggested VS Code `settings.json`:**

```json
{
  "python.defaultInterpreterPath": ".venv/bin/python",
  "editor.formatOnSave": true,
  "python.formatting.provider": "none",
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true
  },
  "python.analysis.typeCheckingMode": "basic",
  "editor.rulers": [88]
}
```

---

### PyCharm

PyCharm Professional or Community also works well.

**Configuration:**

1. Open the project root as a PyCharm project
2. Set the Python interpreter to your virtual environment
3. Enable **PEP 8** code style inspection
4. Install the **Mermaid** plugin for diagram previews

---

## Python Environment Setup

Always use a virtual environment for development to avoid polluting your system Python:

```bash
# Create a virtual environment
python3 -m venv .venv

# Activate it
# On Linux/macOS:
source .venv/bin/activate

# On Windows (PowerShell):
.venv\Scripts\Activate.ps1

# Install in editable mode with all dependencies
pip install -e .
```

Verify the CLI is available:

```bash
codewiki --version
```

---

## Environment Variables for Development

Create a `.env` file in the project root for web app development:

```bash
# Copy from the template if available
cp .env.example .env
```

Key variables for local development:

```bash
# LLM provider settings
MAIN_MODEL=claude-sonnet-4
CLUSTER_MODEL=claude-sonnet-4
LLM_BASE_URL=https://api.anthropic.com/v1
MAIN_API_KEY=your_dev_api_key

# Output token limit (reduce for faster dev cycles)
MAX_OUTPUT_TOKENS=8192

# Max token field (use max_completion_tokens for o3 reasoning models)
CODEWIKI_GENERATION_MAX_TOKEN_FIELD=max_tokens
CODEWIKI_CLUSTER_MAX_TOKEN_FIELD=max_tokens
CODEWIKI_FALLBACK_MAX_TOKEN_FIELD=max_tokens
```

> **Note:** The `.env` file is loaded automatically by `python-dotenv` when running the web app. CLI mode uses the OS keychain instead.

---

## Code Style

CodeWiki follows standard Python conventions:

- **PEP 8** style guidelines
- **88-character** line length (matching Black/Ruff defaults)
- Type annotations are encouraged for function signatures
- Docstrings use standard Python docstring format

**Linting and formatting:**

```bash
# Install ruff (if not installed)
pip install ruff

# Lint the codebase
ruff check codewiki/

# Auto-fix where possible
ruff check --fix codewiki/

# Format code
ruff format codewiki/
```

---

## Tree-sitter Language Bindings

CodeWiki uses Tree-sitter for AST-based code parsing across 8 languages. On first use, language grammars are compiled or downloaded automatically. No manual setup is required.

If you are working on language analyzer code, you may want to install the Tree-sitter CLI for grammar development:

```bash
pip install tree-sitter
```

Language-specific analyzer files are in:

```text
codewiki/src/be/dependency_analyzer/analyzers/
├── python.py
├── javascript.py
├── typescript.py
├── java.py
├── csharp.py
├── c.py
├── cpp.py
└── php.py
```

---

## Working with the Docker Setup

For full-stack local testing with Docker:

```bash
# Build the image
docker build -f docker/Dockerfile -t codewiki:0.0.1 .

# Start with Docker Compose
cd docker
docker-compose up
```

The web app will be available at `http://localhost:8000`.

**Volume mounts (from `docker-compose.yml`):**

- `../output` → `/app/output` — Persistent cache and output storage
- `~/.ssh` → `/root/.ssh:ro` — Git credentials for private repositories (read-only)

---

## Keyring (CLI Development)

When developing CLI features, configuration is stored in:

- **API keys:** OS keychain under the service name `codewiki`
- **Other settings:** `~/.codewiki/config.json`

To inspect or reset configuration during development:

```bash
# Show current configuration
codewiki config show

# Reset a specific setting
codewiki config set --main-model gpt-4o-mini

# Clear all configuration
# Manually delete: ~/.codewiki/config.json
# Manually remove keychain entries via your OS keychain manager
```
