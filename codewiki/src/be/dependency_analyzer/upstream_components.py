"""The code this repository builds on, read from the Flamingo hub's code graph.

A service whose logic lives in a library it consumes (a Spring Boot entry point that assembles a library's
controllers, data layer and security) is documented together with that library code, the way it was when the
library was cloned beside it. Nothing is cloned: the hub's code graph says which artifacts this repository consumes
from other repositories and which definitions each holds, and serves their files at the commit it indexed.

- ``GET  {HUB_BASE_URL}/api/ci/code-documentation/upstream?github=<repo>`` answers ``producers`` (each upstream
  repository with its commit, the artifacts consumed and how many components) and ``own_imports`` (this repository's
  files, each with the upstream components it imports) and ``consumed_by`` (per artifact, this repository's modules
  that depend on it).
- ``GET  ...?github=<repo>&upstream=<owner/lib>&page=&pageSize=`` answers one page of that producer's components:
  symbol key, name, the kind the graph's tagger wrote, file, lines, and the components its file imports. The graph
  decides what a component is (a definition with a body that no other definition of its file encloses), so every
  one is a unit worth a page, whatever its kind.
- ``POST ...`` with ``{github, upstream, paths}`` answers the texts of up to 80 of its files.

Every component becomes a ``Node`` namespaced by the producer's repository name, its file written under a
temporary directory outside the checkout so the prompts read it like any other file. This repository's own
components gain the edges to what they import. Without hub settings, or when the hub cannot be read, nothing is
added and the repository is documented alone.
"""

from __future__ import annotations

import logging
import os
import tempfile
from typing import Dict, List, Optional

import httpx

from codewiki.src.be.agent_tools.code_graph import HubSettings, hub_error_message, read_hub_settings
from codewiki.src.be.dependency_analyzer.models.core import Node

logger = logging.getLogger(__name__)

UPSTREAM_PATH = "/api/ci/code-documentation/upstream"
PAGE_SIZE = 1000
FILES_PER_REQUEST = 80
TIMEOUT_SECONDS = 120.0

# Extensions stripped from a file path to form its module path, as the parser does for this repository's own files.
_SOURCE_EXTENSIONS = (".py", ".js", ".ts", ".java", ".cs", ".cpp", ".hpp", ".h", ".c", ".tsx", ".jsx", ".cc",
                      ".mjs", ".cxx", ".cjs", ".rs", ".go", ".kt", ".php")


class UpstreamUnavailable(Exception):
    """The hub could not answer; the run documents the repository alone and says why."""


def _module_path(file: str) -> str:
    path = file
    for ext in _SOURCE_EXTENSIONS:
        if path.endswith(ext):
            path = path[: -len(ext)]
            break
    return path.replace("/", ".")


def _get(client: httpx.Client, settings: HubSettings, params: Dict[str, object]) -> dict:
    response = client.get(f"{settings.base_url}{UPSTREAM_PATH}", params=params, headers=settings.headers)
    if response.status_code >= 400:
        raise UpstreamUnavailable(hub_error_message(response))
    return response.json()


def _post(client: httpx.Client, settings: HubSettings, body: dict) -> dict:
    response = client.post(f"{settings.base_url}{UPSTREAM_PATH}", json=body, headers=settings.headers)
    if response.status_code >= 400:
        raise UpstreamUnavailable(hub_error_message(response))
    return response.json()


def _slice(text: str, start: Optional[int], end: Optional[int]) -> str:
    if not start:
        return text
    lines = text.splitlines()
    return "\n".join(lines[start - 1 : (end or start)])


def load_upstream_components(own_components: Dict[str, Node], settings: Optional[HubSettings] = None) -> Dict[str, Node]:
    """The upstream components for this repository, keyed by their ids; ``own_components`` gain their import edges.

    Returns an empty dict when the hub is not configured or cannot be read (logged), never raises.
    """
    settings = settings or read_hub_settings()
    if not settings:
        return {}
    try:
        with httpx.Client(timeout=TIMEOUT_SECONDS) as client:
            return _load(client, settings, own_components)
    except (UpstreamUnavailable, httpx.HTTPError, ValueError) as error:
        logger.warning(f"Upstream components are off: the hub could not be read ({error})")
        return {}


def _load(client: httpx.Client, settings: HubSettings, own_components: Dict[str, Node]) -> Dict[str, Node]:
    plan = _get(client, settings, {"github": settings.repository})
    producers: List[dict] = plan.get("producers") or []
    consumed_by: Dict[str, List[str]] = plan.get("consumed_by") or {}
    if not producers:
        logger.info(f"Upstream components: {settings.repository} consumes nothing another managed repository publishes")
        return {}

    root = tempfile.mkdtemp(prefix="codewiki-upstream-", dir=os.environ.get("RUNNER_TEMP") or None)
    by_key: Dict[str, str] = {}
    pending: Dict[str, List[str]] = {}
    nodes: Dict[str, Node] = {}

    for producer in producers:
        github = producer["github"]
        repo_name = github.split("/")[-1]
        commit = producer["commit_sha"]
        rows: List[dict] = []
        page = 1
        while True:
            answer = _get(client, settings, {"github": settings.repository, "upstream": github, "page": page, "pageSize": PAGE_SIZE})
            rows.extend(answer.get("components") or [])
            if page * PAGE_SIZE >= int(answer.get("total") or 0) or not answer.get("components"):
                break
            page += 1

        texts = _read_files(client, settings, github, sorted({row["file"] for row in rows}), root, repo_name)
        for row in rows:
            text = texts.get(row["file"])
            if text is None:
                continue
            node_id = f"{repo_name}.{_module_path(row['file'])}::{row['name']}"
            if node_id in nodes:
                continue
            nodes[node_id] = Node(
                id=node_id,
                name=row["name"],
                component_type=row["kind"],
                file_path=os.path.join(root, repo_name, row["file"]),
                relative_path=f"{repo_name}/{row['file']}",
                source_code=_slice(text, row.get("start_line"), row.get("end_line")),
                start_line=row.get("start_line") or 0,
                end_line=row.get("end_line") or 0,
                node_type=row["kind"],
                display_name=row["name"],
                component_id=node_id,
                short_id=f"{_module_path(row['file'])}::{row['name']}",
                namespace=repo_name,
                source_url=f"https://github.com/{github}/blob/{commit}/{row['file']}",
                source_repository=github,
                source_artifact=row.get("artifact"),
                used_by=consumed_by.get(row.get("artifact") or "") or None,
            )
            by_key[row["symbol"]] = node_id
            pending[node_id] = row.get("depends_on") or []
        logger.info(
            f"Upstream components: {len(rows)} from {github} at {commit[:12]} "
            f"({', '.join(producer.get('artifacts') or [])}), {len(texts)} files read"
        )

    for node_id, keys in pending.items():
        nodes[node_id].depends_on = {by_key[k] for k in keys if k in by_key and by_key[k] != node_id}

    own_imports: Dict[str, List[str]] = plan.get("own_imports") or {}
    linked = 0
    for component in own_components.values():
        targets = {by_key[k] for k in own_imports.get(component.relative_path, []) if k in by_key}
        if targets:
            component.depends_on |= targets
            linked += 1
    logger.info(f"Upstream components: {len(nodes)} added, {linked} of this repository's components linked to them")
    return nodes


def _read_files(client: httpx.Client, settings: HubSettings, github: str, files: List[str], root: str, repo_name: str) -> Dict[str, str]:
    texts: Dict[str, str] = {}
    for i in range(0, len(files), FILES_PER_REQUEST):
        answer = _post(client, settings, {"github": settings.repository, "upstream": github, "paths": files[i : i + FILES_PER_REQUEST]})
        for entry in answer.get("files") or []:
            text = entry.get("text")
            if not isinstance(text, str):
                continue
            path = os.path.join(root, repo_name, entry["path"])
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(text)
            texts[entry["path"]] = text
    return texts
