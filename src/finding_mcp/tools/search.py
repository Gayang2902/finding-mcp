"""Search tools backed by ripgrep."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from ..config import Settings
from ..core import ripgrep
from ..core.git_utils import cache_key
from ..models import PaginatedResponse


def search_code(
    settings: Settings,
    pattern: str,
    glob: str | None = None,
    language: str | None = None,
    limit: int = 50,
    case_sensitive: bool = True,
) -> PaginatedResponse:
    """Regex search."""
    root = settings.require_project_root()
    if limit > settings.max_limit:
        limit = settings.max_limit
    hits, truncated = ripgrep.search(
        root,
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
    root = settings.require_project_root()
    if limit > settings.max_limit:
        limit = settings.max_limit
    hits, truncated = ripgrep.search(
        root,
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


def register(mcp: FastMCP, settings: Settings) -> None:
    @mcp.tool(name="search_code")
    def _search_code(
        pattern: str,
        glob: str | None = None,
        language: str | None = None,
        limit: int = 50,
        case_sensitive: bool = True,
    ) -> dict:
        """Regex search across the codebase.

        Args:
            pattern: PCRE-style regex.
            glob: Optional file glob (e.g. "src/**/*.java").
            language: Optional language filter.
        """
        result = search_code(settings, pattern, glob, language, limit, case_sensitive)
        result.commit_hash = cache_key(settings.project_root)
        return result.model_dump()

    @mcp.tool(name="search_literal")
    def _search_literal(
        text: str,
        glob: str | None = None,
        language: str | None = None,
        limit: int = 50,
        case_sensitive: bool = True,
    ) -> dict:
        """Literal string search (no regex). Use for sink names like
        `Runtime.getRuntime().exec(` or payload strings with metacharacters.
        """
        result = search_literal(settings, text, glob, language, limit, case_sensitive)
        result.commit_hash = cache_key(settings.project_root)
        return result.model_dump()
