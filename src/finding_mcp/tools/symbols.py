"""Symbol-based tools backed by ctags (+ ripgrep for references)."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from ..config import Settings
from ..core import ripgrep
from ..core.git_utils import cache_key
from ..core.ripgrep import regex_escape
from ..indexers.ctags import TagEntry, get_index
from ..models import (
    CodeLocation,
    PaginatedResponse,
    SymbolDefinition,
    SymbolReference,
)


def _tag_to_definition(tag: TagEntry) -> SymbolDefinition:
    return SymbolDefinition(
        name=tag.name,
        kind=tag.kind,
        location=CodeLocation(file_path=tag.path, line=tag.line),
        signature=tag.signature,
        language=tag.language.lower() if tag.language else None,
        scope=tag.scope,
    )


def find_definition(
    settings: Settings,
    symbol: str,
    language: str | None = None,
) -> list[SymbolDefinition]:
    """Return all definitions for `symbol`. Multiple if overloaded/ambiguous."""
    root = settings.require_project_root()
    index = get_index(root, settings.cache_dir)
    tags = index.lookup(symbol)
    if language:
        wanted = language.lower()
        tags = [t for t in tags if (t.language or "").lower() == wanted
                or (t.language or "").lower() == "typescript" and wanted == "tsx"]
    return [_tag_to_definition(t) for t in tags]


def find_references(
    settings: Settings,
    symbol: str,
    language: str | None = None,
    limit: int = 50,
) -> PaginatedResponse:
    """Find usages via ripgrep. Word-boundary regex around the symbol.

    NOTE: This is a textual search and may include comments/strings. Callers
    that need precision should validate hits with `get_function_at`.
    """
    # \b doesn't work well for symbols with $ (PHP) or scope operators; word-bound is best-effort
    root = settings.require_project_root()
    pattern = rf"\b{regex_escape(symbol)}\b"
    hits, truncated = ripgrep.search(
        root,
        pattern,
        glob=None,
        language=language,
        limit=limit,
    )
    refs = [SymbolReference(location=h.location, line_text=h.line_text) for h in hits]
    return PaginatedResponse(
        items=[r.model_dump() for r in refs],
        truncated=truncated,
    )


def list_symbols(
    settings: Settings,
    file_path: str,
) -> list[SymbolDefinition]:
    """All symbols defined in a single file."""
    root = settings.require_project_root()
    abs_path = (root / file_path).resolve()
    try:
        rel = str(abs_path.relative_to(root))
    except ValueError as e:
        raise ValueError(
            f"file_path must be inside project root: {file_path}"
        ) from e

    index = get_index(root, settings.cache_dir)
    tags = index.in_file(rel)
    return [_tag_to_definition(t) for t in tags]


def register(mcp: FastMCP, settings: Settings) -> None:
    @mcp.tool(name="find_definition")
    def _find_definition(symbol: str, language: str | None = None) -> dict:
        """Find where a symbol (function, class, variable) is defined.

        Returns a list of definitions; multiple entries for overloads or
        cross-language symbols. Each definition includes file_path + line.

        Args:
            symbol: The symbol name to look up.
            language: Optional filter (java, php, javascript, typescript, tsx).
        """
        defs = find_definition(settings, symbol, language)
        return {
            "definitions": [d.model_dump() for d in defs],
            "commit_hash": cache_key(settings.project_root),
        }

    @mcp.tool(name="find_references")
    def _find_references(
        symbol: str,
        language: str | None = None,
        limit: int = 50,
    ) -> dict:
        """Find textual references to a symbol across the codebase.

        Uses word-boundary regex via ripgrep. Includes comments/strings — the
        agent should validate hits with `get_function_at` if precision matters.
        """
        result = find_references(settings, symbol, language, limit)
        result.commit_hash = cache_key(settings.project_root)
        return result.model_dump()

    @mcp.tool(name="list_symbols")
    def _list_symbols(file_path: str) -> dict:
        """List every symbol defined in a single file (functions, classes, variables)."""
        defs = list_symbols(settings, file_path)
        return {
            "file_path": file_path,
            "symbols": [d.model_dump() for d in defs],
            "commit_hash": cache_key(settings.project_root),
        }

