#!/usr/bin/env python3
"""
Data models and classes for the CodeWiki web application.
"""

from datetime import datetime
from typing import Optional, Any, Dict
from dataclasses import dataclass
from pydantic import BaseModel, HttpUrl


class RepositorySubmission(BaseModel):
    """Pydantic model for repository submission form."""
    repo_url: HttpUrl


class JobStatusResponse(BaseModel):
    """Pydantic model for job status API response."""
    job_id: str
    repo_url: str
    status: str
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    progress: str = ""
    docs_path: Optional[str] = None
    main_model: Optional[str] = None
    commit_id: Optional[str] = None


@dataclass
class JobStatus:
    """Tracks the status of a documentation generation job."""
    job_id: str
    repo_url: str
    status: str  # 'queued', 'processing', 'completed', 'failed'
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    progress: str = ""
    docs_path: Optional[str] = None
    main_model: Optional[str] = None
    commit_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize this JobStatus to a plain dict."""
        return {
            "job_id": self.job_id,
            "repo_url": self.repo_url,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_message": self.error_message,
            "progress": self.progress,
            "docs_path": self.docs_path,
            "main_model": self.main_model,
            "commit_id": self.commit_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "JobStatus":
        """Deserialize a JobStatus from a plain dict."""
        created_at = data.get("created_at")
        started_at = data.get("started_at")
        completed_at = data.get("completed_at")
        return cls(
            job_id=data["job_id"],
            repo_url=data["repo_url"],
            status=data["status"],
            created_at=datetime.fromisoformat(created_at) if isinstance(created_at, str) else created_at,
            started_at=datetime.fromisoformat(started_at) if isinstance(started_at, str) else started_at,
            completed_at=datetime.fromisoformat(completed_at) if isinstance(completed_at, str) else completed_at,
            error_message=data.get("error_message"),
            progress=data.get("progress", ""),
            docs_path=data.get("docs_path"),
            main_model=data.get("main_model"),
            commit_id=data.get("commit_id"),
        )


@dataclass
class CacheEntry:
    """Represents a cached documentation result."""
    repo_url: str
    repo_url_hash: str
    docs_path: str
    created_at: datetime
    last_accessed: datetime

    def to_dict(self) -> Dict[str, Any]:
        """Serialize this CacheEntry to a plain dict."""
        return {
            "repo_url": self.repo_url,
            "repo_url_hash": self.repo_url_hash,
            "docs_path": self.docs_path,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CacheEntry":
        """Deserialize a CacheEntry from a plain dict."""
        created_at = data.get("created_at")
        last_accessed = data.get("last_accessed")
        return cls(
            repo_url=data["repo_url"],
            repo_url_hash=data["repo_url_hash"],
            docs_path=data["docs_path"],
            created_at=datetime.fromisoformat(created_at) if isinstance(created_at, str) else created_at,
            last_accessed=datetime.fromisoformat(last_accessed) if isinstance(last_accessed, str) else last_accessed,
        )
