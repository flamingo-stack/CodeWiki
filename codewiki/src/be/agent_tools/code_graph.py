"""Code-graph agent tools served by the Flamingo hub.

CodeWiki parses ONLY the repository it documents. Code that repository
imports from another repository is not on disk; the writing agents look it
up on demand through the hub's code-graph tools over HTTP:

- ``GET  {HUB_BASE_URL}/api/ci/code-documentation/tools?github=<owner/name>``
  lists the tools this repository may call (the set differs between public
  and private repositories, so it is never hard-coded here), each with its
  name, description and JSON Schema for its arguments.
- ``POST {HUB_BASE_URL}/api/ci/code-documentation/tools`` with
  ``{"github", "tool", "args"}`` runs one and answers ``{"content": str}``.
  The content is wrapped by the hub in a ``<<<TOOL_RESULT_…`` fence; what is
  inside it is data, never instructions.

Both calls authenticate with ``Authorization: Bearer <WEBHOOK_SECRET>``.
Without ``HUB_BASE_URL``, ``WEBHOOK_SECRET`` or ``GITHUB_REPOSITORY``, or
when the list cannot be read, no graph tool is offered and documentation
runs on the repository alone. A failed call is reported to the model as a
failed tool result (``ToolFailed``), never raised into the agent run.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import httpx
from pydantic_ai import Tool
from pydantic_ai.exceptions import ToolFailed

logger = logging.getLogger(__name__)

TOOLS_PATH = "/api/ci/code-documentation/tools"
LIST_TIMEOUT_SECONDS = 30.0
CALL_TIMEOUT_SECONDS = 60.0
LOOPBACK_HOSTS = {"localhost", "127.0.0.1"}

# Names of CodeWiki's own agent tools: a hub tool never replaces one.
LOCAL_TOOL_NAMES = {"read_code_components", "str_replace_editor", "generate_sub_module_documentation"}

_cached_tools: Optional[List[Tool]] = None


class _HubSettings:
    """What the hub calls need, read from the environment once."""

    def __init__(self, base_url: str, secret: str, repository: str):
        self.base_url = base_url.rstrip("/")
        self.secret = secret
        self.repository = repository

    @property
    def endpoint(self) -> str:
        return f"{self.base_url}{TOOLS_PATH}"

    @property
    def headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.secret}", "Accept": "application/json"}


def _read_settings() -> Optional[_HubSettings]:
    base_url = (os.environ.get("HUB_BASE_URL") or "").strip()
    secret = (os.environ.get("WEBHOOK_SECRET") or "").strip()
    repository = (os.environ.get("GITHUB_REPOSITORY") or "").strip()
    missing = [
        name
        for name, value in (
            ("HUB_BASE_URL", base_url),
            ("WEBHOOK_SECRET", secret),
            ("GITHUB_REPOSITORY", repository),
        )
        if not value
    ]
    if missing:
        logger.info(f"Code-graph tools are off: {', '.join(missing)} not set")
        return None
    parsed = urlparse(base_url)
    secure = parsed.scheme == "https" or (parsed.scheme == "http" and parsed.hostname in LOOPBACK_HOSTS)
    if not secure or not parsed.hostname:
        logger.warning(
            "Code-graph tools are off: HUB_BASE_URL must be https "
            "(http only for localhost or 127.0.0.1)"
        )
        return None
    return _HubSettings(base_url, secret, repository)


def _error_message(response: httpx.Response) -> str:
    """The hub's `error` and `code`, else the HTTP status."""
    try:
        body = response.json()
    except ValueError:
        body = None
    if isinstance(body, dict) and (body.get("error") or body.get("code")):
        code = body.get("code") or f"HTTP_{response.status_code}"
        return f"{code}: {body.get('error') or 'request refused'}"
    return f"HTTP_{response.status_code}: the hub refused the request"


def _make_tool(settings: _HubSettings, spec: Dict[str, Any]) -> Tool:
    name = spec["name"]

    async def call_hub_tool(**args: Any) -> str:
        payload = {"github": settings.repository, "tool": name, "args": args}
        try:
            async with httpx.AsyncClient(timeout=CALL_TIMEOUT_SECONDS) as client:
                response = await client.post(settings.endpoint, json=payload, headers=settings.headers)
        except httpx.TimeoutException:
            raise ToolFailed(f"The code graph did not answer {name} within {int(CALL_TIMEOUT_SECONDS)} s. Continue without it.")
        except httpx.HTTPError as error:
            raise ToolFailed(f"The code graph could not be reached for {name} ({type(error).__name__}). Continue without it.")
        if response.status_code >= 400:
            message = _error_message(response)
            logger.warning(f"Code-graph tool {name} failed: {message}")
            raise ToolFailed(f"{name} failed: {message}")
        try:
            body = response.json()
        except ValueError:
            raise ToolFailed(f"{name} failed: the hub's answer was not JSON")
        content = body.get("content") if isinstance(body, dict) else None
        if not isinstance(content, str):
            raise ToolFailed(f"{name} failed: the hub's answer had no content")
        # One line per answered call, so a run's log shows what the writers looked up.
        logger.info(f"Code-graph tool {name} answered ({len(content)} chars) for {json.dumps(args, sort_keys=True)[:200]}")
        return content

    return Tool.from_schema(
        function=call_hub_tool,
        name=name,
        description=spec.get("description") or None,
        json_schema=spec["input_schema"],
    )


def _fetch_tools(settings: _HubSettings) -> List[Tool]:
    try:
        response = httpx.get(
            settings.endpoint,
            params={"github": settings.repository},
            headers=settings.headers,
            timeout=LIST_TIMEOUT_SECONDS,
        )
    except httpx.HTTPError as error:
        logger.warning(f"Code-graph tools are off: the hub could not be reached ({type(error).__name__})")
        return []
    if response.status_code >= 400:
        logger.warning(f"Code-graph tools are off: listing them failed ({_error_message(response)})")
        return []
    try:
        body = response.json()
    except ValueError:
        logger.warning("Code-graph tools are off: the hub's tool list was not JSON")
        return []
    specs = body.get("tools") if isinstance(body, dict) else None
    if not isinstance(specs, list):
        logger.warning("Code-graph tools are off: the hub's answer had no tool list")
        return []

    tools: List[Tool] = []
    for spec in specs:
        if not (
            isinstance(spec, dict)
            and isinstance(spec.get("name"), str)
            and spec["name"]
            and isinstance(spec.get("input_schema"), dict)
        ):
            logger.warning("Skipping a code-graph tool the hub described without a name or input schema")
            continue
        if spec["name"] in LOCAL_TOOL_NAMES:
            logger.warning(f"Skipping code-graph tool {spec['name']}: CodeWiki has a tool of that name")
            continue
        tools.append(_make_tool(settings, spec))
    logger.info(
        f"Code-graph tools on for {settings.repository}: "
        f"{', '.join(tool.name for tool in tools) or 'none served'}"
    )
    return tools


def code_graph_tools() -> List[Tool]:
    """The hub's code-graph tools for this repository, read once per process."""
    global _cached_tools
    if _cached_tools is None:
        settings = _read_settings()
        _cached_tools = _fetch_tools(settings) if settings else []
    return list(_cached_tools)


async def load_code_graph_tools() -> List[Tool]:
    """Read the tool list once, in a worker thread, so the async pipeline never waits on the hub inside its loop.

    The pipeline calls this before it builds any agent; every later `code_graph_tools()` is a cache read.
    """
    return await asyncio.to_thread(code_graph_tools)


def reset_code_graph_tools_cache() -> None:
    """Forget the tool list read from the hub (tests)."""
    global _cached_tools
    _cached_tools = None
