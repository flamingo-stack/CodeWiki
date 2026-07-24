# Quick Start

Get CodeWiki running and generate your first documentation in under 5 minutes.

---

## TL;DR — Fastest Path

```bash
# 1. Clone CodeWiki
git clone https://github.com/flamingo-stack/CodeWiki.git
cd CodeWiki

# 2. Install in editable mode
pip install -e .

# 3. Configure API keys (stored securely in system keychain)
codewiki config set \
  --cluster-api-key YOUR_API_KEY \
  --main-api-key YOUR_API_KEY \
  --cluster-base-url https://api.anthropic.com/v1 \
  --main-base-url https://api.anthropic.com/v1 \
  --cluster-model claude-3-haiku-20240307 \
  --main-model claude-sonnet-4-5

# 4. Generate documentation for any local repo
codewiki generate --output ./docs
```

---

## Step-by-Step Installation

### Step 1 — Clone the Repository

```bash
git clone https://github.com/flamingo-stack/CodeWiki.git
cd CodeWiki
```

### Step 2 — Install Python Dependencies

```bash
# Install CodeWiki as an editable package (recommended for development)
pip install -e .

# Verify the CLI is available
codewiki --version
# Expected: CodeWiki CLI v1.0.1
```

### Step 3 — Configure Your LLM Providers

CodeWiki uses three model roles: `cluster` (for grouping modules), `main` (for writing docs), and `fallback` (backup if main fails).

```bash
codewiki config set \
  --cluster-api-key sk-your-cluster-key \
  --main-api-key sk-your-main-key \
  --fallback-api-key sk-your-fallback-key \
  --cluster-base-url https://api.openai.com/v1 \
  --main-base-url https://api.openai.com/v1 \
  --fallback-base-url https://api.openai.com/v1 \
  --cluster-model gpt-4o-mini \
  --main-model gpt-4o \
  --fallback-model gpt-3.5-turbo
```

> **Tip:** You can reuse the same API key and base URL for all three roles — just pass it three times with `--cluster-api-key`, `--main-api-key`, and `--fallback-api-key`.

### Step 4 — Generate Documentation

Run `codewiki generate` inside any git repository:

```bash
# Navigate to a project you want to document
cd /path/to/your/project

# Generate docs into ./docs (default output directory)
codewiki generate

# Or specify a custom output directory
codewiki generate --output ./wiki
```

---

## Generate Documentation for CodeWiki Itself

As a "Hello World" example, generate docs for the CodeWiki repository:

```bash
cd CodeWiki

codewiki generate --output ./docs --doc-type architecture
```

### Expected Output

```text
📊 Analyzing repository...
🔍 Building dependency graph...
🗂️  Clustering modules...
✍️  Generating documentation (leaf-first)...
  ✅ dependency_analyzer
  ✅ agent_tools
  ✅ llm_services
  ✅ documentation_generator
  ✅ web_app
✅ Documentation generated successfully!

Output: ./docs/
```

### Output Structure

```text
docs/
├── metadata.json
├── module_tree.json
├── overview.md
└── ModuleName/
    └── ModuleName.md
```

---

## Quick Start — Web Application Mode

If you prefer a browser interface to submit GitHub URLs:

```bash
# Start the web app (default: http://127.0.0.1:8000)
python codewiki/run_web_app.py
```

Then open your browser at `http://127.0.0.1:8000`, paste a GitHub repository URL, and click **Generate**.

---

## Quick Start — Docker Compose

For a containerized deployment of the web app:

```bash
# Copy and configure the environment file
cp .env.example .env
# Edit .env with your API keys

# Start the container
cd docker
docker compose up -d
```

The web app will be available at `http://localhost:8000` (or the port configured via `APP_PORT` in `.env`).

---

## Useful CLI Options

| Flag | Description |
|---|---|
| `--output / -o` | Output directory (default: `./docs`) |
| `--doc-type` | Style: `api`, `architecture`, `user-guide`, `developer` |
| `--include` | Comma-separated glob patterns to include (e.g., `*.py`) |
| `--exclude` | Comma-separated glob patterns to exclude |
| `--focus` | Comma-separated module paths to prioritize |
| `--max-depth` | Maximum module nesting depth (default: `2`) |
| `--instructions` | Custom freeform prompt instructions for the LLM |
| `--create-branch` | Auto-create a git branch before writing docs |
| `--github-pages` | Generate `index.html` for GitHub Pages hosting |
| `--no-cache` | Force full regeneration, bypassing cache |

---

## Next Steps

- Read [First Steps](first-steps.md) to explore key features like branch creation, filtering, and custom instructions
- Review [Prerequisites](prerequisites.md) if you encounter installation issues
