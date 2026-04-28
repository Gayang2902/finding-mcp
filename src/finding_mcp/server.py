"""MCP server — 20 security analysis tools over stdio or SSE.

IMPORTANT: stdio transport reserves stdout exclusively for JSON-RPC.
All logging and diagnostics MUST go to stderr. Any non-JSON byte on
stdout will break the MCP protocol and cause "Connection closed" errors.
"""

from __future__ import annotations

import io
import logging
import os
import sys

# Force logging to stderr BEFORE importing anything that might configure handlers.
logging.basicConfig(
    level=logging.INFO,
    stream=sys.stderr,
    format="[%(asctime)s] %(levelname)s %(name)s: %(message)s",
    force=True,
)
log = logging.getLogger("finding-mcp")

from mcp.server.fastmcp import FastMCP  # noqa: E402, I001

from . import tools_meta, tools_routes, tools_search, tools_structure, tools_symbols, tools_taint  # noqa: E402
from .config import Settings, load_settings  # noqa: E402
from .git_utils import cache_key  # noqa: E402


def _guard_stdout() -> None:
    """Protect stdout from non-JSON-RPC writes in stdio transport mode.

    1. Reconfigures all logging handlers to stderr (in case libraries added stdout handlers).
    2. Captures Python warnings through the logging system (→ stderr).
    3. Redirects fd 1 to stderr so C-extension output can't corrupt the protocol.
    4. Gives sys.stdout the saved real stdout fd for MCP's JSON-RPC transport.
    """
    root = logging.getLogger()
    for h in root.handlers[:]:
        root.removeHandler(h)
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s %(name)s: %(message)s"))
    root.addHandler(handler)
    root.setLevel(logging.INFO)

    logging.captureWarnings(True)

    real_stdout_fd = os.dup(sys.stdout.fileno())
    os.dup2(sys.stderr.fileno(), 1)
    sys.stdout = io.TextIOWrapper(
        io.BufferedWriter(io.FileIO(real_stdout_fd, mode="w", closefd=True)),
        write_through=True,
    )


def _build_server(settings: Settings) -> FastMCP:
    mcp = FastMCP("finding-mcp")

    # ---------- Symbol tools (ctags) ----------

    @mcp.tool()
    def find_definition(symbol: str, language: str | None = None) -> dict:
        """Find where a symbol (function, class, variable) is defined.

        Returns a list of definitions; multiple entries for overloads or
        cross-language symbols. Each definition includes file_path + line.

        Args:
            symbol: The symbol name to look up.
            language: Optional filter (java, php, javascript, typescript, tsx).
        """
        defs = tools_symbols.find_definition(settings, symbol, language)
        return {
            "definitions": [d.model_dump() for d in defs],
            "commit_hash": cache_key(settings.project_root),
        }

    @mcp.tool()
    def find_references(
        symbol: str,
        language: str | None = None,
        limit: int = 50,
    ) -> dict:
        """Find textual references to a symbol across the codebase.

        Uses word-boundary regex via ripgrep. Includes comments/strings — the
        agent should validate hits with `get_function_at` if precision matters.
        """
        result = tools_symbols.find_references(settings, symbol, language, limit)
        result.commit_hash = cache_key(settings.project_root)
        return result.model_dump()

    @mcp.tool()
    def list_symbols(file_path: str) -> dict:
        """List every symbol defined in a single file (functions, classes, variables)."""
        defs = tools_symbols.list_symbols(settings, file_path)
        return {
            "file_path": file_path,
            "symbols": [d.model_dump() for d in defs],
            "commit_hash": cache_key(settings.project_root),
        }

    # ---------- Structure tools (tree-sitter) ----------

    @mcp.tool()
    def get_function(file_path: str, function_name: str) -> dict:
        """Return the full body and signature of a named function in a file.

        Useful when an agent has a function name from `find_definition` and
        wants the source.
        """
        fb = tools_structure.get_function(settings, file_path, function_name)
        return {
            "function": fb.model_dump() if fb else None,
            "commit_hash": cache_key(settings.project_root),
        }

    @mcp.tool()
    def get_function_at(file_path: str, line: int) -> dict:
        """Return the function enclosing a given line. Useful for resolving the
        context of a search hit.
        """
        fb = tools_structure.get_function_at(settings, file_path, line)
        return {
            "function": fb.model_dump() if fb else None,
            "commit_hash": cache_key(settings.project_root),
        }

    @mcp.tool()
    def get_callees(file_path: str, function_name: str) -> dict:
        """List every call expression made inside a given function.

        AST-based; does not resolve overloads or dynamic dispatch.
        """
        callees = tools_structure.get_callees(settings, file_path, function_name)
        return {
            "callees": [c.model_dump() for c in callees],
            "commit_hash": cache_key(settings.project_root),
        }

    @mcp.tool()
    def get_callers(symbol: str, limit: int = 50) -> dict:
        """Find places that appear to call `symbol`.

        Heuristic: ripgrep for `symbol(`. Definitions are filtered out.
        Cross-validate with `get_function_at` for high-confidence answers.
        """
        result = tools_structure.get_callers(settings, symbol, limit)
        result.commit_hash = cache_key(settings.project_root)
        return result.model_dump()

    @mcp.tool()
    def get_imports(file_path: str) -> dict:
        """List all import / use / require declarations in a file."""
        entries = tools_structure.get_imports(settings, file_path)
        return {
            "imports": [e.model_dump() for e in entries],
            "commit_hash": cache_key(settings.project_root),
        }

    # ---------- Search tools (ripgrep) ----------

    @mcp.tool()
    def search_code(
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
        result = tools_search.search_code(
            settings, pattern, glob, language, limit, case_sensitive
        )
        result.commit_hash = cache_key(settings.project_root)
        return result.model_dump()

    @mcp.tool()
    def search_literal(
        text: str,
        glob: str | None = None,
        language: str | None = None,
        limit: int = 50,
        case_sensitive: bool = True,
    ) -> dict:
        """Literal string search (no regex). Use for sink names like
        `Runtime.getRuntime().exec(` or payload strings with metacharacters.
        """
        result = tools_search.search_literal(
            settings, text, glob, language, limit, case_sensitive
        )
        result.commit_hash = cache_key(settings.project_root)
        return result.model_dump()

    # ---------- Meta tools ----------

    @mcp.tool()
    def list_files(glob: str | None = None, limit: int = 200) -> dict:
        """List files in the project, optionally filtered by glob."""
        result = tools_meta.list_files(settings, glob, limit)
        result.commit_hash = cache_key(settings.project_root)
        return result.model_dump()

    @mcp.tool()
    def get_file(
        file_path: str,
        line_start: int | None = None,
        line_end: int | None = None,
        line: int | None = None,
        before: int = 40,
        after: int = 40,
    ) -> dict:
        """Read a file or a line range. Output is capped to ~200KB.

        Two modes:
        - Range mode: line_start + line_end (absolute line numbers)
        - Center mode: line + before/after (show context around a specific line)
        """
        return tools_meta.get_file(
            settings, file_path, line_start, line_end,
            line=line, before=before, after=after,
        )

    @mcp.tool()
    def get_repo_info() -> dict:
        """Return project root, current commit, language distribution.

        Call this first when starting analysis on a new repository.
        """
        info = tools_meta.get_repo_info(settings)
        return info.model_dump()

    @mcp.tool()
    def get_project_structure(max_depth: int = 3, include_file_sizes: bool = False) -> dict:
        """Return the project directory tree with metadata (file counts, languages).

        Use this as a blueprint to understand project layout before deep-diving.
        """
        return tools_meta.get_project_structure(settings, max_depth, include_file_sizes)

    # ---------- Taint analysis tools (Semgrep) ----------

    @mcp.tool()
    def run_taint_analysis(
        rule_file: str | None = None,
        language: str | None = None,
        target_dir: str | None = None,
    ) -> dict:
        """Run Semgrep taint analysis to extract all Source->Sink data flow paths.

        If rule_file is not provided, uses built-in taint rules for the specified
        language (java, php, javascript). If language is also None, runs all built-in rules.

        Returns an analysis_id. Use get_taint_paths() to retrieve results.
        """
        return tools_taint.run_taint_analysis(settings, rule_file, language, target_dir)

    @mcp.tool()
    def get_taint_paths(
        analysis_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> dict:
        """List taint findings from a completed analysis (paginated summaries).

        Each result includes finding_id — use get_taint_path_detail() to inspect
        one path at a time for consistent, thorough analysis.
        """
        result = tools_taint.get_taint_paths(settings, analysis_id, limit, offset)
        return result.model_dump()

    @mcp.tool()
    def get_taint_path_detail(
        analysis_id: str,
        finding_id: str,
    ) -> dict:
        """Get full detail for one taint finding: code snippet, dataflow trace.

        Analyze one path at a time for consistency. Cross-reference with
        get_function_at() and get_callees() to validate the finding.
        """
        return tools_taint.get_taint_path_detail(settings, analysis_id, finding_id)

    @mcp.tool()
    def list_taint_analyses() -> dict:
        """List all completed taint analysis runs with their IDs and finding counts."""
        return tools_taint.list_analyses(settings)

    # ---------- Route extraction tools ----------

    @mcp.tool()
    def map_routes(framework: str | None = None) -> dict:
        """Map all HTTP route definitions with their middleware chains.
        Auto-detects framework (express, spring, laravel, fastify) if not specified.
        Use check_auth_coverage() to find routes missing authentication.
        """
        result = tools_routes.map_routes(settings, framework)
        result.commit_hash = cache_key(settings.project_root)
        return result.model_dump()

    @mcp.tool()
    def check_auth_coverage(
        framework: str | None = None, auth_patterns: list[str] | None = None,
    ) -> dict:
        """Find routes that lack authentication middleware.
        Auto-detects auth patterns from codebase. Pass custom auth_patterns to override.
        """
        result = tools_routes.check_auth_coverage(settings, framework, auth_patterns)
        result.commit_hash = cache_key(settings.project_root)
        return result.model_dump()

    return mcp


def main() -> None:
    settings = load_settings()

    log.info("Starting Finding MCP")
    log.info("  project_root: %s", settings.project_root)
    log.info("  transport:    %s", settings.transport)
    if settings.transport != "stdio":
        log.info("  listen:       %s:%d", settings.host, settings.port)

    if settings.transport == "stdio":
        _guard_stdout()

    mcp = _build_server(settings)

    if settings.transport == "sse":
        mcp.run(transport="sse", host=settings.host, port=settings.port)
    elif settings.transport == "streamable-http":
        mcp.run(transport="streamable-http", host=settings.host, port=settings.port)
    else:
        mcp.run()


if __name__ == "__main__":
    main()
