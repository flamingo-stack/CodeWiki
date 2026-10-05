"""
Analysis result models for the dependency analyzer.

Defines the Pydantic models used to represent the outcome of analyzing a
repository (functions, call relationships, file tree, and summary data) as
well as the NodeSelection model used for partial export of selected nodes.
These models are the primary data contract passed from the dependency
analysis stage to downstream documentation-generation and export stages.
"""

from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from codewiki.src.be.dependency_analyzer.models.core import Node, CallRelationship, Repository


class AnalysisResult(BaseModel):
    """Result of analyzing a repository"""

    repository: Repository
    functions: List[Node]
    relationships: List[CallRelationship]
    file_tree: Dict[str, Any]
    summary: Dict[str, Any]
    visualization: Dict[str, Any] = {}
    readme_content: Optional[str] = None


class NodeSelection(BaseModel):
    """Selected nodes for partial export"""

    selected_nodes: List[str] = []
    include_relationships: bool = True
    custom_names: Dict[str, str] = {}
