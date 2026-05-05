"""Auto-detect web frameworks from project files."""

from __future__ import annotations

import json
from pathlib import Path

from ..core import ripgrep
from ..models import FrameworkDetection


def detect_frameworks(project_root: Path) -> list[FrameworkDetection]:
    detected: list[FrameworkDetection] = []

    # --- Node.js: package.json ---
    pkg_json = project_root / "package.json"
    if pkg_json.is_file():
        try:
            pkg = json.loads(pkg_json.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pkg = {}
        all_deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
        if "express" in all_deps:
            detected.append(FrameworkDetection(
                framework="express",
                language="javascript",
                confidence="high",
                evidence="express in package.json dependencies",
            ))
        if "fastify" in all_deps:
            detected.append(FrameworkDetection(
                framework="fastify",
                language="javascript",
                confidence="high",
                evidence="fastify in package.json dependencies",
            ))

    # --- Java: pom.xml / build.gradle ---
    pom = project_root / "pom.xml"
    if pom.is_file():
        try:
            pom_text = pom.read_text(encoding="utf-8")
        except OSError:
            pom_text = ""
        if "spring-boot-starter-web" in pom_text:
            detected.append(FrameworkDetection(
                framework="spring",
                language="java",
                confidence="high",
                evidence="spring-boot-starter-web in pom.xml",
            ))

    gradle = project_root / "build.gradle"
    if gradle.is_file():
        try:
            gradle_text = gradle.read_text(encoding="utf-8")
        except OSError:
            gradle_text = ""
        if "spring-boot-starter-web" in gradle_text:
            detected.append(FrameworkDetection(
                framework="spring",
                language="java",
                confidence="high",
                evidence="spring-boot-starter-web in build.gradle",
            ))

    # --- PHP: composer.json ---
    composer = project_root / "composer.json"
    if composer.is_file():
        try:
            comp = json.loads(composer.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            comp = {}
        all_deps = {**comp.get("require", {}), **comp.get("require-dev", {})}
        if "laravel/framework" in all_deps:
            detected.append(FrameworkDetection(
                framework="laravel",
                language="php",
                confidence="high",
                evidence="laravel/framework in composer.json",
            ))

    if detected:
        return detected

    # --- Fallback: ripgrep for import patterns ---
    _FALLBACK_PATTERNS: list[tuple[str, str, str]] = [
        (r"require\(['\"]express['\"]\)", "express", "javascript"),
        (r"from\s+['\"]express['\"]", "express", "javascript"),
        (r"import\s+org\.springframework\.web", "spring", "java"),
        (r"@(Get|Post|Put|Delete|Patch|Request)Mapping", "spring", "java"),
        (r"Route::(get|post|put|delete|patch)", "laravel", "php"),
    ]

    seen: set[str] = set()
    for pattern, framework, language in _FALLBACK_PATTERNS:
        if framework in seen:
            continue
        hits, _ = ripgrep.search(project_root, pattern, limit=1)
        if hits:
            seen.add(framework)
            detected.append(FrameworkDetection(
                framework=framework,
                language=language,
                confidence="medium",
                evidence=f"ripgrep match for {pattern}",
            ))

    return detected
