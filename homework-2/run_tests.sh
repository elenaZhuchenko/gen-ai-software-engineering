#!/usr/bin/env bash
# run_tests.sh — Run the full test suite and generate coverage reports.
#
# Usage:
#   ./run_tests.sh              # full suite + HTML + terminal coverage
#   ./run_tests.sh --fast       # skip performance tests
#   ./run_tests.sh --unit       # unit tests only (no integration/performance)
#   ./run_tests.sh --file <name># run a single test file
#
# Reports are written to:
#   src/htmlcov/index.html      — HTML coverage report (open in browser)
#   src/.coverage               — raw coverage data

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="$SCRIPT_DIR/src"
HTMLCOV_DIR="$SRC_DIR/htmlcov"
REPORT_DIR="$SCRIPT_DIR/docs/screenshots"

# ─── Colour helpers ────────────────────────────────────────────────────────
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

# ─── Parse arguments ──────────────────────────────────────────────────────
MODE="full"
SINGLE_FILE=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --fast)   MODE="fast";   shift ;;
        --unit)   MODE="unit";   shift ;;
        --file)   MODE="file";   SINGLE_FILE="$2"; shift 2 ;;
        --help|-h)
            grep '^#' "$0" | head -20 | sed 's/^# \{0,2\}//'
            exit 0
            ;;
        *) error "Unknown option: $1"; exit 1 ;;
    esac
done

# ─── Prerequisites ────────────────────────────────────────────────────────
if ! command -v python &>/dev/null && ! command -v python3 &>/dev/null; then
    error "Python not found. Install Python 3.11+ and try again."
    exit 1
fi

PYTHON=$(command -v python3 || command -v python)

if ! "$PYTHON" -c "import pytest" &>/dev/null; then
    warn "pytest not found — installing dependencies from requirements.txt …"
    "$PYTHON" -m pip install -r "$SRC_DIR/requirements.txt" --quiet
fi

# ─── Build pytest command ─────────────────────────────────────────────────
cd "$SRC_DIR"

PYTEST_ARGS=(
    --cov=.
    --cov-report=term-missing
    "--cov-report=html:$HTMLCOV_DIR"
    "--cov-report=xml:$SCRIPT_DIR/coverage.xml"
    --cov-fail-under=85
    -v
    --tb=short
)

case "$MODE" in
    full)
        info "Running FULL test suite …"
        PYTEST_ARGS+=(../src/tests)
        ;;
    fast)
        info "Running FAST suite (skipping performance tests) …"
        PYTEST_ARGS+=(--ignore=tests/test_performance.py ../src/tests)
        ;;
    unit)
        info "Running UNIT tests only …"
        PYTEST_ARGS+=(
            tests/test_ticket_api.py
            tests/test_ticket_model.py
            tests/test_import_csv.py
            tests/test_import_json.py
            tests/test_import_xml.py
            tests/test_categorization.py
        )
        ;;
    file)
        info "Running single file: tests/$SINGLE_FILE …"
        PYTEST_ARGS+=("tests/$SINGLE_FILE")
        ;;
esac

echo ""
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BOLD}  Intelligent Customer Support System — Test Runner${NC}"
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# ─── Run tests ────────────────────────────────────────────────────────────
set +e
"$PYTHON" -m pytest "${PYTEST_ARGS[@]}"
EXIT_CODE=$?
set -e

echo ""
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if [[ $EXIT_CODE -eq 0 ]]; then
    success "All tests passed and coverage ≥ 85 %"
else
    error "Tests failed or coverage below 85 % (exit code: $EXIT_CODE)"
fi

# ─── Report locations ─────────────────────────────────────────────────────
echo ""
info "Coverage reports:"
echo "   Terminal : printed above (--cov-report=term-missing)"
echo "   HTML     : file://$HTMLCOV_DIR/index.html"
echo "   XML      : $SCRIPT_DIR/coverage.xml"
echo ""

exit $EXIT_CODE
