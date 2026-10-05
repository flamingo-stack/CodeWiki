#!/usr/bin/env python3
"""
Data models and classes for the CodeWiki web application.

This module defines the data types that flow through the CodeWiki
documentation-generation pipeline:

- RepositorySubmission: the pydantic request model accepted by the API
  when a user submits a repository URL to be documented.
- JobStatusResponse: the pydantic response model returned by the API
  when reporting the status of a documentation generation job.
- JobStatus: the dataclass used internally by the background worker to
  track the lifecycle of a documentation generation job (queued ->
  processing -> completed/failed), and which is serialized at the
  boundary between the background worker, the API layer, and the cache.
- CacheEntry: the dataclass representing a cached documentation result,
  persisted and read back by the cache manager.

JobStatus and CacheEntry provide explicit to_dict()/from_dict()
serialization helpers so that all boundary crossings (background worker
-> API response -> cache) go through a single, type-safe conversion
point rather than ad-hoc dict construction elsewhere in the codebase.
"""

from datetime import datetime
from typing import Optional, Any, Dict
from dataclasses import dataclass, asdict


def _coerce_datetime(value: Any) -> Optional[datetime]:
    """Coerce a value into a datetime instance, or None."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value)
    raise TypeError(f"Cannot coerce value of type {type(value)!r} to datetime")


def _datetime_to_iso(value: Optional[datetime]) -> Optional[str]:
    """Convert a datetime (or None) into its ISO 8601 string representation."""
    if value is None:
        return None
    return value.isoformat()


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
        """Serialize this JobStatus to a plain dict with ISO-formatted datetimes."""
        data = asdict(self)
        data["created_at"] = _datetime_to_iso(self.created_at)
        data["started_at"] = _datetime_to_iso(self.started_at)
        data["completed_at"] = _datetime_to_iso(self.completed_at)
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "JobStatus":
        """Deserialize a JobStatus from a plain dict, coercing datetime fields."""
        return cls(
            job_id=data["job_id"],
            repo_url=data["repo_url"],
            status=data["status"],
            created_at=_coerce_datetime(data["created_at"]),
            started_at=_coerce_datetime(data.get("started_at")),
            completed_at=_coerce_datetime(data.get("completed_at")),
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
        """Serialize this CacheEntry to a plain dict with ISO-formatted datetimes."""
        return {
            "repo_url": self.repo_url,
            "repo_url_hash": self.repo_url_hash,
            "docs_path": self.docs_path,
            "created_at": _datetime_to_iso(self.created_at),
            "last_accessed": _datetime_to_iso(self.last_accessed),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CacheEntry":
        """Deserialize a CacheEntry from a plain dict, coercing datetime fields."""
        return cls(
            repo_url=data["repo_url"],
            repo_url_hash=data["repo_url_hash"],
            docs_path=data["docs_path"],
            created_at=_coerce_datetime(data["created_at"]),
            last_accessed=_coerce_datetime(data["last_accessed"]),
        )
