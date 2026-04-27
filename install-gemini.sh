#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SERVER_NAME="finding-mcp"
SCOPE="user"

usage() {
    cat <<EOF
Usage: ./install-gemini.sh <target-repo> [options]

Register finding-mcp as a Gemini CLI MCP server.

Arguments:
  <target-repo>    Path to the repository to analyze

Options:
  -s, --scope      Registration scope: user (default) or project
  -h, --help       Show this help

Examples:
  ./install-gemini.sh /path/to/target
  ./install-gemini.sh . --scope project
  ./install-gemini.sh ~/repos/my-app -s project
EOF
    exit "${1:-0}"
}

# --- parse args ---
TARGET=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        -s|--scope)  SCOPE="$2"; shift 2 ;;
        -h|--help)   usage 0 ;;
        -*)          echo "Unknown option: $1" >&2; usage 1 ;;
        *)           TARGET="$1"; shift ;;
    esac
done

[[ -z "$TARGET" ]] && { echo "Error: target repository path is required." >&2; echo ""; usage 1; }

RESOLVED="$(cd "$TARGET" 2>/dev/null && pwd)" || { echo "Error: directory not found: $TARGET" >&2; exit 1; }
TARGET="$RESOLVED"

# --- check dependencies ---
missing=()
command -v python3 &>/dev/null || missing+=("python3")

if [[ ${#missing[@]} -gt 0 ]]; then
    echo "Error: missing required tools: ${missing[*]}" >&2
    exit 1
fi

# --- determine settings.json path ---
if [[ "$SCOPE" == "project" ]]; then
    SETTINGS_DIR=".gemini"
else
    SETTINGS_DIR="$HOME/.gemini"
fi

mkdir -p "$SETTINGS_DIR"
SETTINGS_FILE="$SETTINGS_DIR/settings.json"

# --- read or create settings.json ---
if [[ -f "$SETTINGS_FILE" ]]; then
    SETTINGS=$(cat "$SETTINGS_FILE")
else
    SETTINGS='{}'
fi

# --- update mcpServers entry via python (available since we require python3) ---
UPDATED=$(python3 -c "
import json, sys

settings = json.loads(sys.argv[1])
settings.setdefault('mcpServers', {})
settings['mcpServers']['$SERVER_NAME'] = {
    'command': '$SCRIPT_DIR/run.sh',
    'args': ['$TARGET'],
    'timeout': 30000
}
print(json.dumps(settings, indent=2, ensure_ascii=False))
" "$SETTINGS")

echo "$UPDATED" > "$SETTINGS_FILE"

echo "Registered $SERVER_NAME for Gemini CLI."
echo "  Target:   $TARGET"
echo "  Scope:    $SCOPE"
echo "  Config:   $SETTINGS_FILE"
echo ""
echo "Done! The venv will be created automatically on first MCP call."
