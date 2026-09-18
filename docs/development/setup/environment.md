# Development Environment Setup

## IDE Recommendations

CodeWiki is a Python project (`codewiki/` package, Python 3.12 per the project's Dockerfile base image). Any editor with good Python support works well:

- **VS Code** with the Python extension (linting, debugging, IntelliSense) and the Pylance language server.
- **PyCharm** (Community or Professional) for full-featured Python development, including built-in debugging and refactoring tools.

## Required Development Tools

| Tool | Purpose |
|---|---|
| Python 3.12+ | Matches the runtime used in `docker/Dockerfile` |
| pip | Installing dependencies from `requirements.txt` |
| Git | Version control; also required at runtime for `GitManager` and repository cloning features |
| Docker & Docker Compose | Optional, for running the web application in a container matching production (`docker/docker-compose.yml`, `docker/Dockerfile`) |

## Setting Up Your Local Python Environment

```bash
git clone https://github.com/flamingo-stack/CodeWiki.git
cd CodeWiki

# Create an isolated virtual environment
python3 -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Environment Variables for Development

CodeWiki loads environment variables via `python-dotenv` (`load_dotenv()` in `codewiki/src/config.py`), so you can place a `.env` file at the repository root instead of exporting variables manually:

```bash
# .env (repository root)
MAIN_MODEL=claude-sonnet-4
CLUSTER_MODEL=claude-sonnet-4
FALLBACK_MODEL=claude-sonnet-4
MAIN_API_KEY=your-key-here
CLUSTER_API_KEY=your-key-here
FALLBACK_API_KEY=your-key-here
LLM_BASE_URL=https://api.anthropic.com/v1
MAX_OUTPUT_TOKENS=16384
```

> When developing against the CLI instead of the web app, prefer `codewiki config set` (which stores API keys in your OS keyring) over plaintext `.env` files, to match how the CLI is used in practice.

## Editor Extensions / Plugins

For VS Code, useful extensions include:

- **Python** (ms-python.python) — linting, debugging, testing integration
- **Pylance** — fast type-checking and IntelliSense
- **Docker** — for editing/inspecting `docker/Dockerfile` and `docker/docker-compose.yml`
- **Markdown All in One** or similar — since CodeWiki's core output is Markdown, a good Markdown preview/lint extension helps validate generated docs during development

## Verifying Your Setup

```bash
# Confirm the CLI module loads
python -m codewiki --help

# Confirm the web app module imports cleanly
python -c "from codewiki.src.fe import web_app"
```

Continue to [Local Development](local-development.md) to run CodeWiki end-to-end from source.
