"""Vulnerability hunting tools — high-level primitives that reduce agent roundtrips.

These compose lower-level indexers (ctags, tree-sitter, ripgrep) into
security-focused queries that would otherwise require 5-15 tool calls.
"""

from __future__ import annotations

from collections import deque
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from ..config import Settings
from ..core import ripgrep
from ..core.git_utils import cache_key
from ..indexers.ctags import get_index
from ..indexers.treesitter import TreeSitterError, list_callees

# ---------------------------------------------------------------------------
# Dangerous sink patterns by language
# ---------------------------------------------------------------------------

SINK_PATTERNS: dict[str, list[tuple[str, str]]] = {
    "javascript": [
        (r"\beval\s*\(", "code_injection"),
        (r"\bFunction\s*\(", "code_injection"),
        (r"child_process\.\w+\s*\(", "command_injection"),
        (r"\bexec\s*\(", "command_injection"),
        (r"\bexecSync\s*\(", "command_injection"),
        (r"\.innerHTML\s*=", "xss"),
        (r"document\.write\s*\(", "xss"),
        (r"\.\$\{.*\}.*query|\.query\s*\(", "sql_injection"),
        (r"\.redirect\s*\(", "open_redirect"),
        (r"(axios|fetch|http\.request|https\.request)\s*\(", "ssrf"),
        (r"fs\.(readFile|writeFile|unlink|rmdir)\w*\s*\(", "path_traversal"),
        (r"\.deserialize\s*\(", "deserialization"),
    ],
    "typescript": [],  # filled below
    "java": [
        (r"Runtime\.getRuntime\(\)\.\s*exec\s*\(", "command_injection"),
        (r"ProcessBuilder\s*\(", "command_injection"),
        (r"\.execute(Query|Update|Batch)?\s*\(", "sql_injection"),
        (r"createQuery\s*\(", "sql_injection"),
        (r"createNativeQuery\s*\(", "sql_injection"),
        (r"createStatement\s*\(", "sql_injection"),
        (r"\.readObject\s*\(", "deserialization"),
        (r"InitialContext\)?\s*\.\s*lookup\s*\(", "jndi_injection"),
        (r"SpelExpressionParser\s*\(", "spel_injection"),
        (r"sendRedirect\s*\(", "open_redirect"),
        (r"(URL|HttpURLConnection|RestTemplate)\s*[\.(]", "ssrf"),
        (r"new\s+File\s*\(", "path_traversal"),
        (r"FileInputStream\s*\(", "path_traversal"),
    ],
    "php": [
        (r"\b(exec|system|passthru|shell_exec|popen|proc_open)\s*\(", "command_injection"),
        (r"\beval\s*\(", "code_injection"),
        (r"\b(include|require|include_once|require_once)\s*[\(\$]", "file_inclusion"),
        (r"\b(mysqli_query|mysql_query|pg_query)\s*\(", "sql_injection"),
        (r"\->query\s*\(", "sql_injection"),
        (r"\bunserialize\s*\(", "deserialization"),
        (r"\bfile_get_contents\s*\(", "ssrf"),
        (r"\bcurl_exec\s*\(", "ssrf"),
        (r"\b(fopen|file_put_contents|unlink|rmdir)\s*\(", "path_traversal"),
        (r"\bheader\s*\(\s*['\"]Location", "open_redirect"),
        (r"\becho\b|\bprint\b", "xss"),
    ],
}
SINK_PATTERNS["typescript"] = SINK_PATTERNS["javascript"]
SINK_PATTERNS["tsx"] = SINK_PATTERNS["javascript"]

# ---------------------------------------------------------------------------
# Entry point patterns by language
# ---------------------------------------------------------------------------

ENTRY_PATTERNS: dict[str, list[tuple[str, str]]] = {
    "javascript": [
        (r"app\.(get|post|put|delete|patch|all)\s*\(", "http_handler"),
        (r"router\.(get|post|put|delete|patch|all)\s*\(", "http_handler"),
        (r"\.on\s*\(\s*['\"]message", "event_listener"),
        (r"\.on\s*\(\s*['\"]data", "event_listener"),
        (r"\.on\s*\(\s*['\"]connection", "event_listener"),
        (r"exports\.\w+\s*=\s*async\s*\(event", "lambda_handler"),
        (r"module\.exports\s*=\s*async\s*\(event", "lambda_handler"),
    ],
    "typescript": [],
    "java": [
        (r"@(Get|Post|Put|Delete|Patch|Request)Mapping", "http_handler"),
        (r"@(GET|POST|PUT|DELETE|PATCH)\b", "http_handler"),  # JAX-RS
        (r"public\s+static\s+void\s+main\s*\(", "main_method"),
        (r"@EventListener", "event_listener"),
        (r"@RabbitListener", "message_listener"),
        (r"@KafkaListener", "message_listener"),
        (r"@Scheduled", "scheduled_task"),
        (r"doGet\s*\(|doPost\s*\(|service\s*\(HttpServlet", "servlet"),
    ],
    "php": [
        (r"Route::(get|post|put|delete|patch|any)\s*\(", "http_handler"),
        (r"function\s+(store|update|destroy|index|show)\s*\(", "controller_action"),
        (r"\$_GET|\$_POST|\$_REQUEST|\$_FILES", "direct_input"),
        (r"function\s+handle\s*\(", "command_handler"),
    ],
}
ENTRY_PATTERNS["typescript"] = ENTRY_PATTERNS["javascript"]
ENTRY_PATTERNS["tsx"] = ENTRY_PATTERNS["javascript"]


# ---------------------------------------------------------------------------
# Implementation
# ---------------------------------------------------------------------------


def list_dangerous_sinks(
    settings: Settings,
    language: str | None = None,
    limit: int = 100,
) -> dict:
    """Find known dangerous function calls (sinks) in the codebase."""
    root = settings.require_project_root()

    languages = [language] if language else list(SINK_PATTERNS.keys())
    # Deduplicate (typescript == javascript patterns)
    seen_langs: set[str] = set()
    results: list[dict] = []

    for lang in languages:
        if lang not in SINK_PATTERNS or lang in seen_langs:
            continue
        seen_langs.add(lang)

        for pattern, vuln_type in SINK_PATTERNS[lang]:
            if len(results) >= limit:
                break
            hits, _ = ripgrep.search(
                root,
                pattern,
                language=lang if lang not in ("tsx",) else "typescript",
                limit=min(10, limit - len(results)),
            )
            for h in hits:
                results.append({
                    "vulnerability_type": vuln_type,
                    "language": lang,
                    "location": h.location.model_dump(),
                    "line_text": h.line_text,
                })
        if len(results) >= limit:
            break

    return {
        "sinks": results,
        "total": len(results),
        "truncated": len(results) >= limit,
        "note": "Static pattern match — custom sinks or wrapped calls require manual search_code",
        "commit_hash": cache_key(root),
    }


def list_entry_points(
    settings: Settings,
    language: str | None = None,
    limit: int = 100,
) -> dict:
    """Find external input entry points (HTTP handlers, event listeners, etc.)."""
    root = settings.require_project_root()

    languages = [language] if language else list(ENTRY_PATTERNS.keys())
    seen_langs: set[str] = set()
    results: list[dict] = []

    for lang in languages:
        if lang not in ENTRY_PATTERNS or lang in seen_langs:
            continue
        seen_langs.add(lang)

        for pattern, entry_type in ENTRY_PATTERNS[lang]:
            if len(results) >= limit:
                break
            hits, _ = ripgrep.search(
                root,
                pattern,
                language=lang if lang not in ("tsx",) else "typescript",
                limit=min(10, limit - len(results)),
            )
            for h in hits:
                results.append({
                    "entry_type": entry_type,
                    "language": lang,
                    "location": h.location.model_dump(),
                    "line_text": h.line_text,
                })
        if len(results) >= limit:
            break

    return {
        "entry_points": results,
        "total": len(results),
        "truncated": len(results) >= limit,
        "note": "Static pattern match — dynamic routing or reflection-based handlers may not appear",  # noqa: E501
        "commit_hash": cache_key(root),
    }


def trace_call_chain(
    settings: Settings,
    source_function: str,
    sink_pattern: str,
    max_depth: int = 6,
) -> dict:
    """BFS through the call graph from source_function looking for sink_pattern.

    Returns the call chain if a path is found, or explored nodes if not.
    Uses tree-sitter for callees and ctags for resolving definitions.
    """
    root = settings.require_project_root()
    index = get_index(root, settings.cache_dir)

    # Find starting function definition
    tags = index.lookup(source_function)
    if not tags:
        return {"error": f"Function not found: {source_function}", "chain": []}

    # BFS state
    # Each queue entry: (function_name, file_path, chain_so_far)
    queue: deque[tuple[str, Path, list[dict]]] = deque()
    visited: set[tuple[str, str]] = set()

    for tag in tags:
        abs_path = root / tag.path
        if abs_path.is_file():
            entry = {"function": tag.name, "file": tag.path, "line": tag.line}
            queue.append((tag.name, abs_path, [entry]))
            visited.add((tag.name, tag.path))

    found_chains: list[list[dict]] = []
    explored: list[str] = []
    max_explored = 200

    while queue and len(explored) < max_explored:
        func_name, file_path, chain = queue.popleft()

        if len(chain) > max_depth:
            continue

        try:
            callees = list_callees(file_path, func_name)
        except TreeSitterError:
            continue

        for callee_name, loc in callees:
            # Normalize: strip object prefix (e.g., "obj.method" → "method")
            short_name = callee_name.split(".")[-1] if "." in callee_name else callee_name

            # Check if this callee matches the sink pattern
            import re
            if re.search(sink_pattern, callee_name):
                rel_path = str(file_path.relative_to(root))
                sink_step = {
                    "function": callee_name,
                    "file": rel_path,
                    "line": loc.line,
                    "is_sink": True,
                }
                found_chains.append(chain + [sink_step])
                continue

            # Resolve definition and continue BFS
            callee_tags = index.lookup(short_name)
            for ct in callee_tags:
                key = (ct.name, ct.path)
                if key in visited:
                    continue
                visited.add(key)
                ct_path = root / ct.path
                if not ct_path.is_file():
                    continue
                step = {"function": ct.name, "file": ct.path, "line": ct.line}
                queue.append((ct.name, ct_path, chain + [step]))
                explored.append(f"{ct.name} @ {ct.path}:{ct.line}")

    return {
        "chains_found": len(found_chains),
        "chains": found_chains[:10],
        "explored_count": len(explored),
        "max_depth": max_depth,
        "note": "Static call graph — indirect calls (callbacks, reflection, dynamic dispatch) not traced",  # noqa: E501
        "commit_hash": cache_key(root),
    }


# ---------------------------------------------------------------------------
# MCP registration
# ---------------------------------------------------------------------------


def register(mcp: FastMCP, settings: Settings) -> None:
    @mcp.tool(name="list_dangerous_sinks")
    def _list_dangerous_sinks(
        language: str | None = None,
        limit: int = 100,
    ) -> dict:
        """Find known dangerous function calls (sinks) in the codebase.

        Scans for patterns like eval(), exec(), SQL query execution,
        file operations, deserialization, SSRF-prone calls, etc.

        Results are grouped by vulnerability type. Use trace_call_chain
        to verify if user input actually reaches these sinks.

        NOTE: Only detects known patterns. Custom sinks or wrapped
        dangerous calls require manual search_code.

        Args:
            language: Filter to specific language (java, javascript, php, typescript).
            limit: Max results (default 100).
        """
        return list_dangerous_sinks(settings, language, limit)

    @mcp.tool(name="list_entry_points")
    def _list_entry_points(
        language: str | None = None,
        limit: int = 100,
    ) -> dict:
        """Find external input entry points — where user data enters the application.

        Detects HTTP route handlers, event listeners, message consumers,
        CLI parsers, lambda handlers, and direct input access ($_GET, etc.).

        Use this as the starting point for vulnerability analysis:
        entry_points → trace_call_chain → dangerous_sinks.

        NOTE: Static pattern match — dynamic routing or reflection-based
        handlers may not appear. Use map_routes for framework-aware detection.

        Args:
            language: Filter to specific language.
            limit: Max results (default 100).
        """
        return list_entry_points(settings, language, limit)

    @mcp.tool(name="trace_call_chain")
    def _trace_call_chain(
        source_function: str,
        sink_pattern: str,
        max_depth: int = 6,
    ) -> dict:
        """Trace the call graph from a function to see if it reaches a dangerous sink.

        Performs BFS through the static call graph starting from source_function,
        checking each callee against sink_pattern (regex).

        Example: trace_call_chain("handleRequest", "exec|query|eval")
        → finds if handleRequest can reach exec(), query(), or eval() within 6 hops.

        Returns found chains (source→...→sink) or empty if no path exists.

        NOTE: Static analysis only — cannot follow callbacks, dynamic dispatch,
        or cross-process calls. For those cases, combine with search_code.

        Args:
            source_function: Starting function name.
            sink_pattern: Regex pattern matching sink function names.
            max_depth: Maximum call chain depth (default 6).
        """
        if max_depth > 10:
            max_depth = 10
        return trace_call_chain(settings, source_function, sink_pattern, max_depth)
