"""Route extraction dispatcher."""

from __future__ import annotations

from pathlib import Path

from ..models import RouteDefinition
from . import express, laravel, spring


def extract_routes(
    project_root: Path,
    framework: str,
    files: list[Path],
) -> tuple[list[RouteDefinition], list[str]]:
    """Return (routes, global_middleware) for the given framework."""
    if framework == "express":
        return express.extract(project_root, files)
    if framework == "spring":
        return spring.extract(project_root, files)
    if framework == "laravel":
        return laravel.extract(project_root, files)
    return [], []
