# First Steps

You've installed CodeWiki, configured your LLM credentials, and generated your first documentation set. Here's what to explore next.

## 1. Inspect and Confirm Your Configuration

Use `codewiki config show` to review everything CodeWiki currently knows about your setup — models, base URLs, token limits, temperature settings, and agent instructions. API keys are always masked (only the first/last few characters shown).

```bash
codewiki config show
codewiki config show --json
```

Use `codewiki config validate` any time you change providers or suspect something is misconfigured. It checks the config file, verifies all three API keys are present, validates base URL formats, confirms models are set, and (unless `--quick` is passed) performs a live connectivity test against each configured provider.

```bash
codewiki config validate
codewiki config validate --quick     # Skip live API connectivity test
codewiki config validate --verbose   # Step-by-step diagnostic output
```

## 2. Customize What Gets Documented

The `generate` command accepts several options that narrow or reshape the analysis without touching your saved configuration:

```bash
# Only analyze C# files, skip test projects
codewiki generate --include "*.cs" --exclude "*Tests*,*Specs*,test_*"

# Focus documentation on specific modules/paths
codewiki generate --focus "src/core,src/api" --doc-type architecture

# Add free-form custom instructions for the documentation agent
codewiki generate --instructions "Focus on public APIs and include usage examples"

# Include additional source directories (e.g., vendored dependencies)
codewiki generate --additional-paths "vendor/packages,external/deps"
```

If you want these choices to become your **default** behavior for every future run (rather than one-off flags), persist them with:

```bash
codewiki config agent --include "*.cs" --exclude "*Tests*,*Specs*"
codewiki config agent --doc-type architecture
codewiki config agent --instructions "Focus on public APIs and include usage examples"

# Clear all saved agent instructions
codewiki config agent --clear
```

`--doc-type` accepts one of: `api`, `architecture`, `user-guide`, or `developer`.

## 3. Tune Token Budgets and Depth for Large Repositories

If your repository is very large or the LLM response is being truncated, adjust token and depth limits either per-run or persistently:

```bash
# Per-run override
codewiki generate --max-tokens 32768 --max-token-per-module 40000 --max-token-per-leaf-module 20000 --max-depth 3

# Persist as defaults
codewiki config set --cluster-max-tokens 128000 --main-max-tokens 128000 \
  --max-token-per-module 40000 --max-token-per-leaf-module 20000 --max-depth 3
```

`--max-depth` controls how many levels of hierarchical module decomposition are produced (default: 2).

## 4. Explore the Git and GitHub Pages Workflow

If you're documenting a Git-tracked project, CodeWiki can create a dedicated branch for the generated docs and prepare a GitHub Pages-ready static site:

```bash
codewiki generate --create-branch --github-pages
```

`--create-branch` requires a clean working tree and creates a timestamped branch. `--github-pages` renders a self-contained `index.html` from the generated `module_tree.json` and `metadata.json`, suitable for publishing directly.

For CI/CD pipelines where you don't want interactive prompts, add `--force` to overwrite existing documentation without prompting, and `--no-cache` to force a full regeneration.

## 5. Explore the Generated Output Structure

After a run, look inside your output directory (default `./docs`) for:

- Individual Markdown files per analyzed module (leaves generated first, then parent overview pages)
- `module_tree.json` — the hierarchical module structure used for navigation
- `metadata.json` — job status and generation statistics
- `index.html` (only if `--github-pages` was used)

If you used `--diagrams-output`, Mermaid diagrams extracted from the generated Markdown are also saved separately as `.mmd` files.

## Where to Get Help

- Run `codewiki --help`, `codewiki generate --help`, or `codewiki config --help` / `codewiki config set --help` for full flag references directly in your terminal — these are the most up-to-date source of truth for available options.
- For questions, feedback, or community discussion, join the OpenMSP Slack community: [https://www.openmsp.ai/](https://www.openmsp.ai/) ([join link](https://join.slack.com/t/openmsp/shared_invite/zt-36bl7mx0h-3~U2nFH6nqHqoTPXMaHEHA)).
- If you plan to contribute code or documentation improvements back to CodeWiki itself, continue on to the development section of this documentation.
