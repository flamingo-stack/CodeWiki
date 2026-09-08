# Quick Start

This guide gets you from zero to a generated documentation set in about five minutes, using the `codewiki` CLI against a local repository.

> If you'd rather run CodeWiki as a hosted web service (submit a GitHub URL, poll for job status, view cached results), see the Docker-based setup mentioned at the end of this guide instead.

## Step 1: Install CodeWiki

Clone the repository and install the package (editable install is convenient for exploring the source):

```bash
git clone https://github.com/flamingo-stack/CodeWiki.git
cd CodeWiki
pip install -e .
```

This registers the `codewiki` console command, defined in `pyproject.toml` as:

```text
[project.scripts]
codewiki = "codewiki.cli.main:cli"
```

Verify the install:

```bash
codewiki --version
codewiki version
```

## Step 2: Configure Your LLM Credentials

CodeWiki needs API credentials for at least a **main model** and a **cluster model** (a fallback model is optional but recommended). Credentials are stored securely in your OS keyring; non-secret settings go to `~/.codewiki/config.json`.

```bash
codewiki config set \
  --cluster-api-key "sk-your-cluster-provider-key" \
  --main-api-key "sk-your-main-provider-key" \
  --cluster-model "your-cluster-model-name" \
  --main-model "your-main-model-name" \
  --cluster-base-url "https://api.your-provider.com/v1" \
  --main-base-url "https://api.your-provider.com/v1"
```

> **Note:** Replace the model names, base URLs, and API keys with values for your actual LLM provider. CodeWiki does not ship with default credentials — you must supply your own.

Confirm the configuration was saved and is complete:

```bash
codewiki config validate
```

## Step 3: Generate Documentation for a Repository

Navigate to any Git repository you want to document, then run:

```bash
cd /path/to/your/project
codewiki generate
```

By default, output is written to `./docs`. The CLI runs through four staged checks and then the documentation pipeline itself:

```text
Validating configuration...
Validating repository...
Analyzing dependencies...
Generating documentation...
```

## Expected Output

After a successful run, you should see a `docs/` directory in your project containing:

- Markdown files for each analyzed module (leaf modules first, then parent overview pages)
- A `module_tree.json` describing the hierarchical module structure
- A `metadata.json` describing job statistics and status

## Example: Verbose Run with Custom Output

```bash
codewiki generate --output ./generated-docs --verbose
```

Add `--verbose` any time you want detailed stage-by-stage progress and debug information printed to your terminal.

## Example: Generate a GitHub Pages Site

```bash
codewiki generate --github-pages --create-branch
```

This additionally renders a self-contained `index.html` viewer (from the generated `module_tree.json` and `metadata.json`) and creates a timestamped Git branch for the documentation changes, ready to push and open a pull request.

## Running the Web Application Instead

If you prefer the hosted web workflow (submit a GitHub repo URL through a browser, track job status, and view cached results), you can run the FastAPI app directly:

```bash
python codewiki/run_web_app.py
```

Or via Docker Compose:

```bash
cd docker
docker compose up --build
```

The web app listens on port `8000` by default (configurable via the `APP_PORT` environment variable read by `docker/docker-compose.yml`).

## Next Steps

Once you've generated your first documentation set, continue to [First Steps](first-steps.md) to learn about customizing what gets documented, exploring the CLI's other options, and where to find help.
