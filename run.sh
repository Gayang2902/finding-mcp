#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"

# Auto-bootstrap: create venv and install if missing
if [ ! -d "$VENV_DIR" ]; then
    echo "[finding-mcp] First run — setting up environment..." >&2
    if command -v uv &>/dev/null; then
        uv venv "$VENV_DIR" >&2
        uv pip install -e "$SCRIPT_DIR" --python "$VENV_DIR/bin/python" >&2
    else
        python3 -m venv "$VENV_DIR" >&2
        "$VENV_DIR/bin/pip" install -q -e "$SCRIPT_DIR" >&2
    fi
    echo "[finding-mcp] Setup complete." >&2
fi

exec "$VENV_DIR/bin/python" -m finding_mcp "$@"
