"""Runtime configuration — CLI args > env vars > defaults."""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    project_root: Path
    cache_dir: Path
    transport: str = "stdio"
    host: str = "0.0.0.0"
    port: int = 8080
    max_response_bytes: int = 200_000
    default_limit: int = 50
    max_limit: int = 500
    semgrep_timeout: int = 300
    semgrep_max_findings: int = 1000


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="finding-mcp",
        description="Security-focused code analysis MCP server",
    )
    p.add_argument(
        "project_root",
        nargs="?",
        default=None,
        help="Path to the target repository (or set FINDING_MCP_PROJECT_ROOT)",
    )
    p.add_argument(
        "--project-root",
        dest="project_root_flag",
        default=None,
        help="Path to the target repository (alternative to positional arg)",
    )
    p.add_argument(
        "-t", "--transport",
        choices=["stdio", "sse", "streamable-http"],
        default=None,
        help="MCP transport (default: stdio)",
    )
    p.add_argument(
        "--host",
        default=None,
        help="Host to bind for sse/streamable-http (default: 0.0.0.0)",
    )
    p.add_argument(
        "-p", "--port",
        type=int,
        default=None,
        help="Port for sse/streamable-http (default: 8080)",
    )
    p.add_argument(
        "--cache-dir",
        default=None,
        help="Cache directory (default: ~/.cache/finding-mcp)",
    )
    return p.parse_args(argv)


def _env(key: str, *legacy_keys: str) -> str | None:
    val = os.environ.get(key)
    if val:
        return val
    for lk in legacy_keys:
        val = os.environ.get(lk)
        if val:
            return val
    return None


def load_settings(argv: list[str] | None = None) -> Settings:
    args = parse_args(argv)

    root_str = (
        args.project_root_flag
        or args.project_root
        or _env("FINDING_MCP_PROJECT_ROOT", "CODE_NAVIGATOR_PROJECT_ROOT")
    )
    if not root_str:
        print(
            "Error: project root is required.\n"
            "  finding-mcp /path/to/repo\n"
            "  finding-mcp --project-root /path/to/repo\n"
            "  FINDING_MCP_PROJECT_ROOT=/path/to/repo finding-mcp",
            file=sys.stderr,
        )
        sys.exit(1)

    project_root = Path(root_str).expanduser().resolve()
    if not project_root.is_dir():
        print(f"Error: not a directory: {project_root}", file=sys.stderr)
        sys.exit(1)

    cache_str = args.cache_dir or _env("FINDING_MCP_CACHE_DIR", "CODE_NAVIGATOR_CACHE_DIR")
    if cache_str:
        cache_dir = Path(cache_str).expanduser().resolve()
    else:
        cache_dir = Path.home() / ".cache" / "finding-mcp"
    cache_dir.mkdir(parents=True, exist_ok=True)

    transport = args.transport or _env("FINDING_MCP_TRANSPORT") or "stdio"
    host = args.host or _env("FINDING_MCP_HOST") or "0.0.0.0"
    port = args.port or int(_env("FINDING_MCP_PORT") or "8080")

    semgrep_timeout = int(
        _env("FINDING_MCP_SEMGREP_TIMEOUT", "CODE_NAVIGATOR_SEMGREP_TIMEOUT") or "300"
    )
    semgrep_max_findings = int(
        _env("FINDING_MCP_SEMGREP_MAX_FINDINGS", "CODE_NAVIGATOR_SEMGREP_MAX_FINDINGS") or "1000"
    )

    return Settings(
        project_root=project_root,
        cache_dir=cache_dir,
        transport=transport,
        host=host,
        port=port,
        semgrep_timeout=semgrep_timeout,
        semgrep_max_findings=semgrep_max_findings,
    )
