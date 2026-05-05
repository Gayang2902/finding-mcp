"""MCP server — 20 security analysis tools over stdio or SSE.

IMPORTANT: stdio transport reserves stdout exclusively for JSON-RPC.
All logging and diagnostics MUST go to stderr. Any non-JSON byte on
stdout will break the MCP protocol and cause "Connection closed" errors.
"""

from __future__ import annotations

import io
import logging
import os
import sys

# Force logging to stderr BEFORE importing anything that might configure handlers.
logging.basicConfig(
    level=logging.INFO,
    stream=sys.stderr,
    format="[%(asctime)s] %(levelname)s %(name)s: %(message)s",
    force=True,
)
log = logging.getLogger("finding-mcp")

from mcp.server.fastmcp import FastMCP  # noqa: E402, I001

from .tools import hunting as tools_hunting, meta as tools_meta, routes as tools_routes  # noqa: E402
from .tools import search as tools_search, structure as tools_structure  # noqa: E402
from .tools import symbols as tools_symbols, taint as tools_taint  # noqa: E402
from .config import Settings, load_settings  # noqa: E402


def _guard_stdout() -> None:
    """Protect stdout from non-JSON-RPC writes in stdio transport mode.

    1. Reconfigures all logging handlers to stderr (in case libraries added stdout handlers).
    2. Captures Python warnings through the logging system (→ stderr).
    3. Redirects fd 1 to stderr so C-extension output can't corrupt the protocol.
    4. Gives sys.stdout the saved real stdout fd for MCP's JSON-RPC transport.

    Gracefully degrades if fd manipulation fails (e.g., non-standard MCP hosts
    that don't provide real file descriptors).
    """
    root = logging.getLogger()
    for h in root.handlers[:]:
        root.removeHandler(h)
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s %(name)s: %(message)s"))
    root.addHandler(handler)
    root.setLevel(logging.INFO)

    logging.captureWarnings(True)

    try:
        real_stdout_fd = os.dup(sys.stdout.fileno())
        os.dup2(sys.stderr.fileno(), 1)
        sys.stdout = io.TextIOWrapper(
            io.BufferedWriter(io.FileIO(real_stdout_fd, mode="w", closefd=True)),
            write_through=True,
        )
    except (OSError, io.UnsupportedOperation):
        # Some MCP hosts don't provide real fds (e.g., Windows named pipes).
        # Fall back to just ensuring logging goes to stderr (already done above).
        log.debug("fd-level stdout guard skipped — non-standard stdio")


def _build_server(settings: Settings) -> FastMCP:
    mcp = FastMCP("finding-mcp")

    @mcp.tool(name="set_project_root")
    def _set_project_root(path: str) -> dict:
        """Set or switch the target repository for analysis.

        Call this before any other tool if the server was started without a
        fixed project root, or to switch to a different project mid-session.

        Args:
            path: Absolute or relative path to the target repository.
                  Relative paths are resolved against the current project root.
        """
        from pathlib import Path as P
        p = P(path).expanduser()
        if not p.is_absolute() and settings.project_root:
            p = settings.project_root / p
        resolved = p.resolve()
        if not resolved.is_dir():
            return {"error": f"Not a directory: {path}"}
        settings.project_root = resolved
        log.info("Project root set to: %s", resolved)
        return {
            "project_root": str(resolved),
            "message": f"Now analyzing: {resolved.name}",
        }

    tools_symbols.register(mcp, settings)
    tools_structure.register(mcp, settings)
    tools_search.register(mcp, settings)
    tools_meta.register(mcp, settings)
    tools_taint.register(mcp, settings)
    tools_routes.register(mcp, settings)
    tools_hunting.register(mcp, settings)
    return mcp


def main() -> None:
    settings = load_settings()

    # Guard stdout BEFORE any log output in stdio mode — some MCP hosts
    # start reading stdout immediately and any non-JSON bytes cause failure.
    if settings.transport == "stdio":
        _guard_stdout()

    log.info("Starting Finding MCP")
    log.info("  project_root: %s", settings.project_root)
    log.info("  transport:    %s", settings.transport)
    if settings.transport != "stdio":
        log.info("  listen:       %s:%d", settings.host, settings.port)

    mcp = _build_server(settings)

    if settings.transport == "sse":
        mcp.run(transport="sse", host=settings.host, port=settings.port)
    elif settings.transport == "streamable-http":
        mcp.run(transport="streamable-http", host=settings.host, port=settings.port)
    else:
        mcp.run()


if __name__ == "__main__":
    main()
