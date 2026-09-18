# First Steps

You've generated your first documentation set — here's what to do next.

## 1. Review Your Generated Configuration

The CLI persists non-sensitive settings to `~/.codewiki/config.json`, while API keys are stored securely in your system keyring (macOS Keychain, Windows Credential Manager, or Linux Secret Service). Inspect what was saved:

```bash
cat ~/.codewiki/config.json
```

You can update any per-provider setting at any time with `codewiki config set`:

```bash
# Update just the fallback model's token limit
codewiki config set --fallback-max-tokens 64000
```

> Deprecated single-provider flags (`--base-url`, `--max-tokens`, `--api-version`, `--max-token-field`, `--api-path`) have been removed in favor of per-provider equivalents (`--cluster-*`, `--main-*`, `--fallback-*`). Attempting to use them raises a migration error with guidance.

## 2. Explore the Generated Documentation Tree

Open the output directory produced by your first run (default `docs/` relative to the analyzed repository):

- `README.md` — the top-level repository overview, generated last by summarizing all top-level modules.
- Per-module folders and Markdown files — hierarchical documentation for each logical module the clustering stage identified.
- `metadata.json` — statistics about the run (module count, files analyzed, generation time).

## 3. Scope Your Next Generation Run

`codewiki generate` supports several options to control scope and behavior:

```bash
# Only include specific file patterns
codewiki generate --include "*.py,*.ts"

# Exclude test files
codewiki generate --exclude "*Tests*,*test_*"

# Focus documentation on specific modules/paths
codewiki generate --focus "src/core,src/api"

# Choose a documentation type and add custom instructions
codewiki generate --doc-type architecture --instructions "Focus on public APIs"

# Skip the cache and force a full regeneration
codewiki generate --no-cache
```

By default, if documentation already exists at the output path, the CLI will prompt before overwriting it — pass `--force` to skip the prompt.

## 4. Try Git-Integrated Publishing

If your target directory is a git repository, you can have CodeWiki create a dedicated documentation branch and prepare it for review:

```bash
codewiki generate --create-branch --github-pages
```

This will:

- Verify the working tree is clean (or fail with `RepositoryError` unless forced).
- Create a timestamped branch like `docs/codewiki-20240315-143022`.
- Generate an `index.html` static viewer alongside the Markdown output for GitHub Pages.
- Print next-step instructions, including a URL you can use to open a pull request.

## 5. Try the Web Application Flow

If you'd rather not use the terminal for every run, start the FastAPI web app (see [Quick Start](quick-start.md) for Docker Compose setup) and submit repository URLs through the browser. The web app will:

- Validate the GitHub URL and check for a cached result first.
- Queue a background job if no cache hit exists, cloning the repository and running the same generation pipeline used by the CLI.
- Serve the finished documentation at `/docs/{job_id}` once processing completes.

## Getting Help

- Run `codewiki --help` or `codewiki generate --help` to see all available CLI options and inline documentation.
- Run `codewiki config set --help` for the full list of per-provider LLM configuration options.
- For community support, join the OpenMSP Slack community at https://www.openmsp.ai/ or via the invite link: https://join.slack.com/t/openmsp/shared_invite/zt-36bl7mx0h-3~U2nFH6nqHqoTPXMaHEHA
