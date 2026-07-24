# Local Development Guide

This guide walks you through cloning CodeWiki, running it locally, and configuring your development workflow.

---

## Clone and Setup

```bash
# Clone the repository
git clone https://github.com/flamingo-stack/CodeWiki.git
cd CodeWiki

# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate   # Linux/macOS
# .venv\Scripts\Activate.ps1  # Windows PowerShell

# Install in editable mode
pip install -e .

# Verify installation
codewiki --version
```

---

## Running the CLI Locally

The CLI is the primary development interface. After `pip install -e .`, the `codewiki` command is available in your virtual environment.

### Configure LLM Credentials

```bash
codewiki config set \
  --main-model claude-sonnet-4 \
  --main-api-key sk-ant-your-key \
  --main-base-url https://api.anthropic.com/v1 \
  --cluster-model claude-sonnet-4 \
  --cluster-api-key sk-ant-your-key \
  --cluster-base-url https://api.anthropic.com/v1 \
  --fallback-model claude-sonnet-4 \
  --fallback-api-key sk-ant-your-key \
  --fallback-base-url https://api.anthropic.com/v1
```

### Run Generation on a Repository

```bash
# Generate docs for any local repository
codewiki generate --output /tmp/test-docs /path/to/some-repo
```

### Run Against the CodeWiki Repository Itself

```bash
# Document CodeWiki's own codebase
codewiki generate --output ./self-docs
```

---

## Running the Web Application Locally

The web app is a FastAPI application served via Uvicorn.

### Configure Environment

Create a `.env` file in the project root:

```bash
MAIN_MODEL=claude-sonnet-4
LLM_BASE_URL=https://api.anthropic.com/v1
MAIN_API_KEY=sk-ant-your-key
CLUSTER_API_KEY=sk-ant-your-key
FALLBACK_API_KEY=sk-ant-your-key
```

### Start the Web Server

```bash
# Standard start
python -m codewiki.run_web_app

# With auto-reload (development mode)
python -m codewiki.run_web_app --reload

# Custom host and port
python -m codewiki.run_web_app --host 0.0.0.0 --port 8080

# Debug mode (verbose logging)
python -m codewiki.run_web_app --debug --reload
```

The web app starts at `http://localhost:8000`.

### Web App Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Documentation submission form |
| `/` | POST | Submit a repository URL |
| `/api/job/{job_id}` | GET | JSON job status |
| `/docs/{job_id}` | GET | Redirect to generated docs |
| `/static-docs/{job_id}/{filename}` | GET | Serve generated Markdown as HTML |

---

## Development Workflow

### Working on CLI Commands

CLI commands are in `codewiki/cli/commands/`:

- [`generate.py`](https://github.com/flamingo-stack/CodeWiki/blob/main/codewiki/cli/commands/generate.py) — The `codewiki generate` command
- [`config.py`](https://github.com/flamingo-stack/CodeWiki/blob/main/codewiki/cli/commands/config.py) — The `codewiki config` command group

To test a CLI change immediately (editable install picks it up automatically):

```bash
codewiki generate --help
```

### Working on Backend Logic

Core backend files:

- [`codewiki/src/be/documentation_generator.py`](https://github.com/flamingo-stack/CodeWiki/blob/main/codewiki/src/be/documentation_generator.py) — Main orchestration
- [`codewiki/src/be/agent_orchestrator.py`](https://github.com/flamingo-stack/CodeWiki/blob/main/codewiki/src/be/agent_orchestrator.py) — AI agent lifecycle
- [`codewiki/src/be/llm_services.py`](https://github.com/flamingo-stack/CodeWiki/blob/main/codewiki/src/be/llm_services.py) — LLM provider factory
- [`codewiki/src/be/cluster_modules.py`](https://github.com/flamingo-stack/CodeWiki/blob/main/codewiki/src/be/cluster_modules.py) — Module clustering

### Working on the Dependency Analyzer

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

The analysis pipeline entry point:

```text
codewiki/src/be/dependency_analyzer/analysis/analysis_service.py
```

---

## Running with Docker Compose (Local)

For a fully containerized local environment:

```bash
# Build the Docker image
docker build -f docker/Dockerfile -t codewiki:0.0.1 .

# Create the external Docker network
docker network create codewiki-network

# Create output directory
mkdir -p output

# Start the service
cd docker
docker-compose up
```

The app will be available at `http://localhost:8000` (or whichever port `APP_PORT` is set to in your `.env`).

**Stop the service:**

```bash
docker-compose down
```

---

## Debug Configuration

### CLI Verbose Logging

```bash
codewiki generate --verbose
```

### Web App Debug Mode

```bash
python -m codewiki.run_web_app --debug
```

This enables `log_level=debug` in Uvicorn, showing all request/response details.

### Python Debugger (pdb)

You can insert breakpoints directly in Python source files:

```python
import pdb; pdb.set_trace()
```

Or use VS Code's Python debugger by creating a launch configuration:

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

## Hot Reload

The web app supports hot reload via Uvicorn's `--reload` flag:

```bash
python -m codewiki.run_web_app --reload
```

Changes to `.py` files under `codewiki/src/fe/` are picked up automatically.

For CLI development, the editable install (`pip install -e .`) means any changes to `codewiki/cli/` are immediately reflected without reinstalling.

---

## Inspecting LLM Requests

To monitor LLM API calls during development:

- Set `log_level=debug` to see raw request sizes
- Each `call_llm()` invocation logs: model name, base URL, prompt length, temperature, token field, and response length
- Request counts are tracked and logged every 100 requests via `increment_request_counter()`

Check logs for patterns like:

```text
[LLM] Model: claude-sonnet-4 | Base URL: https://api.anthropic.com/v1
[LLM] Prompt length: 4200 chars | Max tokens: 16384
[LLM] Response length: 1850 chars
```
