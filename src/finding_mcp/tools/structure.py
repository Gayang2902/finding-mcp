"""Structure tools backed by tree-sitter."""

from __future__ import annotations

from pathlib import Path

from mcp.server.fastmcp import FastMCP

from ..config import Settings
from ..core import ripgrep
from ..core.git_utils import cache_key
from ..core.ripgrep import regex_escape
from ..indexers import treesitter
from ..models import (
    CallSite,
    CodeLocation,
    FunctionBody,
    ImportEntry,
    PaginatedResponse,
)


def _resolve_path(settings: Settings, file_path: str) -> Path:
    root = settings.require_project_root()
    abs_path = (root / file_path).resolve()
    try:
        abs_path.relative_to(root)
    except ValueError as e:
        raise ValueError(f"file_path must be inside project root: {file_path}") from e
    if not abs_path.is_file():
        raise FileNotFoundError(f"File not found: {file_path}")
    return abs_path


def _to_relative_location(loc: CodeLocation, project_root: Path) -> CodeLocation:
    p = Path(loc.file_path)
    if p.is_absolute():
        try:
            rel = str(p.relative_to(project_root))
        except ValueError:
            rel = loc.file_path
        return CodeLocation(
            file_path=rel,
            line=loc.line,
            end_line=loc.end_line,
            column=loc.column,
        )
    return loc


def get_function(
    settings: Settings,
    file_path: str,
    function_name: str,
) -> FunctionBody | None:
    abs_path = _resolve_path(settings, file_path)
    fb = treesitter.find_function(abs_path, function_name)
    if fb is None:
        return None
    fb.location = _to_relative_location(fb.location, settings.project_root)
    return fb


def get_function_at(
    settings: Settings,
    file_path: str,
    line: int,
) -> FunctionBody | None:
    abs_path = _resolve_path(settings, file_path)
    fb = treesitter.find_function_at_line(abs_path, line)
    if fb is None:
        return None
    fb.location = _to_relative_location(fb.location, settings.project_root)
    return fb


def get_callees(
    settings: Settings,
    file_path: str,
    function_name: str,
) -> list[CallSite]:
    abs_path = _resolve_path(settings, file_path)
    pairs = treesitter.list_callees(abs_path, function_name)

    # Read source once for line text snippets
    source = abs_path.read_text(encoding="utf-8", errors="replace").splitlines()

    out: list[CallSite] = []
    for callee, loc in pairs:
        rel_loc = _to_relative_location(loc, settings.project_root)
        line_text = ""
        if 1 <= loc.line <= len(source):
            line_text = source[loc.line - 1].strip()
        out.append(CallSite(callee=callee, location=rel_loc, line_text=line_text))
    return out


def get_callers(
    settings: Settings,
    symbol: str,
    limit: int = 50,
) -> PaginatedResponse:
    """Find call sites of `symbol` across the codebase.

    Heuristic: ripgrep for `symbol(` (call pattern) word-bounded. Then optionally
    refine by parsing each hit's enclosing function. Phase 1 returns the raw hits
    so the LLM can decide which are real calls.
    """
    root = settings.require_project_root()
    pattern = rf"\b{regex_escape(symbol)}\s*\("
    hits, truncated = ripgrep.search(
        root,
        pattern,
        limit=limit,
    )

    # Filter out self-definitions (the def line itself starts with `function`/`def`/etc.)
    callers: list[CallSite] = []
    for h in hits:
        text = h.line_text
        # Crude heuristic: skip lines that look like definitions
        lowered = text.lstrip()
        if lowered.startswith(("function ", "def ", "fun ")):
            continue
        callers.append(
            CallSite(
                callee=symbol,
                location=h.location,
                line_text=text,
            )
        )

    return PaginatedResponse(
        items=[c.model_dump() for c in callers],
        truncated=truncated,
    )


def get_imports(settings: Settings, file_path: str) -> list[ImportEntry]:
    abs_path = _resolve_path(settings, file_path)
    entries = treesitter.list_imports(abs_path)
    for e in entries:
        e.location = _to_relative_location(e.location, settings.project_root)
    return entries


def register(mcp: FastMCP, settings: Settings) -> None:
    @mcp.tool(name="get_function")
    def _get_function(file_path: str, function_name: str) -> dict:
        """Return the full body and signature of a named function in a file.

        Useful when an agent has a function name from `find_definition` and
        wants the source.
        """
        fb = get_function(settings, file_path, function_name)
        return {
            "function": fb.model_dump() if fb else None,
            "commit_hash": cache_key(settings.project_root),
        }

    @mcp.tool(name="get_function_at")
    def _get_function_at(file_path: str, line: int) -> dict:
        """Return the function enclosing a given line. Useful for resolving the
        context of a search hit.
        """
        fb = get_function_at(settings, file_path, line)
        return {
            "function": fb.model_dump() if fb else None,
            "commit_hash": cache_key(settings.project_root),
        }

    @mcp.tool(name="get_callees")
    def _get_callees(file_path: str, function_name: str) -> dict:
        """List every call expression made inside a given function.

        AST-based; does not resolve overloads or dynamic dispatch.
        """
        callees = get_callees(settings, file_path, function_name)
        return {
            "callees": [c.model_dump() for c in callees],
            "commit_hash": cache_key(settings.project_root),
        }

    @mcp.tool(name="get_callers")
    def _get_callers(symbol: str, limit: int = 50) -> dict:
        """Find places that appear to call `symbol`.

        Heuristic: ripgrep for `symbol(`. Definitions are filtered out.
        Cross-validate with `get_function_at` for high-confidence answers.
        """
        result = get_callers(settings, symbol, limit)
        result.commit_hash = cache_key(settings.project_root)
        return result.model_dump()

    @mcp.tool(name="get_imports")
    def _get_imports(file_path: str) -> dict:
        """List all import / use / require declarations in a file."""
        entries = get_imports(settings, file_path)
        return {
            "imports": [e.model_dump() for e in entries],
            "commit_hash": cache_key(settings.project_root),
        }

