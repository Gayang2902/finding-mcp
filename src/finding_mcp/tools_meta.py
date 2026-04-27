"""Meta tools — file listing, file reading, repository info, project structure."""

from __future__ import annotations

import fnmatch
from collections import Counter
from pathlib import Path

from .config import Settings
from .git_utils import cache_key, get_head_commit, is_working_tree_dirty
from .languages import detect_language
from .models import FileEntry, PaginatedResponse, RepoInfo

SKIP_DIR_NAMES = {
    ".git", ".svn", ".hg",
    "node_modules", "vendor", "build", "dist", "target",
    ".gradle", ".idea", ".vscode", "__pycache__",
    ".venv", "venv", ".env", "env",
    ".tox", ".mypy_cache", ".pytest_cache", ".ruff_cache",
}


def _iter_files(project_root: Path):
    """Yield Path objects for all files, skipping noise directories."""
    for path in project_root.rglob("*"):
        # Skip directories with noise names anywhere in the path
        if any(part in SKIP_DIR_NAMES for part in path.parts):
            continue
        if path.is_file():
            yield path


def list_files(
    settings: Settings,
    glob: str | None = None,
    limit: int = 200,
) -> PaginatedResponse:
    if limit > settings.max_limit:
        limit = settings.max_limit

    matches: list[FileEntry] = []
    truncated = False
    for path in _iter_files(settings.project_root):
        rel = str(path.relative_to(settings.project_root))
        if glob and not fnmatch.fnmatch(rel, glob):
            continue
        try:
            size = path.stat().st_size
        except OSError:
            continue
        matches.append(
            FileEntry(
                path=rel,
                size_bytes=size,
                language=detect_language(rel),
            )
        )
        if len(matches) > limit:
            truncated = True
            break

    return PaginatedResponse(
        items=[m.model_dump() for m in matches[:limit]],
        truncated=truncated,
    )


def get_file(
    settings: Settings,
    file_path: str,
    line_start: int | None = None,
    line_end: int | None = None,
    line: int | None = None,
    before: int = 40,
    after: int = 40,
) -> dict:
    abs_path = (settings.project_root / file_path).resolve()
    try:
        abs_path.relative_to(settings.project_root)
    except ValueError as e:
        raise ValueError(f"file_path must be inside project root: {file_path}") from e
    if not abs_path.is_file():
        raise FileNotFoundError(f"File not found: {file_path}")

    text = abs_path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    total_lines = len(lines)

    if line is not None:
        if line_start is not None or line_end is not None:
            raise ValueError("Cannot combine 'line' with 'line_start'/'line_end'")
        line_start = max(1, line - before)
        line_end = min(total_lines, line + after)

    if line_start is None and line_end is None:
        # Whole file — but cap by max_response_bytes
        if len(text.encode("utf-8")) > settings.max_response_bytes:
            # Return first N lines roughly fitting the budget
            cutoff_bytes = 0
            cut_at = total_lines
            for i, ln in enumerate(lines):
                cutoff_bytes += len(ln.encode("utf-8")) + 1
                if cutoff_bytes > settings.max_response_bytes:
                    cut_at = i
                    break
            return {
                "file_path": file_path,
                "line_start": 1,
                "line_end": cut_at,
                "total_lines": total_lines,
                "content": "\n".join(lines[:cut_at]),
                "truncated": True,
            }
        return {
            "file_path": file_path,
            "line_start": 1,
            "line_end": total_lines,
            "total_lines": total_lines,
            "content": text,
            "truncated": False,
        }

    start = max(1, line_start or 1)
    end = min(total_lines, line_end or total_lines)
    if start > end:
        raise ValueError(f"Invalid range: line_start={start} > line_end={end}")

    selected = "\n".join(lines[start - 1 : end])
    truncated = False
    if len(selected.encode("utf-8")) > settings.max_response_bytes:
        # Truncate to budget
        cutoff_bytes = 0
        cut_at = end
        for i in range(start - 1, end):
            cutoff_bytes += len(lines[i].encode("utf-8")) + 1
            if cutoff_bytes > settings.max_response_bytes:
                cut_at = i
                break
        selected = "\n".join(lines[start - 1 : cut_at])
        end = cut_at
        truncated = True

    return {
        "file_path": file_path,
        "line_start": start,
        "line_end": end,
        "total_lines": total_lines,
        "content": selected,
        "truncated": truncated,
    }


def get_repo_info(settings: Settings) -> RepoInfo:
    counter: Counter[str] = Counter()
    total = 0
    for path in _iter_files(settings.project_root):
        total += 1
        lang = detect_language(path)
        if lang:
            counter[lang] += 1

    return RepoInfo(
        project_root=str(settings.project_root),
        commit_hash=get_head_commit(settings.project_root),
        is_dirty=is_working_tree_dirty(settings.project_root),
        languages=dict(counter),
        total_files=total,
    )


def get_project_structure(
    settings: Settings,
    max_depth: int = 3,
    include_file_sizes: bool = False,
) -> dict:
    root = settings.project_root

    def _build_tree(dir_path: Path, depth: int) -> dict:
        node: dict = {"name": dir_path.name, "type": "directory", "children": []}
        file_count = 0
        lang_counter: Counter[str] = Counter()
        total_size = 0

        try:
            entries = sorted(dir_path.iterdir(), key=lambda p: (p.is_file(), p.name))
        except PermissionError:
            return node

        for entry in entries:
            if entry.name in SKIP_DIR_NAMES:
                continue
            if entry.is_dir():
                if depth >= max_depth:
                    sub_count, sub_langs, sub_size = _summarize_subtree(entry)
                    file_count += sub_count
                    lang_counter.update(sub_langs)
                    total_size += sub_size
                    node["children"].append({
                        "name": entry.name,
                        "type": "directory",
                        "collapsed": True,
                        "file_count": sub_count,
                        "languages": dict(sub_langs),
                    })
                else:
                    child = _build_tree(entry, depth + 1)
                    file_count += child.get("file_count", 0)
                    lang_counter.update(child.get("languages", {}))
                    total_size += child.get("total_size_bytes", 0)
                    node["children"].append(child)
            elif entry.is_file():
                file_count += 1
                lang = detect_language(entry)
                if lang:
                    lang_counter[lang] += 1
                try:
                    size = entry.stat().st_size
                except OSError:
                    size = 0
                total_size += size
                child_node: dict = {"name": entry.name, "type": "file"}
                if lang:
                    child_node["language"] = lang
                if include_file_sizes:
                    child_node["size_bytes"] = size
                node["children"].append(child_node)

        node["file_count"] = file_count
        node["languages"] = dict(lang_counter)
        if include_file_sizes:
            node["total_size_bytes"] = total_size
        return node

    def _summarize_subtree(dir_path: Path) -> tuple[int, Counter[str], int]:
        count = 0
        langs: Counter[str] = Counter()
        size = 0
        for p in dir_path.rglob("*"):
            if any(part in SKIP_DIR_NAMES for part in p.parts):
                continue
            if p.is_file():
                count += 1
                lang = detect_language(p)
                if lang:
                    langs[lang] += 1
                try:
                    size += p.stat().st_size
                except OSError:
                    pass
        return count, langs, size

    tree = _build_tree(root, 0)
    return {
        "tree": tree,
        "summary": {
            "total_files": tree.get("file_count", 0),
            "languages": tree.get("languages", {}),
        },
        "commit_hash": cache_key(root),
    }
