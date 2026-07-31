#!/usr/bin/env bash
# run-mcp.sh — helper to test all 4 MCP servers from terminal.
# Usage:
#   cd homework-5/custom-mcp-server
#   source .venv/bin/activate
#   cd ..
#   bash run-mcp.sh [github|filesystem|notion|custom] [list|call] [args...]
#
# Or just:   source .env && bash run-mcp.sh filesystem list

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Load .env if it exists and vars are not already set
if [[ -f "$SCRIPT_DIR/.env" ]]; then
  set -a
  # shellcheck source=/dev/null
  source "$SCRIPT_DIR/.env"
  set +a
fi

GITHUB_PAT="${GITHUB_PAT:-}"
NOTION_TOKEN="${NOTION_TOKEN:-}"

FS_PATH="$(cd "$SCRIPT_DIR/.." && pwd)"
CUSTOM_SERVER="$SCRIPT_DIR/custom-mcp-server/server.py"
FASTMCP="$SCRIPT_DIR/custom-mcp-server/.venv/bin/fastmcp"

SERVER="${1:-}"
ACTION="${2:-list}"
shift 2 2>/dev/null || true
EXTRA_ARGS=("$@")

case "$SERVER" in
  github)
    [[ -z "$GITHUB_PAT" ]] && { echo "GITHUB_PAT is not set. Add it to homework-5/.env"; exit 1; }
    if [[ "$ACTION" == "list" ]]; then
      "$FASTMCP" list \
        --server-spec "https://api.githubcopilot.com/mcp/" \
        --auth "Bearer $GITHUB_PAT"
    else
      "$FASTMCP" call \
        --server-spec "https://api.githubcopilot.com/mcp/" \
        --auth "Bearer $GITHUB_PAT" \
        --target list_pull_requests \
        owner=elenaZhuchenko repo=gen-ai-software-engineering state=all per_page=5
    fi
    ;;

  filesystem)
    if [[ "$ACTION" == "list" ]]; then
      "$FASTMCP" list \
        --command "npx -y @modelcontextprotocol/server-filesystem $FS_PATH"
    else
      "$FASTMCP" call \
        --command "npx -y @modelcontextprotocol/server-filesystem $FS_PATH" \
        --target "list_directory" \
        --input-json "{\"path\":\"$FS_PATH/homework-5\"}"
    fi
    ;;

  notion)
    [[ -z "$NOTION_TOKEN" ]] && { echo "NOTION_TOKEN is not set. Add it to homework-5/.env"; exit 1; }
    if [[ "$ACTION" == "list" ]]; then
      NOTION_TOKEN="$NOTION_TOKEN" "$FASTMCP" list \
        --command "npx -y @notionhq/notion-mcp-server"
    else
      NOTION_TOKEN="$NOTION_TOKEN" "$FASTMCP" call \
        --command "npx -y @notionhq/notion-mcp-server" \
        --target "API-post-search" \
        --input-json '{"query":"Bug","filter":{"property":"object","value":"page"}}'
    fi
    ;;

  custom)
    if [[ "$ACTION" == "list" ]]; then
      "$FASTMCP" list "$CUSTOM_SERVER" --resources
    else
      WORD_COUNT="${EXTRA_ARGS[0]:-15}"
      "$FASTMCP" call "$CUSTOM_SERVER" --target "read" \
        --input-json "{\"word_count\":$WORD_COUNT}"
    fi
    ;;

  *)
    echo "Usage: bash run-mcp.sh <github|filesystem|notion|custom> [list|call] [word_count]"
    echo ""
    echo "Examples:"
    echo "  bash run-mcp.sh github call"
    echo "  bash run-mcp.sh filesystem call"
    echo "  bash run-mcp.sh notion call"
    echo "  bash run-mcp.sh custom call 15"
    exit 1
    ;;
esac
