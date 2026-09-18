# Quick Start

This guide gets you from a fresh clone to your first generated documentation set as quickly as possible.

## TL;DR Setup

### Option A — Run the CLI locally

```bash
# 1. Clone the repository
git clone https://github.com/flamingo-stack/CodeWiki.git
cd CodeWiki

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Configure your LLM provider (cluster/main/fallback)
python -m codewiki config set \
  --cluster-api-key "YOUR_API_KEY" \
  --main-api-key "YOUR_API_KEY" \
  --fallback-api-key "YOUR_API_KEY" \
  --cluster-model "claude-sonnet-4" \
  --main-model "claude-sonnet-4" \
  --fallback-model "claude-sonnet-4" \
  --cluster-base-url "https://api.anthropic.com/v1" \
  --main-base-url "https://api.anthropic.com/v1" \
  --fallback-base-url "https://api.anthropic.com/v1"

# 4. Run it against any local repository
cd /path/to/some/repo
python -m codewiki generate
```

### Option B — Run the web application with Docker Compose

```bash
# 1. Clone the repository
git clone https://github.com/flamingo-stack/CodeWiki.git
cd CodeWiki

# 2. Provide environment variables (LLM keys, models, etc.) in a .env file
#    at the repository root (see Prerequisites for the full variable list)
cat > .env << 'EOF'
MAIN_MODEL=claude-sonnet-4
CLUSTER_MODEL=claude-sonnet-4
FALLBACK_MODEL=claude-sonnet-4
MAIN_API_KEY=YOUR_API_KEY
CLUSTER_API_KEY=YOUR_API_KEY
FALLBACK_API_KEY=YOUR_API_KEY
EOF

# 3. Create the external network required by the compose file
docker network create codewiki-network

# 4. Start the web application
docker compose -f docker/docker-compose.yml up -d --build
```

The web application listens on `http://localhost:8000` (configurable via `APP_PORT`).

> **Note:** No default credentials, usernames, or passwords are built into CodeWiki — LLM API keys must come from your own provider account, and you supply them explicitly as shown above.

## A "Hello World" Example

Once configured, generate documentation for CodeWiki's own repository (or any repository you have locally):

```bash
cd CodeWiki
python -m codewiki generate
```

This runs the full pipeline:

1. **Repository validation** — confirms the current directory is a supported repository and detects languages present.
2. **Dependency analysis** — parses source files and builds a dependency graph.
3. **Module clustering** — an LLM groups related code components into logical modules.
4. **Documentation generation** — each module (leaf-first, then parents) is documented and written as Markdown.
5. **Finalization** — a repository-level overview and `metadata.json` are written to the output directory.

## Expected Output

By default, generated docs are written under a `docs/` output directory relative to your target repository, containing:

```text
docs/
├── README.md              # Top-level repository overview
├── metadata.json           # Generation statistics and job info
└── <module-name>/
    └── <module-name>.md    # Per-module documentation
```

If you passed `--github-pages` to `codewiki generate`, an `index.html` static viewer is also produced alongside the Markdown files.

The terminal output shows staged progress (dependency analysis → clustering → documentation generation) with colored status messages and a completion summary listing the files generated.

## Using the Web Application (Manual Flow)

If you're running the FastAPI web app (Option B, or directly via `python codewiki/run_web_app.py`):

1. Open `http://localhost:8000` in your browser.
2. Submit a GitHub repository URL (and optionally a commit ID) through the form.
3. The job is queued and processed by a background worker; poll `GET /api/job/{job_id}` for status, or wait on the redirect.
4. Once complete, view the generated documentation at `/docs/{job_id}`.

## Next Steps

- Read [First Steps](first-steps.md) to learn what to configure and explore right after your first run.
- Review [Prerequisites](prerequisites.md) if any command above failed due to missing tools or environment variables.
