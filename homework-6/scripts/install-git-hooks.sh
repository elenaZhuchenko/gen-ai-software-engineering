#!/usr/bin/env bash
# Install the homework-6 git hooks for this repository.
# Run once from the repository root or from homework-6/.
#
# NOTE — repo-wide effect: git only supports one hooks directory per repo
# (core.hooksPath), and this is a monorepo of independent homeworks. This
# script will therefore point core.hooksPath at homework-6's hooks/ for
# every push in the repo, not just homework-6 pushes. The installed
# pre-push hook is scoped internally to only run the coverage check when
# the push actually touches homework-6/ (see scripts/git-hooks/pre-push),
# so pushing other homeworks' branches is unaffected — but if another
# homework later installs its own hooksPath, the two would conflict and
# only the most recently installed one would take effect.

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
HOOKS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/git-hooks" && pwd)"

existing_hooks_path="$(git config --get core.hooksPath || true)"
if [ -n "$existing_hooks_path" ] && [ "$existing_hooks_path" != "$HOOKS_DIR" ]; then
    echo "⚠️  core.hooksPath is already set to: $existing_hooks_path"
    echo "   Overwriting it with homework-6's hooks dir would disable those hooks."
    echo "   Re-run with FORCE=1 to overwrite anyway, e.g.: FORCE=1 bash $0"
    if [ "${FORCE:-0}" != "1" ]; then
        exit 1
    fi
fi

echo "Installing hooks from: $HOOKS_DIR"
echo "Repository root:       $REPO_ROOT"

# Use core.hooksPath so the hook directory is repo-wide but points to hw6 hooks.
git config core.hooksPath "$HOOKS_DIR"
chmod +x "$HOOKS_DIR/pre-push"

echo "✅ Git hooks installed. pre-push hook will enforce coverage ≥ 80% for pushes"
echo "   that touch homework-6/ (other homeworks' pushes are not affected)."
echo "   Run 'git config --unset core.hooksPath' to remove."
