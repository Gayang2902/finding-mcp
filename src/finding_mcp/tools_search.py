"""Search tools backed by ripgrep."""

from __future__ import annotations

from . import ripgrep
from .config import Settings
from .models import PaginatedResponse


def search_code(
    settings: Settings,
    pattern: str,
    glob: str | None = None,
    language: str | None = None,
    limit: int = 50,
    case_sensitive: bool = True,
) -> PaginatedResponse:
    """Regex search."""
    if limit > settings.max_limit:
        limit = settings.max_limit
    hits, truncated = ripgrep.search(
        settings.project_root,
        pattern,
        fixed_string=False,
        glob=glob,
        language=language,
        limit=limit,
        case_sensitive=case_sensitive,
    )
    return PaginatedResponse(
        items=[h.model_dump() for h in hits],
        truncated=truncated,
    )


def search_literal(
    settings: Settings,
    text: str,
    glob: str | None = None,
    language: str | None = None,
    limit: int = 50,
    case_sensitive: bool = True,
) -> PaginatedResponse:
    """Literal string search (no regex interpretation). Best for sink names with
    parens, payloads, or symbols containing regex metacharacters.
    """
    if limit > settings.max_limit:
        limit = settings.max_limit
    hits, truncated = ripgrep.search(
        settings.project_root,
        text,
        fixed_string=True,
        glob=glob,
        language=language,
        limit=limit,
        case_sensitive=case_sensitive,
    )
    return PaginatedResponse(
        items=[h.model_dump() for h in hits],
        truncated=truncated,
    )
