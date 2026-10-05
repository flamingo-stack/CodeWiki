"""
Documentation job data models.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
import uuid
import json


class JobStatus(str, Enum):
    """Documentation job status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class GenerationOptions:
    """Options for documentation generation."""
    create_branch: bool = False
    github_pages: bool = False
    no_cache: bool = False
    custom_output: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "create_branch": self.create_branch,
            "github_pages": self.github_pages,
            "no_cache": self.no_cache,
            "custom_output": self.custom_output,
        }

    @classmethod
    def from_dict(cls, data: Any) -> 'GenerationOptions':
        """Create from dictionary."""
        if isinstance(data, cls):
            return data
        if not data:
            return cls()
        return cls(
            create_branch=bool(data.get('create_branch', False)),
            github_pages=bool(data.get('github_pages', False)),
            no_cache=bool(data.get('no_cache', False)),
            custom_output=data.get('custom_output'),
        )


@dataclass
class JobStatistics:
    """Statistics for a documentation job."""
    total_files_analyzed: int = 0
    leaf_nodes: int = 0
    max_depth: int = 0
    total_tokens_used: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "total_files_analyzed": self.total_files_analyzed,
            "leaf_nodes": self.leaf_nodes,
            "max_depth": self.max_depth,
            "total_tokens_used": self.total_tokens_used,
        }

    @classmethod
    def from_dict(cls, data: Any) -> 'JobStatistics':
        """Create from dictionary."""
        if isinstance(data, cls):
            return data
        if not data:
            return cls()
        return cls(
            total_files_analyzed=_coerce_int(data.get('total_files_analyzed'), 0),
            leaf_nodes=_coerce_int(data.get('leaf_nodes'), 0),
            max_depth=_coerce_int(data.get('max_depth'), 0),
            total_tokens_used=_coerce_int(data.get('total_tokens_used'), 0),
        )


@dataclass
class LLMRoleConfig:
    """Configuration for a single LLM role (cluster, main, or fallback)."""
    model: str = ""
    api_key: str = ""
    base_url: str = ""
    api_version: str = ""
    max_tokens: int = 0
    temperature: float = 0.0
    temperature_supported: bool = True
    max_token_field: str = "max_tokens"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "model": self.model,
            "api_key": self.api_key,
            "base_url": self.base_url,
            "api_version": self.api_version,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "temperature_supported": self.temperature_supported,
            "max_token_field": self.max_token_field,
        }

    @classmethod
    def from_dict(cls, data: Any) -> 'LLMRoleConfig':
        """Create from dictionary."""
        if isinstance(data, cls):
            return data
        if not data:
            return cls()
        return cls(
            model=data.get('model', ''),
            api_key=data.get('api_key', ''),
            base_url=data.get('base_url', ''),
            api_version=data.get('api_version', ''),
            max_tokens=_coerce_int(data.get('max_tokens'), 0),
            temperature=float(data.get('temperature', 0.0) or 0.0),
            temperature_supported=bool(data.get('temperature_supported', True)),
            max_token_field=data.get('max_token_field', 'max_tokens'),
        )


@dataclass
class LLMConfig:
    """LLM configuration for a job, mirroring the three-role (cluster, main, fallback) pattern."""
    cluster: LLMRoleConfig = field(default_factory=LLMRoleConfig)
    main: LLMRoleConfig = field(default_factory=LLMRoleConfig)
    fallback: LLMRoleConfig = field(default_factory=LLMRoleConfig)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "cluster": self.cluster.to_dict(),
            "main": self.main.to_dict(),
            "fallback": self.fallback.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Any) -> Optional['LLMConfig']:
        """Create from dictionary, or None if data is empty."""
        if isinstance(data, cls):
            return data
        if not data:
            return None
        return cls(
            cluster=LLMRoleConfig.from_dict(data.get('cluster')),
            main=LLMRoleConfig.from_dict(data.get('main')),
            fallback=LLMRoleConfig.from_dict(data.get('fallback')),
        )


def _coerce_job_status(value: Any, default: JobStatus = JobStatus.PENDING) -> JobStatus:
    """Coerce a raw value into a JobStatus, falling back to a default."""
    if isinstance(value, JobStatus):
        return value
    if value is None:
        return default
    try:
        return JobStatus(value)
    except ValueError:
        return default


def _coerce_int(value: Any, default: int = 0) -> int:
    """Coerce a raw value into an int, falling back to a default."""
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


@dataclass
class DocumentationJob:
    """
    Represents a documentation generation job.
    
    Attributes:
        job_id: Unique job identifier
        repository_path: Absolute path to repository
        repository_name: Repository name
        output_directory: Output directory path
        commit_hash: Git commit SHA
        branch_name: Git branch name (if applicable)
        timestamp_start: Job start time
        timestamp_end: Job end time (if completed)
        status: Current job status
        error_message: Error message (if failed)
        files_generated: List of generated files
        module_count: Number of modules documented
        generation_options: Generation options used
        llm_config: LLM configuration used
        statistics: Job statistics
    """
    job_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    repository_path: str = ""
    repository_name: str = ""
    output_directory: str = ""
    commit_hash: str = ""
    branch_name: Optional[str] = None
    timestamp_start: str = field(default_factory=lambda: datetime.now().isoformat())
    timestamp_end: Optional[str] = None
    status: JobStatus = JobStatus.PENDING
    error_message: Optional[str] = None
    files_generated: List[str] = field(default_factory=list)
    module_count: int = 0
    generation_options: GenerationOptions = field(default_factory=GenerationOptions)
    llm_config: Optional[LLMConfig] = None
    statistics: JobStatistics = field(default_factory=JobStatistics)
    
    def start(self):
        """Mark job as started."""
        self.status = JobStatus.RUNNING
        self.timestamp_start = datetime.now().isoformat()
    
    def complete(self):
        """Mark job as completed."""
        self.status = JobStatus.COMPLETED
        self.timestamp_end = datetime.now().isoformat()
    
    def fail(self, error_message: str):
        """Mark job as failed."""
        self.status = JobStatus.FAILED
        self.error_message = error_message
        self.timestamp_end = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = {
            "job_id": self.job_id,
            "repository_path": self.repository_path,
            "repository_name": self.repository_name,
            "output_directory": self.output_directory,
            "commit_hash": self.commit_hash,
            "branch_name": self.branch_name,
            "timestamp_start": self.timestamp_start,
            "timestamp_end": self.timestamp_end,
            "status": self.status.value if isinstance(self.status, JobStatus) else self.status,
            "error_message": self.error_message,
            "files_generated": self.files_generated,
            "module_count": self.module_count,
            "generation_options": self.generation_options.to_dict(),
            "llm_config": self.llm_config.to_dict() if self.llm_config else None,
            "statistics": self.statistics.to_dict(),
        }
        return data
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DocumentationJob':
        """Create from dictionary."""
        job = cls(
            job_id=data.get('job_id', str(uuid.uuid4())),
            repository_path=data.get('repository_path', ''),
            repository_name=data.get('repository_name', ''),
            output_directory=data.get('output_directory', ''),
            commit_hash=data.get('commit_hash', ''),
            branch_name=data.get('branch_name'),
            timestamp_start=data.get('timestamp_start', datetime.now().isoformat()),
            timestamp_end=data.get('timestamp_end'),
            status=_coerce_job_status(data.get('status'), JobStatus.PENDING),
            error_message=data.get('error_message'),
            files_generated=data.get('files_generated', []),
            module_count=_coerce_int(data.get('module_count'), 0),
        )
        
        # Parse nested objects
        if 'generation_options' in data:
            job.generation_options = GenerationOptions.from_dict(data['generation_options'])
        
        if 'llm_config' in data and data['llm_config']:
            job.llm_config = LLMConfig.from_dict(data['llm_config'])
        
        if 'statistics' in data:
            job.statistics = JobStatistics.from_dict(data['statistics'])
        
        return job


