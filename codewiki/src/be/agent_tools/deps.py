"""Dependency container for CodeWiki agent tools.

Defines CodeWikiDeps, a dataclass holding the shared context and state
(paths, component registry, module tree position, configuration, etc.)
that is passed to agent tools during the CodeWiki documentation generation
pipeline.
"""
from dataclasses import dataclass
from typing import Any
from codewiki.src.be.dependency_analyzer.models.core import Node
from codewiki.src.config import Config

@dataclass
class CodeWikiDeps:
    absolute_docs_path: str
    absolute_repo_path: str
    registry: dict
    components: dict[str, Node]
    path_to_current_module: list[str]
    current_module_name: str
    module_tree: dict[str, Any]
    max_depth: int
    current_depth: int
    config: Config  # LLM configuration
    custom_instructions: str = None
