#!/usr/bin/env bash
# run_server.sh — Start the Support Ticket API server and seed it with demo data.
#
# Usage:
#   ./run_server.sh              # start server + load seed data
#   ./run_server.sh --no-seed    # start server only, no sample data
#   ./run_server.sh --seed-only  # load seed data into a running server
#   ./run_server.sh --port 9000  # custom port (default: 8000)
#   ./run_server.sh --host 0.0.0.0  # custom host (default: 127.0.0.1)
#
# After startup the API is available at:
#   http://HOST:PORT/docs      — Swagger UI
#   http://HOST:PORT/redoc     — ReDoc
#   http://HOST:PORT/health    — health check

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="$SCRIPT_DIR/src"
SEED_FILE="$SCRIPT_DIR/demo/seed_data.json"

HOST="127.0.0.1"
PORT="8000"
SEED=true
SEED_ONLY=false

# ─── Colours ───────────────────────────────────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'

info()    { echo -e "${CYAN}[INFO]${NC}  $*"; }
success() { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*" >&2; }
step()    { echo -e "\n${BOLD}${BLUE}▶ $*${NC}"; }

# ─── Parse arguments ──────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case "$1" in
        --no-seed)   SEED=false;              shift ;;
        --seed-only) SEED_ONLY=true;          shift ;;
        --port)      PORT="$2";               shift 2 ;;
        --host)      HOST="$2";               shift 2 ;;
        --help|-h)
            grep '^#' "$0" | head -20 | sed 's/^# \{0,2\}//'
            exit 0
            ;;
        *) error "Unknown option: $1"; exit 1 ;;
    esac
done

BASE_URL="http://$HOST:$PORT"

# ─── Python detection ─────────────────────────────────────────────────────
PYTHON=$(command -v python3 2>/dev/null || command -v python 2>/dev/null || true)
if [[ -z "$PYTHON" ]]; then
    error "Python not found. Install Python 3.11+ and try again."
    exit 1
fi

# ─── Dependency check ─────────────────────────────────────────────────────
if ! "$PYTHON" -c "import fastapi, uvicorn" &>/dev/null; then
    step "Installing dependencies …"
    "$PYTHON" -m pip install -r "$SRC_DIR/requirements.txt" --quiet
    success "Dependencies installed."
fi

# ─── Seed helper function ─────────────────────────────────────────────────
seed_data() {
    step "Loading seed data into the running server …"

    "$PYTHON" - <<PYEOF
import json, sys, time, urllib.request, urllib.error

base = "$BASE_URL"
seed_file = "$SEED_FILE"

# Wait for the server to be ready (max 15 s)
for attempt in range(30):
    try:
        urllib.request.urlopen(f"{base}/health", timeout=2)
        break
    except Exception:
        time.sleep(0.5)
else:
    print("[ERROR] Server did not become ready in 15 seconds.", file=sys.stderr)
    sys.exit(1)

# Read seed data
with open(seed_file) as f:
    tickets = json.load(f)

# POST each ticket individually so we can track per-ticket results
created, failed = [], []
for t in tickets:
    body = json.dumps(t).encode()
    # auto_classify is a body field, not a query param
    if "auto_classify" not in t:
        t = {**t, "auto_classify": True}
    body = json.dumps(t).encode()
    req = urllib.request.Request(
        f"{base}/tickets",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as r:
            data = json.loads(r.read())
            created.append(data)
    except urllib.error.HTTPError as e:
        body_err = e.read().decode()
        failed.append({"subject": t.get("subject"), "error": body_err})

total = len(tickets)
ok = len(created)
ko = len(failed)

print(f"\n  Seed results: {ok}/{total} tickets created, {ko} failed")
if failed:
    for f in failed:
        print(f"    ✗ {f['subject']}: {f['error'][:80]}")

# Print category breakdown
from collections import Counter
cats = Counter(t.get("category", "other") for t in created)
print("\n  Category breakdown:")
for cat, count in sorted(cats.items(), key=lambda x: -x[1]):
    bar = "█" * count
    print(f"    {cat:<20} {bar} ({count})")

pris = Counter(t.get("priority", "medium") for t in created)
print("\n  Priority breakdown:")
order = ["urgent", "high", "medium", "low"]
for pri in order:
    count = pris.get(pri, 0)
    bar = "█" * count
    print(f"    {pri:<20} {bar} ({count})")
PYEOF
}

# ─── Seed-only mode ───────────────────────────────────────────────────────
if [[ "$SEED_ONLY" == "true" ]]; then
    seed_data
    success "Seed data loaded."
    exit 0
fi

# ─── Banner ───────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BOLD}  Intelligent Customer Support System${NC}"
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# ─── Start server ─────────────────────────────────────────────────────────
step "Starting FastAPI server on $BASE_URL …"

# If seeding, start uvicorn in the background first
if [[ "$SEED" == "true" ]]; then
    (
        cd "$SRC_DIR"
        exec "$PYTHON" -m uvicorn main:app \
            --host "$HOST" \
            --port "$PORT" \
            --reload \
            --log-level info
    ) &
    SERVER_PID=$!

    # Register cleanup on exit
    cleanup() {
        echo ""
        info "Shutting down server (PID $SERVER_PID) …"
        kill "$SERVER_PID" 2>/dev/null || true
        wait "$SERVER_PID" 2>/dev/null || true
        success "Server stopped."
    }
    trap cleanup EXIT INT TERM

    # Wait for health endpoint
    info "Waiting for server to be ready …"
    READY=false
    for i in $(seq 1 30); do
        if "$PYTHON" -c "
import urllib.request, sys
try:
    urllib.request.urlopen('$BASE_URL/health', timeout=1)
except Exception:
    sys.exit(1)
" 2>/dev/null; then
            READY=true
            break
        fi
        sleep 0.5
    done

    if [[ "$READY" != "true" ]]; then
        error "Server did not start within 15 seconds."
        exit 1
    fi

    success "Server is up at ${BOLD}$BASE_URL${NC}"

    # Seed data
    seed_data

    echo ""
    echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "  ${GREEN}${BOLD}Server ready with sample data!${NC}"
    echo -e "  Swagger UI  : ${CYAN}$BASE_URL/docs${NC}"
    echo -e "  ReDoc       : ${CYAN}$BASE_URL/redoc${NC}"
    echo -e "  Tickets API : ${CYAN}$BASE_URL/tickets${NC}"
    echo -e "  Health      : ${CYAN}$BASE_URL/health${NC}"
    echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${DIM}  Press Ctrl+C to stop the server${NC}"
    echo ""

    # Keep the script running (server is in background)
    wait "$SERVER_PID"

else
    # No seed — run uvicorn in foreground directly
    echo -e "  Swagger UI  : ${CYAN}$BASE_URL/docs${NC}"
    echo -e "  ReDoc       : ${CYAN}$BASE_URL/redoc${NC}"
    echo -e "  Tickets API : ${CYAN}$BASE_URL/tickets${NC}"
    echo -e "${DIM}  Press Ctrl+C to stop${NC}"
    echo ""

    cd "$SRC_DIR"
    exec "$PYTHON" -m uvicorn main:app \
        --host "$HOST" \
        --port "$PORT" \
        --reload \
        --log-level info
fi
