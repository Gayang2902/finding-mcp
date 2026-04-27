"""Symbol-based tools backed by ctags (+ ripgrep for references)."""

from __future__ import annotations

from . import ripgrep
from .config import Settings
from .ctags_index import TagEntry, get_index
from .models import (
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
    index = get_index(settings.project_root, settings.cache_dir)
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
    pattern = rf"\b{_regex_escape(symbol)}\b"
    hits, truncated = ripgrep.search(
        settings.project_root,
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
    # Normalize the path
    abs_path = (settings.project_root / file_path).resolve()
    try:
        rel = str(abs_path.relative_to(settings.project_root))
    except ValueError as e:
        raise ValueError(
            f"file_path must be inside project root: {file_path}"
        ) from e

    index = get_index(settings.project_root, settings.cache_dir)
    tags = index.in_file(rel)
    return [_tag_to_definition(t) for t in tags]


def _regex_escape(s: str) -> str:
    """Escape regex metacharacters for ripgrep (PCRE2 default)."""
    out = []
    for ch in s:
        if ch in r".^$*+?()[]{}|\\":
            out.append("\\" + ch)
        else:
            out.append(ch)
    return "".join(out)
