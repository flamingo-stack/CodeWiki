# First Steps

After completing the quick start, here are the first five things to explore in CodeWiki.

---

## 1. Explore the Generated Documentation Structure

After running `codewiki generate`, your output directory follows a deterministic structure:

```text
docs/
├── README.md                    ← Repository overview (auto-generated)
├── module_tree.json             ← Module hierarchy metadata
├── metadata.json                ← Generation audit metadata
└── <ModuleName>/
    ├── <ModuleName>.md          ← Module documentation
    └── <SubModule>/
        └── <SubModule>.md       ← Sub-module documentation
```

**Open `docs/README.md` first.** This is your entry point — it provides a high-level overview of the entire codebase as understood by the AI.

**Inspect `metadata.json`** to see what was generated:

```bash
cat docs/metadata.json
```

It contains:

- Generation timestamp
- Model used
- Repository path and commit ID
- Total components analyzed
- Leaf node count
- List of all generated Markdown files

---

## 2. Review and Refine Configuration

View your current configuration:

```bash
codewiki config show
```

Adjust token limits for large repositories (if generation was truncated or slow):

```bash
codewiki config set \
  --main-max-tokens 128000 \
  --cluster-max-tokens 128000 \
  --fallback-max-tokens 64000
```

Adjust the max documentation depth (default is 2):

```bash
codewiki config set --max-depth 3
```

> **Tip:** Higher depth means more granular module documentation but longer generation time.

---

## 3. Use File Filtering to Focus Documentation

CodeWiki supports include/exclude glob patterns to filter which files are analyzed. This is useful for focusing on the core logic while excluding tests, migrations, or generated code.

**Include only specific file types:**

```bash
codewiki generate --include "*.py,*.ts"
```

**Exclude test directories and generated files:**

```bash
codewiki generate --exclude "tests/,*_test.py,*.generated.*,migrations/"
```

**For a Java/Spring project:**

```bash
codewiki generate \
  --include "*.java" \
  --exclude "*Test.java,*Spec.java" \
  --doc-type architecture
```

**For a TypeScript project:**

```bash
codewiki generate \
  --include "*.ts" \
  --exclude "*.spec.ts,*.test.ts,node_modules/"
```

---

## 4. Generate GitHub Pages Documentation

CodeWiki can generate a static `index.html` viewer compatible with GitHub Pages.

```bash
codewiki generate --github-pages --create-branch
```

This will:

1. Generate all Markdown documentation
2. Create a timestamped Git branch (e.g., `docs/codewiki-20250101-120000`)
3. Generate `docs/index.html` — a fully static documentation viewer
4. Commit all files to the branch

Push the branch and open a PR:

```bash
git push origin docs/codewiki-20250101-120000
```

Then navigate to your repository's **Settings → Pages** and point it to the `docs/` folder on this branch.

---

## 5. Use the Web Interface for Team-Wide Access

The web interface lets any team member generate documentation by pasting a GitHub repository URL — no CLI required.

**Start the web app:**

```bash
python -m codewiki.run_web_app --port 8000
```

Or with auto-reload for development:

```bash
python -m codewiki.run_web_app --reload
```

**What the web interface does:**

- Accepts any public GitHub repository URL
- Queues documentation generation in a background worker
- Caches results (by default for several days) to avoid redundant generation
- Serves rendered Markdown as navigable HTML

**API endpoint to check job status:**

```bash
curl http://localhost:8000/api/job/{job_id}
```

---

## Common Initial Configuration Patterns

### Single LLM Provider (All Roles)

Configure all three roles to use the same provider and key:

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

### Mixed Providers (Cost Optimization)

Use a larger model for documentation and a smaller/cheaper model for clustering:

```bash
codewiki config set \
  --main-model claude-sonnet-4 \
  --main-api-key sk-ant-... \
  --main-base-url https://api.anthropic.com/v1 \
  --cluster-model gpt-4o-mini \
  --cluster-api-key sk-... \
  --cluster-base-url https://api.openai.com/v1 \
  --fallback-model gpt-4o-mini \
  --fallback-api-key sk-... \
  --fallback-base-url https://api.openai.com/v1
```

### Reasoning Models (o3, o3-mini)

Some reasoning models require `max_completion_tokens` instead of `max_tokens`:

```bash
codewiki config set \
  --main-model o3 \
  --main-max-token-field max_completion_tokens \
  --main-temperature-supported false
```

---

## Where to Get Help

CodeWiki is part of the OpenMSP open-source community:

- **OpenMSP Slack:** [Join the community](https://join.slack.com/t/openmsp/shared_invite/zt-36bl7mx0h-3~U2nFH6nqHqoTPXMaHEHA)
- **Community portal:** [openmsp.ai](https://www.openmsp.ai/)
- **Source code:** [github.com/flamingo-stack/CodeWiki](https://github.com/flamingo-stack/CodeWiki)
- **Flamingo Platform:** [flamingo.run](https://flamingo.run)
