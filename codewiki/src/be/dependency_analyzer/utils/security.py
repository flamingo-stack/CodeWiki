"""Security utilities for safe file access within a repository root.

This module implements path-traversal and symlink protections used when
reading files from a repository. It ensures that file access is confined to
a given base directory and that symlinks are not followed, mitigating
directory-traversal and symlink-escape attacks during dependency analysis.
"""

from pathlib import Path
import os

def _inside(base: Path, target: Path) -> bool:
    base_r = base.resolve()
    try:
        target_r = target.resolve()
        return target_r.is_relative_to(base_r)  # py>=3.9
    except AttributeError:
        return str(target.resolve()).startswith(str(base_r))

def assert_safe_path(base_dir: Path, target: Path):
    # Block symlinks (file or dir)
    if target.is_symlink():
        raise PermissionError(f"Symlink blocked: {target}")
    # Block paths that escape repo
    if not _inside(base_dir, target):
        raise PermissionError(f"Path escapes repo: {target} -> {target.resolve()}")

def safe_open_text(base_dir: Path, target: Path, encoding="utf-8"):
    assert_safe_path(base_dir, target)
    if not hasattr(os, "O_NOFOLLOW"):
        raise PermissionError(
            f"Cannot safely open {target}: platform does not support O_NOFOLLOW"
        )
    flags = os.O_RDONLY | os.O_NOFOLLOW
    fd = os.open(str(target), flags)
    try:
        # Re-verify post-open that the opened file descriptor is not a
        # symlink and still resolves inside base_dir, closing the TOCTOU
        # window between the pre-open check and the open() call.
        st = os.fstat(fd)
        import stat as _stat
        if _stat.S_ISLNK(st.st_mode):
            raise PermissionError(f"Symlink blocked: {target}")
        assert_safe_path(base_dir, target)
        with os.fdopen(fd, "r", encoding=encoding, errors="replace") as f:
            return f.read()
    finally:
        try:
            os.close(fd)
        except OSError:
            pass

