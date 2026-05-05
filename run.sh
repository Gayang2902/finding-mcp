#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"

die() { echo "[finding-mcp] ERROR: $*" >&2; exit 1; }

# --- PATH augmentation: MCP hosts often spawn with minimal PATH ---
for p in /opt/homebrew/bin /usr/local/bin "$HOME/.local/bin"; do
    [[ -d "$p" ]] && [[ ":$PATH:" != *":$p:"* ]] && PATH="$p:$PATH"
done
export PATH

# --- consistent locale for subprocess output parsing ---
export LC_ALL="${LC_ALL:-en_US.UTF-8}"

# --- pre-flight: python3 must exist ---
command -v python3 &>/dev/null || die "python3 not found. Install Python 3.10+."

# --- auto-bootstrap: create venv and install if missing ---
if [ ! -d "$VENV_DIR" ]; then
    echo "[finding-mcp] First run — setting up environment..." >&2

    if command -v uv &>/dev/null; then
        uv venv "$VENV_DIR" >&2 || die "Failed to create venv with uv."
        uv pip install -e "$SCRIPT_DIR" --python "$VENV_DIR/bin/python" >&2 || die "Failed to install package with uv."
    else
        python3 -m venv "$VENV_DIR" >&2 || die "Failed to create venv."
        "$VENV_DIR/bin/pip" install -q -e "$SCRIPT_DIR" >&2 || die "Failed to install package with pip."
    fi

    # --- optional dependency hints ---
    missing=()
    command -v ctags &>/dev/null || missing+=("universal-ctags")
    command -v rg    &>/dev/null || missing+=("ripgrep")
    if [[ ${#missing[@]} -gt 0 ]]; then
        echo "[finding-mcp] Warning: missing recommended tools: ${missing[*]}" >&2
        echo "[finding-mcp]   brew install ${missing[*]}  # macOS" >&2
        echo "[finding-mcp]   apt install ${missing[*]}   # Debian/Ubuntu" >&2
    fi

    echo "[finding-mcp] Setup complete." >&2
fi

# --- sanity check: venv python and package must exist ---
[[ -x "$VENV_DIR/bin/python" ]] || die "venv python not found at $VENV_DIR/bin/python. Remove .venv and retry."
"$VENV_DIR/bin/python" -c "import finding_mcp" 2>/dev/null || die "finding_mcp package not installed. Remove .venv and retry."

exec "$VENV_DIR/bin/python" -m finding_mcp "$@"
