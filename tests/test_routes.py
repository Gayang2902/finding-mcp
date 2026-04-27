"""Tests for route extraction tools."""

from __future__ import annotations

from pathlib import Path

import pytest

from finding_mcp.config import Settings
from finding_mcp.framework_detect import detect_frameworks
from finding_mcp.tools_routes import check_auth_coverage, map_routes


@pytest.fixture
def express_settings(tmp_path: Path) -> Settings:
    proj = tmp_path / "express_app"
    proj.mkdir()
    (proj / "package.json").write_text(
        '{"dependencies": {"express": "^4.18.0"}}',
        encoding="utf-8",
    )
    (proj / "app.js").write_text(
        """\
const express = require('express');
const app = express();

app.use(cors);
app.use('/api', logger);

app.get('/public', publicHandler);
app.post('/login', loginHandler);
app.get('/dashboard', authMiddleware, dashboardHandler);
app.put('/users/:id', authMiddleware, verifyToken, updateUser);
app.delete('/admin', requireAuth, deleteAll);
""",
        encoding="utf-8",
    )
    cache = tmp_path / "cache"
    cache.mkdir()
    return Settings(project_root=proj, cache_dir=cache)


@pytest.fixture
def spring_settings(tmp_path: Path) -> Settings:
    proj = tmp_path / "spring_app"
    proj.mkdir()
    (proj / "pom.xml").write_text(
        "<project><dependency>spring-boot-starter-web</dependency></project>",
        encoding="utf-8",
    )
    src = proj / "src"
    src.mkdir()
    (src / "UserController.java").write_text(
        """\
package com.example;

import org.springframework.web.bind.annotation.*;
import org.springframework.security.access.prepost.PreAuthorize;

@RestController
@RequestMapping("/api/users")
public class UserController {

    @GetMapping("/list")
    public List<User> listUsers() {
        return userService.findAll();
    }

    @PostMapping("/create")
    @PreAuthorize("hasRole('ADMIN')")
    public User createUser() {
        return userService.create();
    }

    @DeleteMapping("/{id}")
    public void deleteUser() {
        userService.delete();
    }
}
""",
        encoding="utf-8",
    )
    cache = tmp_path / "cache"
    cache.mkdir()
    return Settings(project_root=proj, cache_dir=cache)


@pytest.fixture
def empty_settings(tmp_path: Path) -> Settings:
    proj = tmp_path / "empty"
    proj.mkdir()
    cache = tmp_path / "cache"
    cache.mkdir()
    return Settings(project_root=proj, cache_dir=cache)


# --- Framework detection ---


def test_detect_express(express_settings: Settings) -> None:
    detections = detect_frameworks(express_settings.project_root)
    frameworks = {d.framework for d in detections}
    assert "express" in frameworks


def test_detect_spring(spring_settings: Settings) -> None:
    detections = detect_frameworks(spring_settings.project_root)
    frameworks = {d.framework for d in detections}
    assert "spring" in frameworks


def test_detect_empty(empty_settings: Settings) -> None:
    detections = detect_frameworks(empty_settings.project_root)
    assert detections == []


# --- Express route extraction ---


def test_express_routes(express_settings: Settings) -> None:
    result = map_routes(express_settings, framework="express")
    assert result.total_routes == 5
    paths = {r.path for r in result.routes}
    assert "/public" in paths
    assert "/dashboard" in paths
    assert "/users/:id" in paths
    assert "/admin" in paths


def test_express_middleware(express_settings: Settings) -> None:
    result = map_routes(express_settings, framework="express")
    dashboard = [r for r in result.routes if r.path == "/dashboard"][0]
    assert "authMiddleware" in dashboard.middleware

    users = [r for r in result.routes if r.path == "/users/:id"][0]
    assert "authMiddleware" in users.middleware
    assert "verifyToken" in users.middleware


def test_express_global_middleware(express_settings: Settings) -> None:
    result = map_routes(express_settings, framework="express")
    assert "cors" in result.global_middleware


def test_express_methods(express_settings: Settings) -> None:
    result = map_routes(express_settings, framework="express")
    method_map = {r.path: r.http_method for r in result.routes}
    assert method_map["/public"] == "GET"
    assert method_map["/login"] == "POST"
    assert method_map["/users/:id"] == "PUT"
    assert method_map["/admin"] == "DELETE"


# --- Spring route extraction ---


def test_spring_routes(spring_settings: Settings) -> None:
    result = map_routes(spring_settings, framework="spring")
    assert result.total_routes == 3
    paths = {r.path for r in result.routes}
    assert "/api/users/list" in paths
    assert "/api/users/create" in paths


def test_spring_class_prefix(spring_settings: Settings) -> None:
    result = map_routes(spring_settings, framework="spring")
    for route in result.routes:
        assert route.class_prefix == "/api/users"


def test_spring_auth_annotations(spring_settings: Settings) -> None:
    result = map_routes(spring_settings, framework="spring")
    create = [r for r in result.routes if "/create" in r.path][0]
    assert create.has_auth_middleware is True
    assert "PreAuthorize" in create.middleware


def test_spring_methods(spring_settings: Settings) -> None:
    result = map_routes(spring_settings, framework="spring")
    method_map = {r.path: r.http_method for r in result.routes}
    assert method_map["/api/users/list"] == "GET"
    assert method_map["/api/users/create"] == "POST"


# --- Auth coverage ---


def test_auth_coverage_express(express_settings: Settings) -> None:
    result = check_auth_coverage(express_settings, framework="express")
    assert result.total_routes == 5
    assert result.unprotected_count > 0
    unprotected_paths = {r.path for r in result.unprotected_routes}
    assert "/public" in unprotected_paths
    assert "/login" in unprotected_paths


def test_auth_coverage_spring(spring_settings: Settings) -> None:
    result = check_auth_coverage(spring_settings, framework="spring")
    assert result.total_routes == 3
    assert result.protected_count >= 1
    unprotected_paths = {r.path for r in result.unprotected_routes}
    assert "/api/users/list" in unprotected_paths


def test_auth_coverage_custom_patterns(express_settings: Settings) -> None:
    result = check_auth_coverage(
        express_settings,
        framework="express",
        auth_patterns=["authMiddleware"],
    )
    protected_paths = {
        r.path for r in result.unprotected_routes
    }
    assert "/public" in protected_paths
    assert "/dashboard" not in protected_paths


# --- Auto-detection ---


def test_auto_detect_routes(express_settings: Settings) -> None:
    result = map_routes(express_settings)
    assert result.total_routes == 5
    assert any(d.framework == "express" for d in result.frameworks_detected)
