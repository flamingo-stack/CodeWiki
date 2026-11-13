"""
What a CodeWiki run spent, per model, from the model's own answers.

Every agent run (the module writers) goes through a fallback model, so the model that answered is read
off each response (`ModelResponse.model_name`), never assumed from the configuration. The clustering
calls go through the OpenAI client directly and are recorded from that response's usage.

Totals are logged as they grow, and, when `CODEWIKI_USAGE_FILE` is set, merged into that file in the
Code Documentation workflow's usage format (`usage.by_model[model] = {input, output, cacheRead}`, plus a
`funnel.stage2` entry), which the workflow's final report sends to the hub. Input tokens exclude cache
reads, which are counted on their own, as the hub prices them.
"""

from __future__ import annotations

import json
import logging
import os
import threading
from typing import Any, Dict

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_by_model: Dict[str, Dict[str, int]] = {}
_runs = {"agent_runs": 0, "failed_attempts": 0, "requests": 0, "tool_calls": 0}


def _add(model: str, input_tokens: int, output_tokens: int, cache_read: int) -> None:
    entry = _by_model.setdefault(model or "unknown", {"input": 0, "output": 0, "cacheRead": 0})
    entry["input"] += max(0, int(input_tokens or 0))
    entry["output"] += max(0, int(output_tokens or 0))
    entry["cacheRead"] += max(0, int(cache_read or 0))


def record_agent_run(label: str, result: Any) -> None:
    """One finished agent run: each of its model responses, attributed to the model that answered it."""
    record_messages(label, result.all_messages())


async def run_and_record(agent: Any, label: str, *args: Any, **kwargs: Any) -> Any:
    """Run an agent and record what it spent, a run that fails included.

    A failed run's model responses (answered before the error) were billed too, so they are recorded before the
    error is raised: a run that is retried then counts every attempt.
    """
    from pydantic_ai import capture_run_messages

    with capture_run_messages() as messages:
        try:
            result = await agent.run(*args, **kwargs)
        except BaseException:
            record_messages(f"{label} (failed attempt)", messages, finished=False)
            raise
    record_agent_run(label, result)
    return result


def record_messages(label: str, messages: Any, finished: bool = True) -> None:
    """Each model response of one agent run, attributed to the model that answered it."""
    try:
        from pydantic_ai.messages import ModelResponse, ToolCallPart
    except ImportError:  # pragma: no cover - pydantic_ai is a dependency
        return
    run_tokens = {"input": 0, "output": 0, "cacheRead": 0, "requests": 0, "tool_calls": 0}
    with _lock:
        for message in messages:
            if not isinstance(message, ModelResponse):
                continue
            usage = message.usage
            cache_read = int(getattr(usage, "cache_read_tokens", 0) or 0)
            input_tokens = int(getattr(usage, "input_tokens", 0) or 0) - cache_read
            output_tokens = int(getattr(usage, "output_tokens", 0) or 0)
            _add(message.model_name or "unknown", input_tokens, output_tokens, cache_read)
            run_tokens["input"] += max(0, input_tokens)
            run_tokens["output"] += output_tokens
            run_tokens["cacheRead"] += cache_read
            run_tokens["requests"] += 1
            run_tokens["tool_calls"] += sum(1 for part in message.parts if isinstance(part, ToolCallPart))
        _runs["agent_runs" if finished else "failed_attempts"] += 1
        _runs["requests"] += run_tokens["requests"]
        _runs["tool_calls"] += run_tokens["tool_calls"]
    logger.info(
        f"💰 Usage {label}: {run_tokens['requests']} requests, {run_tokens['tool_calls']} tool calls, "
        f"{run_tokens['input']} input + {run_tokens['cacheRead']} cache-read + {run_tokens['output']} output tokens; "
        f"run total {json.dumps(_by_model, sort_keys=True)}"
    )
    _write()


def record_completion(model: str, response: Any) -> None:
    """One direct chat completion (clustering), from the OpenAI response's usage."""
    usage = getattr(response, "usage", None)
    if usage is None:
        return
    details = getattr(usage, "prompt_tokens_details", None)
    cache_read = int(getattr(details, "cached_tokens", 0) or 0) if details is not None else 0
    with _lock:
        _add(model, int(getattr(usage, "prompt_tokens", 0) or 0) - cache_read, int(getattr(usage, "completion_tokens", 0) or 0), cache_read)
        _runs["requests"] += 1
    logger.info(f"💰 Usage {model}: {getattr(usage, 'prompt_tokens', 0)} prompt + {getattr(usage, 'completion_tokens', 0)} completion tokens")
    _write()


def totals() -> Dict[str, Any]:
    with _lock:
        return {"by_model": json.loads(json.dumps(_by_model)), **_runs}


# What this process has already added to the file, per model: each write re-reads the file and replaces THIS
# share only, so an update another writer made in between is kept, never overwritten by a stale copy.
_written: Dict[str, Dict[str, int]] = {}


def _write() -> None:
    """Merge this run's totals into `CODEWIKI_USAGE_FILE` (the workflow's usage artifact), re-read on every write."""
    global _written
    path = os.environ.get("CODEWIKI_USAGE_FILE")
    if not path:
        return
    with _lock:
        try:
            with open(path, "r", encoding="utf-8") as handle:
                current = json.load(handle)
        except (OSError, ValueError):
            current = {}
        merged = {model: dict(values) for model, values in (current.get("usage", {}).get("by_model") or {}).items()}
        for model, values in _by_model.items():
            entry = merged.setdefault(model, {"input": 0, "output": 0, "cacheRead": 0})
            before = _written.get(model, {})
            for key in ("input", "output", "cacheRead"):
                entry[key] = max(0, entry.get(key, 0) - before.get(key, 0)) + values[key]
        funnel = dict(current.get("funnel") or {})
        funnel["stage2"] = {"engine": "codewiki", **_runs}
        tmp = f"{path}.{os.getpid()}.tmp"
        with open(tmp, "w", encoding="utf-8") as handle:
            json.dump({**current, "usage": {**(current.get("usage") or {}), "by_model": merged}, "funnel": funnel}, handle)
        os.replace(tmp, path)
        _written = {model: dict(values) for model, values in _by_model.items()}
