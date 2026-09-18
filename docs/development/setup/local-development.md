# Local Development

This guide covers running CodeWiki's CLI and web application directly from source for development.

## Clone and Setup

```bash
git clone https://github.com/flamingo-stack/CodeWiki.git
cd CodeWiki

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

## Running the CLI Locally

The CLI can be invoked as a Python module without installing a package, via the `codewiki/__main__.py` entry point:

```bash
# Show CLI help
python -m codewiki --help

# Show version
python -m codewiki version

# Configure LLM providers
python -m codewiki config set --main-api-key "..." --main-model "claude-sonnet-4" \
  --cluster-api-key "..." --cluster-model "claude-sonnet-4" \
  --fallback-api-key "..." --fallback-model "claude-sonnet-4"

# Run generation against a target repository
cd /path/to/target/repo
python -m /path/to/CodeWiki generate --verbose
```

> `codewiki/cli/main.py` is built with [Click](https://click.palletsprojects.com/). The root command group registers the `generate` and `config` subcommands and handles `KeyboardInterrupt` (exit code `130`) and unexpected exceptions (exit code `1`) with clean, colorized error output.

## Running the Web Application Locally

The FastAPI web app can be started directly with `run_web_app.py`, which forwards to `codewiki/src/fe/web_app.py`:

```bash
python codewiki/run_web_app.py --host 0.0.0.0 --port 8080
```

### Hot Reload / Watch Mode

The web app supports `uvicorn`'s auto-reload for development:

```bash
python -m fe.web_app --host 0.0.0.0 --port 8080 --reload --debug
```

With `--reload` enabled, the server restarts automatically whenever source files change, and `--debug` increases log verbosity — both useful while iterating on route handlers, background job processing, or caching logic.

## Running via Docker Compose (Optional)

To exercise the same environment used in production:

```bash
docker network create codewiki-network
docker compose -f docker/docker-compose.yml up -d --build
```

This builds the image from `docker/Dockerfile` (Python 3.12 slim, with `git`, `curl`, `nodejs`, and `npm` installed), mounts `../output` for persistent cache/output storage, and exposes the app on `${APP_PORT:-8000}`.

## Debug Configuration

- **CLI debugging**: Pass `--verbose` to `codewiki generate` where supported to surface debug-level log output from `CLILogger`. Third-party HTTP client loggers (`httpx`, `openai`, `anthropic`) are quieted to `WARNING` by default via `quiet_third_party_loggers()` to keep output readable; this only changes when the CLI logger is created in verbose mode.
- **Web app debugging**: Use `--debug` with `python -m fe.web_app` to increase log verbosity, and `--reload` to avoid restarting the server manually after each code change.
- **IDE debugging**: Both entry points (`codewiki/cli/main.py` and `codewiki/src/fe/web_app.py`) are plain Python callables and can be attached to directly from VS Code or PyCharm's debugger by setting the module/script path and passing the same CLI arguments shown above.

## Working Directory Notes

- CLI generation runs (`codewiki generate`) operate against the **current working directory** as the target repository — `cd` into the repository you want to document before running the command.
- Web app generation runs clone the submitted GitHub URL into a temporary directory managed by `BackgroundWorker` and `GitHubRepoProcessor` — you do not need to manually clone target repositories when using the web flow.
