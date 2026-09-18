# Contributing to CodeWiki

Thanks for your interest in contributing to CodeWiki — the AI-assisted documentation generator behind [Flamingo](https://flamingo.run) and [OpenFrame](https://openframe.ai). This guide covers how to set up your environment, our development workflow, and how to submit changes.

## Community

We don't use GitHub Issues or GitHub Discussions for this project. All discussion, support, and coordination happens in the OpenMSP Slack community:

- [OpenMSP](https://www.openmsp.ai/)
- [Join the Slack workspace](https://join.slack.com/t/openmsp/shared_invite/zt-36bl7mx0h-3~U2nFH6nqHqoTPXMaHEHA)

If you're planning a non-trivial change, it's a good idea to discuss it there first.

## Getting Set Up

CodeWiki is a Python project (Python 3.12, matching the runtime in `docker/Dockerfile`).

```bash
git clone https://github.com/flamingo-stack/CodeWiki.git
cd CodeWiki

# Create an isolated virtual environment
python3 -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

CodeWiki loads environment variables via `python-dotenv`, so you can place a `.env` file at the repository root instead of exporting variables manually:

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

Verify your setup:

```bash
# Confirm the CLI module loads
python -m codewiki --help

# Confirm the web app module imports cleanly
python -c "from codewiki.src.fe import web_app"
```

For the full local-development workflow — running the CLI, running the FastAPI web app with hot reload, and running via Docker Compose — see the [Local Development guide](./docs/development/setup/local-development.md).

## Project Architecture

Before making changes, it's worth understanding how the modules fit together:

- **CLI Core** (`codewiki/cli`) — terminal workflow, persistent configuration, generation pipeline adapter, HTML output, Git operations.
- **Backend Core** (`codewiki/src/be`) — dependency analysis, module clustering, agent orchestration, and Markdown generation/validation.
- **Frontend Core** (`codewiki/src/fe`) — FastAPI web application: route handlers, background job processing, caching, GitHub repository handling.
- **Config Core** (`codewiki/src/config.py`) — the shared `Config` dataclass consumed by every entry point.

See the [Architecture Overview](./docs/development/architecture/README.md) for diagrams and data-flow details, and the [Reference Documentation](./docs/README.md) for module-level deep dives.

## Security Guidelines

CodeWiki handles LLM API keys and clones third-party repositories, so security-conscious contributions matter:

- **Never persist API keys in plain configuration files.** Follow the existing pattern of storing secrets via the `keyring` library, not in `~/.codewiki/config.json` or `.env` files that get committed.
- **Keep `Config.to_dict()` secret-free by default.** If you add new sensitive fields to the `Config` dataclass, add them to `_RUNTIME_ONLY_SECRET_FIELDS` so they are excluded from serialization unless explicitly requested.
- **Validate untrusted input.** Follow the existing patterns in `validate_repository()` and `GitHubRepoProcessor.is_valid_github_url()` — validate paths and URLs before passing them to `git` or filesystem operations.
- **Keep agent file access sandboxed.** Documentation-generation agents may read arbitrary source files for context but must only write within the documentation output tree — do not widen this scope without careful review.
- **Never commit `.env` files containing real API keys.**

See the full [Security Best Practices](./docs/development/security/README.md) page for more detail and a review checklist.

## Development Workflow

1. **Discuss first** for larger changes — reach out on the OpenMSP Slack community.
2. **Fork and branch** from `main`. Use a descriptive branch name (e.g., `fix/config-validation`, `feat/php-analyzer`).
3. **Make focused changes** — keep pull requests scoped to a single concern (a bug fix, a feature, a docs update) to make review easier.
4. **Follow existing patterns**:
   - Use the project's typed errors (`ConfigurationError`, `RepositoryError`, `APIError`) instead of silent failures.
   - When touching `codewiki/src/config.py`, keep the per-provider (cluster/main/fallback) structure consistent for any new LLM-related settings.
   - When touching agent tools (`agent_tools/`), confirm write access remains scoped to the documentation output directory.
5. **Run and verify locally** using the commands in the [Local Development guide](./docs/development/setup/local-development.md) before opening a pull request — including running the CLI (`python -m codewiki generate`) and, where relevant, the web app (`python codewiki/run_web_app.py`).
6. **Open a pull request** against `main` on [flamingo-stack/CodeWiki](https://github.com/flamingo-stack/CodeWiki/pulls) with a clear description of what changed and why.

## Commit Messages

Write clear, descriptive commit messages that explain *why* a change was made, not just *what* changed. Reference the relevant module (e.g., `backend-core`, `cli-core`, `frontend-core`, `config-core`) when it helps reviewers orient quickly.

## Code Review

All changes are reviewed via pull request before merging. Reviewers will pay particular attention to:

- Whether new configuration fields correctly separate secrets from persisted/cached data.
- Whether new input-handling code (paths, URLs, CLI flags) is validated before use.
- Whether documentation-generation agent changes preserve the sandboxed read/write boundaries.

## Questions?

If you get stuck or want feedback on an approach before investing significant time, ask in the OpenMSP Slack community:
[Join here](https://join.slack.com/t/openmsp/shared_invite/zt-36bl7mx0h-3~U2nFH6nqHqoTPXMaHEHA).

---
<div align="center">
  Built with 💛 by the <a href="https://www.flamingo.run/about"><b>Flamingo</b></a> team
</div>
