"""Extract Laravel PHP routes using ripgrep."""

from __future__ import annotations

import re
from pathlib import Path

from ..core import ripgrep
from ..models import RouteDefinition


def extract(project_root: Path, files: list[Path]) -> tuple[list[RouteDefinition], list[str]]:
    routes: list[RouteDefinition] = []

    pattern = r"Route::(get|post|put|delete|patch)\s*\("
    hits, _ = ripgrep.search(project_root, pattern, limit=500)

    for hit in hits:
        match = re.search(
            r"Route::(get|post|put|delete|patch)\s*\(\s*['\"]([^'\"]+)['\"]",
            hit.line_text,
        )
        if not match:
            continue

        method = match.group(1).upper()
        path = match.group(2)

        # Detect middleware chaining on same line
        middleware: list[str] = []
        mw_match = re.search(r"->middleware\s*\(\s*['\"]([^'\"]+)['\"]", hit.line_text)
        if mw_match:
            middleware.append(mw_match.group(1))

        handler_match = re.search(r",\s*['\"]([^'\"]+)['\"]", hit.line_text[match.end():])
        handler_name = handler_match.group(1) if handler_match else None

        routes.append(RouteDefinition(
            http_method=method,
            path=path,
            handler_name=handler_name,
            middleware=middleware,
            has_auth_middleware=False,
            framework="laravel",
            location=hit.location,
        ))

    return routes, []
