# Quick Start

Get CodeWiki running and generate your first documentation in under 5 minutes.

---

## TL;DR (5-Step Setup)

```bash
# 1. Clone the repository
git clone https://github.com/flamingo-stack/CodeWiki.git
cd CodeWiki

# 2. Install dependencies
pip install -e .

# 3. Configure your LLM provider (API key stored in OS keychain)
codewiki config set \
  --main-api-key YOUR_API_KEY \
  --main-model claude-sonnet-4 \
  --main-base-url https://api.anthropic.com/v1 \
  --cluster-api-key YOUR_API_KEY \
  --cluster-model claude-sonnet-4 \
  --cluster-base-url https://api.anthropic.com/v1 \
  --fallback-api-key YOUR_API_KEY \
  --fallback-model claude-sonnet-4 \
  --fallback-base-url https://api.anthropic.com/v1

# 4. Navigate to your project
cd /path/to/your/repository

# 5. Generate documentation
codewiki generate
```

That's it. Documentation is written to `./docs/` by default.

---

## Step-by-Step Guide

### Step 1 — Clone CodeWiki

```bash
git clone https://github.com/flamingo-stack/CodeWiki.git
cd CodeWiki
```

### Step 2 — Install

```bash
pip install -e .
```

This installs the `codewiki` CLI command and all required Python dependencies.

Verify installation:

```bash
codewiki --version
```

Expected output:

```text
CodeWiki CLI, version 1.0.1
```

### Step 3 — Configure Your LLM Provider

CodeWiki supports any OpenAI-compatible LLM endpoint. Configure it once using the CLI:

```bash
codewiki config set \
  --main-model gpt-4o \
  --main-api-key sk-your-openai-key \
  --main-base-url https://api.openai.com/v1 \
  --cluster-model gpt-4o-mini \
  --cluster-api-key sk-your-openai-key \
  --cluster-base-url https://api.openai.com/v1 \
  --fallback-model gpt-3.5-turbo \
  --fallback-api-key sk-your-openai-key \
  --fallback-base-url https://api.openai.com/v1
```

> **API Key Security:** Keys are stored securely in your OS keychain (macOS Keychain, Windows Credential Manager, or Linux Secret Service). They are never written to disk in plaintext.

Verify your configuration was saved:

```bash
codewiki config show
```

### Step 4 — Generate Documentation

Navigate to the repository you want to document and run:

```bash
cd /path/to/your-project
codewiki generate
```

The CLI will show a progress display with stage-by-stage updates:

```text
[1/5] Dependency Analysis ................... 40%
[2/5] Module Clustering ..................... 20%
[3/5] Documentation Generation ............. 30%
[4/5] HTML Generation ....................... 5%
[5/5] Finalization .......................... 5%
```

### Step 5 — View Results

Once complete, open the generated documentation:

```bash
ls ./docs/
```

You will find:

```text
docs/
├── README.md              ← Repository overview
├── module_tree.json       ← Module structure metadata
├── metadata.json          ← Generation metadata
└── <module-name>/
    └── <module-name>.md   ← Per-module documentation
```

---

## Using OpenAI

```bash
codewiki config set \
  --main-model gpt-4o \
  --main-api-key sk-... \
  --main-base-url https://api.openai.com/v1 \
  --cluster-model gpt-4o \
  --cluster-api-key sk-... \
  --cluster-base-url https://api.openai.com/v1 \
  --fallback-model gpt-4o-mini \
  --fallback-api-key sk-... \
  --fallback-base-url https://api.openai.com/v1
```

## Using Anthropic (Claude)

```bash
codewiki config set \
  --main-model claude-sonnet-4 \
  --main-api-key sk-ant-... \
  --main-base-url https://api.anthropic.com/v1 \
  --cluster-model claude-sonnet-4 \
  --cluster-api-key sk-ant-... \
  --cluster-base-url https://api.anthropic.com/v1 \
  --fallback-model claude-haiku-4 \
  --fallback-api-key sk-ant-... \
  --fallback-base-url https://api.anthropic.com/v1
```

---

## Quick Options Reference

| Flag | Description | Default |
|------|-------------|---------|
| `--output / -o` | Output directory | `./docs` |
| `--create-branch` | Auto-create a Git branch | Off |
| `--github-pages` | Generate GitHub Pages `index.html` | Off |
| `--include` | Comma-separated glob patterns to include | All files |
| `--exclude` | Comma-separated glob patterns to exclude | None |
| `--doc-type` | Style: `api`, `architecture`, `user-guide`, `developer` | Default |
| `--max-depth` | Maximum module nesting depth | 2 |

### Example: Architecture docs for a Python project

```bash
codewiki generate \
  --doc-type architecture \
  --output ./architecture-docs \
  --exclude "tests/,*.test.py"
```

### Example: Focus on specific modules

```bash
codewiki generate \
  --focus "src/core,src/api" \
  --instructions "Focus on public APIs and include usage examples"
```

### Example: CI/CD pipeline

```bash
codewiki generate \
  --create-branch \
  --github-pages \
  --output ./docs
```

---

## Try the Web Interface

CodeWiki also provides a web UI. To start it locally:

```bash
python -m codewiki.run_web_app
```

Then open your browser at `http://localhost:8000` and paste any public GitHub repository URL to generate documentation.

---

## Next Steps

After your first successful generation:

- Review [First Steps](first-steps.md) to explore key features in depth
- Check the [Prerequisites](prerequisites.md) if you encountered setup issues
