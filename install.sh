#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SERVER_NAME="finding-mcp"
SCOPE="user"

usage() {
    cat <<EOF
Usage: ./install.sh <target-repo> [options]

Register finding-mcp as a Claude Code MCP server.

Arguments:
  <target-repo>    Path to the repository to analyze

Options:
  -s, --scope      Registration scope: user (default) or project
  -h, --help       Show this help

Examples:
  ./install.sh /path/to/target
  ./install.sh . --scope project
  ./install.sh ~/repos/my-app -s project
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
command -v claude  &>/dev/null || missing+=("claude (Claude Code CLI)")

if [[ ${#missing[@]} -gt 0 ]]; then
    echo "Error: missing required tools: ${missing[*]}" >&2
    exit 1
fi

# --- register ---
echo "Registering $SERVER_NAME..."
echo "  Target: $TARGET"
echo "  Scope:  $SCOPE"
echo ""

claude mcp remove "$SERVER_NAME" -s "$SCOPE" 2>/dev/null || true
claude mcp add "$SERVER_NAME" -s "$SCOPE" -- "$SCRIPT_DIR/run.sh" "$TARGET"

echo ""
echo "Done! The venv will be created automatically on first MCP call."
