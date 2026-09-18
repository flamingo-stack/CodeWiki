# Security Best Practices

CodeWiki handles LLM API keys, clones third-party repositories, and writes generated files to disk. This page documents the security patterns already present in the codebase and best practices to follow when extending it.

## Secrets and Credential Storage

- **API keys are never persisted in plain configuration files.** The CLI's `ConfigManager` writes non-sensitive settings (models, base URLs, token limits, temperatures) to `~/.codewiki/config.json`, but stores API keys in the OS-native secure credential store via the `keyring` library (macOS Keychain, Windows Credential Manager, Linux Secret Service).
- **`Config.to_dict()` excludes secrets by default.** The backend `Config` dataclass defines `_RUNTIME_ONLY_SECRET_FIELDS` (`cluster_api_key`, `main_api_key`, `fallback_api_key`) and strips them from any serialized dict unless the caller explicitly passes `include_secrets=True`. This prevents accidental logging, caching, or transmission of credentials.
- **`from_dict()` enforces secret completeness.** If a caller tries to reconstruct a `Config` from a dict that's missing required secret fields, construction raises a `TypeError` rather than silently defaulting to an insecure or broken state.
- **Environment variables as a fallback.** In non-interactive contexts (the web app, `Config.from_args()`), API keys and models are read from environment variables (`MAIN_API_KEY`, `CLUSTER_API_KEY`, `FALLBACK_API_KEY`, etc.) rather than hard-coded. Missing required variables raise a descriptive `ValueError` rather than proceeding with an empty key.

> **Guideline:** When adding new configuration surfaces, follow the same pattern — keep secrets out of any dict that might be logged, cached to disk, or sent over HTTP, and only include them when explicitly requested by a trusted, in-process caller.

## Input Validation and Sanitization

- **Repository path validation.** `validate_repository()` (`codewiki/cli/utils/repo_validator.py`) checks that a target path exists and contains files with supported extensions before any analysis begins, raising `RepositoryError` on failure rather than proceeding against an invalid or empty path.
- **GitHub URL validation.** `GitHubRepoProcessor.is_valid_github_url()` in Frontend Core validates submitted repository URLs before they are used to drive a `git clone`, reducing the risk of processing malformed or unexpected input from web form submissions.
- **Deprecated/removed CLI flags are rejected explicitly.** `_validate_no_deprecated_options()` in `codewiki/cli/commands/config.py` intercepts removed single-provider flags (`--base-url`, `--max-tokens`, etc.) and raises a `UsageError` with migration guidance, rather than silently ignoring or misapplying them.
- **Output path writability checks.** `check_writable_output()` validates that a destination directory exists (or can be created) and is writable before generation begins, avoiding partial or confusing failures mid-run.

## Authentication and Authorization Patterns

CodeWiki does not implement its own user authentication system. Authorization boundaries instead rely on:

- **LLM provider authentication** via per-provider API keys (cluster/main/fallback), validated at `Config` construction time.
- **Git provider authentication** via the operator's own git/SSH credentials (mounted read-only into the container in `docker/docker-compose.yml` as `~/.ssh:/root/.ssh:ro`) when cloning private repositories or pushing documentation branches.
- **GitHub PR creation** relies on the operator's existing push access to the target repository — `GitManager.get_github_pr_url()` only constructs a compare URL; it does not perform authenticated write operations itself beyond local git commits.

If you deploy the web application publicly, add your own authentication/authorization layer in front of it (e.g., a reverse proxy with auth) — the FastAPI app itself accepts repository submissions from any caller by default.

## Sandboxed Agent File Access

The documentation-generation agents (Backend Core's Agent Orchestration And Tools) are deliberately restricted:

- Agents can **read** arbitrary source files for context via controlled tools (`read_code_components`, `str_replace_editor`).
- Agents can only **write** within the documentation output tree — not into arbitrary repository paths — limiting the blast radius of unexpected LLM behavior.
- Generated Markdown is validated (including Mermaid diagram syntax) before a module is considered complete, catching malformed output before it's published.

## Common Vulnerabilities and Mitigations

| Risk | Mitigation in CodeWiki |
|---|---|
| Leaking LLM API keys via logs or cache | Secrets excluded from `Config.to_dict()` by default; stored in OS keyring, not plaintext config |
| Cloning/analyzing malicious or malformed repositories | `validate_repository()` and `GitHubRepoProcessor.is_valid_github_url()` validate input before cloning/analysis |
| Committing generated docs on a dirty working tree | `GitManager.create_documentation_branch()` refuses to proceed unless the working tree is clean, unless `force=True` |
| Agents writing outside the intended output directory | Agent editing tools are scoped to the documentation output tree only |
| Silent misuse of removed/legacy CLI options | Deprecated flags raise an explicit `UsageError` with migration instructions instead of being silently accepted |

## Environment Variables and Secrets Management Checklist

- Never commit `.env` files containing real API keys — use `.env` only for local development and keep it out of version control.
- Prefer `codewiki config set` (keyring-backed) over environment variables for interactive/local CLI usage.
- When running the web app via Docker Compose, pass secrets through `env_file: ../.env` rather than baking them into the image.
- Audit any new code path that calls `Config.to_dict(include_secrets=True)` — this should be limited to trusted, in-process transfers only.

## Security Testing and Code Review Guidelines

- When reviewing changes to `codewiki/src/config.py`, verify that new sensitive fields are added to `_RUNTIME_ONLY_SECRET_FIELDS` if they should never be persisted.
- When reviewing changes to repository/URL handling (`repo_validator.py`, `github_processor.py`), confirm new input is validated before being passed to `git` or filesystem operations.
- When reviewing changes to agent tools (`agent_tools/`), confirm file write access remains scoped to the documentation output directory.
- Prefer raising the project's existing typed errors (`ConfigurationError`, `RepositoryError`, `APIError`) over silent failures, so security-relevant failures are visible and testable.
