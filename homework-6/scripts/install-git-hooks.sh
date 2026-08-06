#!/usr/bin/env bash
# Install the homework-6 git hooks for this repository.
# Run once from the repository root or from homework-6/.

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
HOOKS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/git-hooks" && pwd)"

echo "Installing hooks from: $HOOKS_DIR"
echo "Repository root:       $REPO_ROOT"

# Use core.hooksPath so the hook directory is repo-wide but points to hw6 hooks.
git config core.hooksPath "$HOOKS_DIR"
chmod +x "$HOOKS_DIR/pre-push"

echo "✅ Git hooks installed. pre-push hook will enforce coverage ≥ 80%."
echo "   Run 'git config --unset core.hooksPath' to remove."
