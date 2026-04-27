#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SERVER_NAME="finding-mcp"

echo "=== $SERVER_NAME installer ==="

SCOPE="${1:-user}"
TARGET="${2:-}"

echo "Registering MCP server (scope=$SCOPE)..."

claude mcp remove "$SERVER_NAME" -s "$SCOPE" 2>/dev/null || true

if [ -n "$TARGET" ]; then
    claude mcp add "$SERVER_NAME" -s "$SCOPE" -- "$SCRIPT_DIR/run.sh" "$TARGET"
else
    echo ""
    echo "Usage:"
    echo "  ./install.sh user /path/to/target   # user scope"
    echo "  ./install.sh project /path/to/target # project scope"
    echo ""
    echo "Or register manually:"
    echo "  claude mcp add $SERVER_NAME -- $SCRIPT_DIR/run.sh /path/to/target"
    exit 1
fi

echo ""
echo "Done! $SERVER_NAME registered."
echo "  Target: $TARGET"
echo "  Scope:  $SCOPE"
echo ""
echo "The venv will be created automatically on first run."
