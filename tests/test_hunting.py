"""Tests for vulnerability hunting tools."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from finding_mcp.config import Settings
from finding_mcp.tools.hunting import list_dangerous_sinks, list_entry_points, trace_call_chain

_has_uctags = any(
    shutil.which(c) for c in ("/opt/homebrew/bin/ctags", "/usr/local/bin/ctags")
)
needs_uctags = pytest.mark.skipif(not _has_uctags, reason="universal-ctags not installed")


@pytest.fixture
def js_project(tmp_path: Path) -> Settings:
    proj = tmp_path / "app"
    proj.mkdir()
    (proj / "package.json").write_text('{"dependencies": {"express": "^4.18.0"}}')
    (proj / "app.js").write_text("""\
const express = require('express');
const app = express();
const { exec } = require('child_process');

app.get('/ping', (req, res) => {
    res.send('pong');
});

app.post('/run', (req, res) => {
    exec(req.body.cmd);
});

function processInput(data) {
    return eval(data);
}

function safeHelper(x) {
    return x.toString();
}
""")
    cache = tmp_path / "cache"
    cache.mkdir()
    return Settings(project_root=proj, cache_dir=cache)


@pytest.fixture
def java_project(tmp_path: Path) -> Settings:
    proj = tmp_path / "app"
    proj.mkdir()
    (proj / "pom.xml").write_text("<project></project>")
    src = proj / "src"
    src.mkdir()
    (src / "Controller.java").write_text("""\
package com.example;

import org.springframework.web.bind.annotation.*;
import java.sql.*;

@RestController
@RequestMapping("/api")
public class Controller {

    @GetMapping("/users")
    public String getUsers() {
        return service.findAll();
    }

    @PostMapping("/query")
    public String runQuery(String input) {
        Statement stmt = conn.createStatement();
        stmt.executeQuery(input);
        return "ok";
    }
}
""")
    cache = tmp_path / "cache"
    cache.mkdir()
    return Settings(project_root=proj, cache_dir=cache)


# --- list_dangerous_sinks ---


def test_sinks_js(js_project: Settings) -> None:
    result = list_dangerous_sinks(js_project, language="javascript")
    sinks = result["sinks"]
    assert len(sinks) > 0
    vuln_types = {s["vulnerability_type"] for s in sinks}
    assert "command_injection" in vuln_types
    assert "code_injection" in vuln_types


def test_sinks_java(java_project: Settings) -> None:
    result = list_dangerous_sinks(java_project, language="java")
    sinks = result["sinks"]
    assert len(sinks) > 0
    vuln_types = {s["vulnerability_type"] for s in sinks}
    assert "sql_injection" in vuln_types


def test_sinks_limit(js_project: Settings) -> None:
    result = list_dangerous_sinks(js_project, limit=2)
    assert len(result["sinks"]) <= 2


# --- list_entry_points ---


def test_entry_points_js(js_project: Settings) -> None:
    result = list_entry_points(js_project, language="javascript")
    entries = result["entry_points"]
    assert len(entries) > 0
    types = {e["entry_type"] for e in entries}
    assert "http_handler" in types


def test_entry_points_java(java_project: Settings) -> None:
    result = list_entry_points(java_project, language="java")
    entries = result["entry_points"]
    assert len(entries) > 0
    types = {e["entry_type"] for e in entries}
    assert "http_handler" in types


# --- trace_call_chain ---


@needs_uctags
def test_trace_finds_sink(js_project: Settings) -> None:
    result = trace_call_chain(js_project, "processInput", r"\beval\b")
    assert result["chains_found"] >= 1
    chain = result["chains"][0]
    assert chain[-1]["is_sink"] is True
    assert "eval" in chain[-1]["function"]


@needs_uctags
def test_trace_no_path(js_project: Settings) -> None:
    result = trace_call_chain(js_project, "safeHelper", r"\bexec\b")
    assert result["chains_found"] == 0


@needs_uctags
def test_trace_unknown_function(js_project: Settings) -> None:
    result = trace_call_chain(js_project, "nonExistentFunc", r"\beval\b")
    assert "error" in result
