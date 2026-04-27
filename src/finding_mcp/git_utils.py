"""Git helpers for commit-keyed caching.

Every response embeds a commit hash so the LLM can correlate findings across calls.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


def get_head_commit(repo_root: Path) -> str | None:
    """Return the HEAD commit hash, or None if not a git repo."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
        if result.returncode != 0:
            return None
        return result.stdout.strip() or None
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None


def is_working_tree_dirty(repo_root: Path) -> bool:
    """Detect uncommitted changes."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
        if result.returncode != 0:
            return False
        return bool(result.stdout.strip())
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def cache_key(repo_root: Path) -> str:
    """Cache key for indexing. Falls back to a working-tree marker if dirty
    or not a git repo. Callers should treat the dirty key as transient.
    """
    commit = get_head_commit(repo_root)
    if commit and not is_working_tree_dirty(repo_root):
        return commit
    return f"WORKTREE-{repo_root.name}"
