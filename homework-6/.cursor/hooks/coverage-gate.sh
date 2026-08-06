#!/usr/bin/env bash
# Cursor beforeShellExecution hook — coverage gate.
# Fires when the Cursor agent attempts to run "git push".
# Blocks the push by returning a deny permission response if coverage < 80%.

set -euo pipefail

HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HW6_DIR="$(cd "$HOOK_DIR/../.." && pwd)"
VENV_PYTHON="$HW6_DIR/.venv/bin/python"
MIN_COVERAGE=80

cd "$HW6_DIR"

if "$VENV_PYTHON" -m pytest \
    --cov=agents --cov=integrator \
    --cov-fail-under="$MIN_COVERAGE" \
    --cov-report=term-missing \
    -q 2>/dev/null; then

    echo '{"permission": "allow"}'
    exit 0
fi

# Coverage below threshold — deny the push
cat <<'EOF'
{
  "permission": "deny",
  "user_message": "🚫 Push blocked — test coverage is below 80%. Run pytest --cov and fix coverage before pushing.",
  "agent_message": "The coverage gate hook detected that unit-test coverage is below 80%. Fix the failing tests or add coverage, then retry git push."
}
EOF
exit 0
