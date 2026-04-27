"""Smoke tests against a tiny in-repo fixture project."""

from __future__ import annotations

from pathlib import Path

import pytest

from finding_mcp.config import Settings
from finding_mcp.tools_meta import get_repo_info, list_files
from finding_mcp.tools_search import search_literal
from finding_mcp.tools_structure import get_function, get_imports


@pytest.fixture
def fixture_settings(tmp_path: Path) -> Settings:
    proj = tmp_path / "fixture"
    proj.mkdir()
    (proj / "src").mkdir()
    (proj / "src" / "Hello.java").write_text(
        """package com.example;

import java.util.List;

public class Hello {
    public String greet(String name) {
        return "hello " + sanitize(name);
    }

    private String sanitize(String s) {
        return s.replaceAll("<", "&lt;");
    }
}
""",
        encoding="utf-8",
    )
    (proj / "src" / "app.js").write_text(
        """import express from 'express';

function vulnerableRoute(req, res) {
    const cmd = req.query.cmd;
    eval(cmd);
}

export default vulnerableRoute;
""",
        encoding="utf-8",
    )
    cache = tmp_path / "cache"
    cache.mkdir()
    return Settings(project_root=proj, cache_dir=cache)


def test_repo_info(fixture_settings: Settings) -> None:
    info = get_repo_info(fixture_settings)
    assert info.total_files == 2
    assert info.languages.get("java") == 1
    assert info.languages.get("javascript") == 1


def test_list_files(fixture_settings: Settings) -> None:
    result = list_files(fixture_settings)
    paths = {item["path"] for item in result.items}
    assert "src/Hello.java" in paths
    assert "src/app.js" in paths


def test_get_function_java(fixture_settings: Settings) -> None:
    fb = get_function(fixture_settings, "src/Hello.java", "greet")
    assert fb is not None
    assert "sanitize" in fb.body
    assert fb.language == "java"


def test_get_function_javascript(fixture_settings: Settings) -> None:
    fb = get_function(fixture_settings, "src/app.js", "vulnerableRoute")
    assert fb is not None
    assert "eval" in fb.body


def test_get_imports_java(fixture_settings: Settings) -> None:
    imports = get_imports(fixture_settings, "src/Hello.java")
    assert any("java.util.List" in i.target or "List" in i.raw for i in imports)


def test_get_imports_javascript(fixture_settings: Settings) -> None:
    imports = get_imports(fixture_settings, "src/app.js")
    assert any("express" in i.target for i in imports)


def test_search_literal(fixture_settings: Settings) -> None:
    result = search_literal(fixture_settings, "eval(", limit=10)
    assert any("app.js" in item["location"]["file_path"] for item in result.items)
