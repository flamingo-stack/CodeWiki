"""Dependency-injection context for the CodeWiki agent tools pipeline.

Defines the CodeWikiDeps dataclass, which carries paths, registry data,
component metadata, and configuration through the agent tools pipeline.
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
