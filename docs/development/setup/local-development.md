# Local Development

This guide walks through cloning CodeWiki, installing it in editable mode, and running it locally against a test repository.

## Clone and Install

```bash
git clone https://github.com/flamingo-stack/CodeWiki.git
cd CodeWiki

# Editable install with development dependencies
pip install -e ".[dev]"
```

Editable installs (`-e`) mean changes to `codewiki/` source files take effect immediately without reinstalling — ideal for iterating on the CLI, backend pipeline, or web app.

Verify the CLI is on your `$PATH` and pointing at your local checkout:

```bash
codewiki --version
```

## Running the CLI Locally

Once installed, you can run `codewiki` against any repository (including CodeWiki's own repository, or one of the bundled test fixtures under `test-multi-path/`):

```bash
codewiki config set \
  --cluster-api-key "sk-..." --main-api-key "sk-..." \
  --cluster-model "your-model" --main-model "your-model" \
  --cluster-base-url "https://api.your-provider.com/v1" \
  --main-base-url "https://api.your-provider.com/v1"

cd /path/to/some/repo
codewiki generate --verbose
```

You can also invoke the CLI as a module without relying on the installed console script:

```bash
python -m codewiki --help
python -m codewiki generate
```

## Running the Web Application Locally

The FastAPI web app can be started directly with Python:

```bash
python codewiki/run_web_app.py
```

This inserts `codewiki/src` onto `sys.path` and delegates to `fe.web_app.main()`. By default it listens on `127.0.0.1:8000` (see `WebAppConfig.DEFAULT_HOST` / `DEFAULT_PORT` in `codewiki/src/fe/config.py`).

Alternatively, run it in a container using Docker Compose:

```bash
cd docker
docker compose up --build
```

The container maps port `8000` (overridable with the `APP_PORT` environment variable) and mounts `../output` for persistent cache/output storage, plus your `~/.ssh` directory (read-only) for cloning private repositories over SSH.

## Hot Reload / Iterating on Code

- **CLI changes**: Because the package is installed with `pip install -e .`, edits to any file under `codewiki/cli/` or `codewiki/src/` are picked up the next time you invoke `codewiki` — no reinstall needed.
- **Web app changes**: `run_web_app.py` does not enable an auto-reloading development server by default. If you need hot reload while iterating on FastAPI routes, restart `python codewiki/run_web_app.py` after each change, or run the underlying ASGI app through `uvicorn` with `--reload` if you invoke it that way directly.

## Debug Configuration

For debugging the CLI in an IDE (e.g., VS Code's Python debugger), set the program to run as a module with arguments, for example:

```bash
python -m codewiki generate --verbose
```

Configure your IDE's launch configuration to run `codewiki/cli/main.py` (or `python -m codewiki`) with the working directory set to the repository you want to analyze, and pass CLI arguments like `generate --verbose` for step-by-step output.

For debugging the web app, set breakpoints inside `codewiki/src/fe/routes.py` or `codewiki/src/fe/background_worker.py` and launch `codewiki/run_web_app.py` directly through your IDE's debugger rather than the CLI.

## Testing Your Changes Against Sample Fixtures

The repository includes a self-contained multi-path test fixture at `test-multi-path/` (with `main/`, `deps/`, `external/` subdirectories) specifically designed to exercise multi-root dependency analysis. Use it to sanity-check changes to the dependency analyzer without needing a large external repository:

```bash
python test-multi-path/test_multi_path.py
python test-multi-path/integration_test.py
```

See the [Testing](../testing/README.md) guide for more on how these and the clustering diagnostic scripts are organized.
