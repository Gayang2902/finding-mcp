"""Route extraction tools."""

from __future__ import annotations

from pathlib import Path

from mcp.server.fastmcp import FastMCP

from ..analyzers import framework_detect
from ..config import Settings
from ..core.git_utils import cache_key
from ..models import AuthCoverageResult, RouteDefinition, RouteMapResult
from ..route_extractors import extract_routes
from .meta import _iter_files

AUTH_PATTERNS = [
    "auth", "authenticate", "requireauth", "isauthenticated",
    "passport", "jwt", "verifytoken", "checksession",
    "protect", "guard", "preauthorize", "secured", "rolesallowed",
]


def _has_auth(route: RouteDefinition, patterns: list[str]) -> bool:
    lower_mw = [m.lower() for m in route.middleware]
    for pat in patterns:
        pat_lower = pat.lower()
        for mw in lower_mw:
            if pat_lower in mw:
                return True
    return False


def _collect_files(project_root: Path) -> list[Path]:
    return list(_iter_files(project_root))


def map_routes(
    settings: Settings,
    framework: str | None = None,
) -> RouteMapResult:
    root = settings.require_project_root()
    detections = framework_detect.detect_frameworks(root)

    if framework:
        frameworks = [framework]
    else:
        frameworks = list({d.framework for d in detections})

    all_files = _collect_files(root)
    all_routes: list[RouteDefinition] = []
    all_global_mw: list[str] = []

    for fw in frameworks:
        routes, global_mw = extract_routes(root, fw, all_files)
        all_routes.extend(routes)
        all_global_mw.extend(global_mw)

    # Mark auth middleware on each route
    for route in all_routes:
        route.has_auth_middleware = _has_auth(route, AUTH_PATTERNS)

    return RouteMapResult(
        routes=all_routes,
        frameworks_detected=detections,
        global_middleware=all_global_mw,
        total_routes=len(all_routes),
        files_scanned=len(all_files),
    )


def check_auth_coverage(
    settings: Settings,
    framework: str | None = None,
    auth_patterns: list[str] | None = None,
) -> AuthCoverageResult:
    patterns = auth_patterns if auth_patterns else AUTH_PATTERNS

    result = map_routes(settings, framework)

    for route in result.routes:
        route.has_auth_middleware = _has_auth(route, patterns)

    unprotected = [r for r in result.routes if not r.has_auth_middleware]
    protected_count = len(result.routes) - len(unprotected)

    detected_patterns: list[str] = []
    for route in result.routes:
        for mw in route.middleware:
            for pat in patterns:
                if pat.lower() in mw.lower() and pat not in detected_patterns:
                    detected_patterns.append(pat)

    return AuthCoverageResult(
        total_routes=len(result.routes),
        protected_count=protected_count,
        unprotected_count=len(unprotected),
        unprotected_routes=unprotected,
        auth_patterns_detected=detected_patterns,
    )


def get_attack_surface(settings: Settings) -> dict:
    """Single pre-flight call that combines route mapping, auth coverage,
    entry points, and dangerous sinks into one compact summary."""
    from .hunting import list_dangerous_sinks, list_entry_points

    root = settings.require_project_root()
    auth_result = check_auth_coverage(settings)
    entry_result = list_entry_points(settings, limit=200)
    sink_result = list_dangerous_sinks(settings, limit=200)

    sinks_by_type: dict[str, int] = {}
    for sink in sink_result["sinks"]:
        vt = sink["vulnerability_type"]
        sinks_by_type[vt] = sinks_by_type.get(vt, 0) + 1

    entries_by_type: dict[str, int] = {}
    for ep in entry_result["entry_points"]:
        et = ep["entry_type"]
        entries_by_type[et] = entries_by_type.get(et, 0) + 1

    high_priority = []
    for route in auth_result.unprotected_routes:
        reasons = ["no_auth_middleware"]
        if "{" in route.path or ":" in route.path:
            reasons.append("path_param_idor_risk")
        if route.http_method.upper() in ("POST", "PUT", "PATCH", "DELETE"):
            reasons.append("state_mutating")
        high_priority.append({
            "method": route.http_method,
            "path": route.path,
            "file": route.location.file_path,
            "line": route.location.line,
            "handler": route.handler_name,
            "reasons": reasons,
        })

    high_priority.sort(key=lambda r: (
        -("path_param_idor_risk" in r["reasons"]),
        -("state_mutating" in r["reasons"]),
    ))

    return {
        "commit_hash": cache_key(root),
        "route_stats": {
            "total": auth_result.total_routes,
            "protected": auth_result.protected_count,
            "unprotected": auth_result.unprotected_count,
            "auth_patterns_detected": auth_result.auth_patterns_detected,
        },
        "high_priority_targets": high_priority[:20],
        "entry_points": {
            "total": entry_result["total"],
            "by_type": entries_by_type,
            "truncated": entry_result["truncated"],
        },
        "sinks": {
            "total": sink_result["total"],
            "by_type": sinks_by_type,
            "truncated": sink_result["truncated"],
        },
        "note": (
            "high_priority_targets = unprotected routes sorted by IDOR/mutation risk. "
            "Cross-reference sinks.by_type with trace_call_chain() from entry points. "
            "For IDOR on protected routes: use get_function_at() on handler, check if "
            "path params are compared against session identity before DB access."
        ),
    }


def register(mcp: FastMCP, settings: Settings) -> None:
    @mcp.tool(name="map_routes")
    def _map_routes(framework: str | None = None) -> dict:
        """Map all HTTP route definitions with their middleware chains.
        Auto-detects framework (express, spring, laravel, fastify) if not specified.
        Use check_auth_coverage() to find routes missing authentication.
        """
        result = map_routes(settings, framework)
        result.commit_hash = cache_key(settings.project_root)
        return result.model_dump()

    @mcp.tool(name="check_auth_coverage")
    def _check_auth_coverage(
        framework: str | None = None, auth_patterns: list[str] | None = None,
    ) -> dict:
        """Find routes that lack authentication middleware.
        Auto-detects auth patterns from codebase. Pass custom auth_patterns to override.

        After finding unprotected routes, also check IDOR on protected routes:
        - get_function_at() on the handler to inspect the body
        - Verify path params (req.params.id) are compared against session identity
        - If ownership logic may be in a service layer, follow with get_callees()
        """
        result = check_auth_coverage(settings, framework, auth_patterns)
        result.commit_hash = cache_key(settings.project_root)
        return result.model_dump()

    @mcp.tool(name="get_attack_surface")
    def _get_attack_surface() -> dict:
        """Single pre-flight call: maps routes, checks auth coverage, lists entry points and sinks.

        Returns a compact attack surface summary:
        - route_stats: total/protected/unprotected counts + detected auth patterns
        - high_priority_targets: unprotected routes sorted by IDOR/mutation risk
          (path params + POST/PUT/PATCH/DELETE ranked first)
        - entry_points.by_type: entry point counts grouped by type
        - sinks.by_type: dangerous sink counts grouped by vulnerability type

        Call this FIRST before dispatching to specialist analysis. Then use
        trace_call_chain() from high-priority entry points toward the top sink types.
        """
        return get_attack_surface(settings)
