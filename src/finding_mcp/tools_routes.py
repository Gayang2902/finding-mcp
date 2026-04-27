"""Route extraction tools."""

from __future__ import annotations

from pathlib import Path

from . import framework_detect
from .config import Settings
from .models import AuthCoverageResult, RouteDefinition, RouteMapResult
from .route_extractors import extract_routes
from .tools_meta import _iter_files

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
    detections = framework_detect.detect_frameworks(settings.project_root)

    if framework:
        frameworks = [framework]
    else:
        frameworks = list({d.framework for d in detections})

    all_files = _collect_files(settings.project_root)
    all_routes: list[RouteDefinition] = []
    all_global_mw: list[str] = []

    for fw in frameworks:
        routes, global_mw = extract_routes(settings.project_root, fw, all_files)
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
