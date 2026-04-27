"""universal-ctags wrapper.

Generates a JSON tags file once per (repo, commit) and queries it in-memory.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import threading
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from .git_utils import cache_key
from .languages import CTAGS_LANGUAGE


def _find_ctags_binary() -> str:
    for candidate in ("/opt/homebrew/bin/ctags", "/usr/local/bin/ctags"):
        if shutil.which(candidate):
            return candidate
    return "ctags"


class CtagsError(RuntimeError):
    pass


@dataclass
class TagEntry:
    name: str
    path: str  # relative to project root
    line: int
    kind: str
    language: str | None = None
    signature: str | None = None
    scope: str | None = None
    scope_kind: str | None = None
    pattern: str | None = None  # raw search pattern from ctags


@dataclass
class CtagsIndex:
    """In-memory index built from a ctags JSON output file."""

    by_name: dict[str, list[TagEntry]] = field(default_factory=lambda: defaultdict(list))
    by_file: dict[str, list[TagEntry]] = field(default_factory=lambda: defaultdict(list))
    all_tags: list[TagEntry] = field(default_factory=list)

    def lookup(self, name: str) -> list[TagEntry]:
        return list(self.by_name.get(name, []))

    def in_file(self, file_path: str) -> list[TagEntry]:
        return list(self.by_file.get(file_path, []))


# Cache: (repo_root_str, cache_key) -> CtagsIndex
_INDEX_CACHE: dict[tuple[str, str], CtagsIndex] = {}
_CACHE_LOCK = threading.Lock()


def get_index(project_root: Path, cache_dir: Path) -> CtagsIndex:
    """Get (and lazily build) the ctags index for the current commit."""
    key = (str(project_root), cache_key(project_root))
    with _CACHE_LOCK:
        cached = _INDEX_CACHE.get(key)
        if cached is not None:
            return cached

    tags_file = cache_dir / "tags" / f"{key[1]}-{abs(hash(key[0]))}.json"
    tags_file.parent.mkdir(parents=True, exist_ok=True)

    if not tags_file.exists():
        _build_tags(project_root, tags_file)

    index = _load_index(tags_file, project_root)
    with _CACHE_LOCK:
        _INDEX_CACHE[key] = index
    return index


_EXCLUDE_DIRS = [
    ".git", ".svn", ".hg",
    "node_modules", "vendor", "build", "dist", "target",
    ".gradle", ".idea", ".vscode", "__pycache__",
    ".venv", "venv", ".env", "env",
    ".tox", ".mypy_cache", ".pytest_cache", ".ruff_cache",
]


def _build_tags(project_root: Path, output_file: Path) -> None:
    """Run ctags over the project, restricted to supported languages."""
    languages = ",".join(sorted(set(CTAGS_LANGUAGE.values())))
    cmd = [
        _find_ctags_binary(),
        "--output-format=json",
        "--fields=+nKszSlF",
        "--extras=+q",
        f"--languages={languages}",
        "-R",
        "-f", str(output_file),
    ]
    for d in _EXCLUDE_DIRS:
        cmd.append(f"--exclude={d}")
    cmd.append(str(project_root))
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            timeout=300,
        )
    except FileNotFoundError as e:
        raise CtagsError(
            "universal-ctags is not installed. Install via "
            "`brew install universal-ctags` or `apt-get install universal-ctags`."
        ) from e
    except subprocess.TimeoutExpired as e:
        raise CtagsError("ctags indexing timed out after 5 minutes") from e

    if proc.returncode != 0:
        raise CtagsError(
            f"ctags failed (exit {proc.returncode}): {proc.stderr.strip()[:500]}"
        )

    # ctags writes warnings to stderr; surface them but don't fail
    if proc.stderr:
        print(f"[ctags] {proc.stderr.strip()[:300]}", file=sys.stderr)


def _load_index(tags_file: Path, project_root: Path) -> CtagsIndex:
    index = CtagsIndex()
    with tags_file.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("!"):
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if entry.get("_type") != "tag":
                continue

            raw_path = entry.get("path", "")
            try:
                rel_path = str(Path(raw_path).resolve().relative_to(project_root))
            except ValueError:
                rel_path = raw_path

            tag = TagEntry(
                name=entry.get("name", ""),
                path=rel_path,
                line=int(entry.get("line", 0) or 0),
                kind=entry.get("kind", ""),
                language=entry.get("language"),
                signature=entry.get("signature"),
                scope=entry.get("scope"),
                scope_kind=entry.get("scopeKind"),
                pattern=entry.get("pattern"),
            )
            index.by_name[tag.name].append(tag)
            index.by_file[tag.path].append(tag)
            index.all_tags.append(tag)
    return index
