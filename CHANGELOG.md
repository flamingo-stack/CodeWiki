# Changelog

## Unreleased

### Breaking changes

- **`--additional-paths` and `additional_source_paths` are removed.** CodeWiki documents only the repository it
  runs in. Other repositories are read through the Flamingo hub's code-graph tools (`HUB_BASE_URL`,
  `WEBHOOK_SECRET`, `GITHUB_REPOSITORY`), never copied beside the checkout. Passing `--additional-paths` now stops
  with an error saying so; drop the option.

### Changes

- Agent models are called by their provider's own API: the OpenAI Responses API on `api.openai.com`, the native
  Anthropic API (with prompt caching) on `api.anthropic.com`, chat completions on any other host.
- Passing provider errors (dropped connections, rate limits, outages) are retried, by the SDK and then per module.
- Every component is placed in a module; clustering no longer leaves "non-essential" components undocumented.
- Copied libraries and minified builds are left out of what is documented (minified by form, a `/*!` library
  banner, vendored folders), and each run logs what it left out and why.
- Each run's model usage, per answering model and failed attempts included, is written to `CODEWIKI_USAGE_FILE`.
