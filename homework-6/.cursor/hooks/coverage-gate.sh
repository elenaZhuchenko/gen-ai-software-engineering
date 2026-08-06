#!/usr/bin/env bash
# Cursor beforeShellExecution hook — coverage gate.
# Fires when the Cursor agent attempts to run "git push".
# Blocks the push by returning a deny permission response if coverage < 80%.
#
# Scope: this repo is a monorepo of independent homeworks, and Cursor hooks
# are configured per-.cursor/hooks.json, but "git push" can be run from any
# subfolder for any homework's branch. Only enforce this homework-6 gate
# when the push is actually about homework-6 (current branch name contains
# "homework-6", or the diff against origin/main touches homework-6/) so a
# push for another homework isn't blocked just because homework-6's .venv
# isn't set up.

set -euo pipefail

HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HW6_DIR="$(cd "$HOOK_DIR/../.." && pwd)"
VENV_PYTHON="$HW6_DIR/.venv/bin/python"
MIN_COVERAGE=80

branch="$(cd "$HW6_DIR" && git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")"
changed=""
if command -v git >/dev/null 2>&1; then
    merge_base="$(cd "$HW6_DIR" && git merge-base HEAD origin/main 2>/dev/null || true)"
    if [ -n "$merge_base" ]; then
        changed="$(cd "$HW6_DIR" && git diff --name-only "$merge_base" HEAD -- homework-6/ 2>/dev/null || true)"
    fi
fi

if [[ "$branch" != *homework-6* ]] && [ -z "$changed" ]; then
    echo '{"permission": "allow"}'
    exit 0
fi

if [ ! -x "$VENV_PYTHON" ]; then
    cat <<'EOF'
{
  "permission": "deny",
  "user_message": "🚫 Push blocked — homework-6/.venv not found, cannot verify coverage.",
  "agent_message": "The coverage gate hook could not find homework-6/.venv. Run the setup steps in HOWTORUN.md, then retry git push."
}
EOF
    exit 0
fi

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
