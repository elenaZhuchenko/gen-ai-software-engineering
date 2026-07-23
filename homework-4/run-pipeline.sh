#!/usr/bin/env bash
# run-pipeline.sh — Single-command entry point for the 4-agent pipeline.
#
# Usage:
#   ./run-pipeline.sh                 # full run (requires CURSOR_API_KEY)
#   ./run-pipeline.sh --dry-run       # validate config only, no API calls
#   ./run-pipeline.sh --from-stage 3  # restart from stage 3
#
# Environment:
#   CURSOR_API_KEY  — required for real runs (get from cursor.com/dashboard)
#
# All arguments are forwarded to run-pipeline.py.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ──────────────────────────────────────────────────────────────────────────────
# Colour helpers
# ──────────────────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

info()    { echo -e "${CYAN}[INFO]${NC}  $*"; }
success() { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*"; }

# ──────────────────────────────────────────────────────────────────────────────
# Find Python 3
# ──────────────────────────────────────────────────────────────────────────────
PYTHON=""
for candidate in python3 python3.12 python3.11 python3.10 python; do
    if command -v "$candidate" &>/dev/null; then
        version=$("$candidate" -c "import sys; print(sys.version_info[:2])" 2>/dev/null)
        if [[ "$version" > "(3, 8)" ]]; then
            PYTHON="$candidate"
            break
        fi
    fi
done

if [[ -z "$PYTHON" ]]; then
    error "Python 3.9+ not found. Install it and try again."
    exit 1
fi

info "Using Python: $($PYTHON --version)"

# ──────────────────────────────────────────────────────────────────────────────
# Check dependencies
# ──────────────────────────────────────────────────────────────────────────────
if ! "$PYTHON" -c "import cursor_sdk" &>/dev/null; then
    warn "cursor-sdk not installed — installing from requirements.txt …"
    "$PYTHON" -m pip install -r "$SCRIPT_DIR/requirements.txt" --quiet
fi

if ! "$PYTHON" -c "import yaml" &>/dev/null; then
    warn "PyYAML not installed — installing …"
    "$PYTHON" -m pip install PyYAML --quiet
fi

# ──────────────────────────────────────────────────────────────────────────────
# Validate API key (unless --dry-run)
# ──────────────────────────────────────────────────────────────────────────────
DRY_RUN=false
for arg in "$@"; do
    [[ "$arg" == "--dry-run" ]] && DRY_RUN=true
done

if [[ "$DRY_RUN" == "false" && -z "${CURSOR_API_KEY:-}" ]]; then
    error "CURSOR_API_KEY is not set."
    echo ""
    echo "  Set it with:"
    echo "    export CURSOR_API_KEY=cursor_..."
    echo ""
    echo "  Get your key at: https://cursor.com/dashboard/integrations"
    echo ""
    echo "  To validate the pipeline configuration without making API calls, run:"
    echo "    ./run-pipeline.sh --dry-run"
    exit 1
fi

# ──────────────────────────────────────────────────────────────────────────────
# Run the pipeline
# ──────────────────────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BOLD}  4-Agent Bug/Security/Test Pipeline${NC}"
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

set +e
"$PYTHON" "$SCRIPT_DIR/run-pipeline.py" "$@"
EXIT_CODE=$?
set -e

echo ""
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if [[ $EXIT_CODE -eq 0 ]]; then
    success "Pipeline finished successfully."
else
    error "Pipeline exited with code $EXIT_CODE."
fi

exit $EXIT_CODE
