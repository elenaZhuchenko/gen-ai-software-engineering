# Claude Code Hooks

Claude Code hooks are shell commands the harness runs at specific points in the agent
lifecycle. They live in `.claude/settings.json` (project) or `~/.claude/settings.json`
(user) — not in `.git/hooks`. Claude does not decide whether to run them; the harness
always does.

Hook input arrives on **stdin as JSON**. Behavior is controlled by the **exit code**:

| Exit code | Effect |
| --- | --- |
| `0` | Success. `stdout` shown in transcript (and fed back to Claude for some events). |
| `2` | Blocking error. `stderr` is fed back to Claude so it can correct itself. |
| other | Non-blocking error. `stderr` shown to the user; execution continues. |

---

## Example 1 — `PostToolUse`: auto-format files after Claude edits them

Runs after every successful `Write`/`Edit`. Keeps the tree formatted without Claude
having to remember to do it.

`.claude/settings.json`

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/format.sh"
          }
        ]
      }
    ]
  }
}
```

`.claude/hooks/format.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail

# PostToolUse payload includes tool_input.file_path
file=$(jq -r '.tool_input.file_path // empty')
[ -z "$file" ] && exit 0
[ -f "$file" ] || exit 0

name=$(basename "$file")

case "$file" in
  *.ts|*.tsx|*.js|*.jsx|*.json|*.css|*.md)
    npx --no-install prettier --write "$file" >/dev/null 2>&1 || true
    echo "✨🧹 Prettier gave $name a spa day — squeaky clean! 🛁"
    ;;
  *.py)
    ruff format "$file" >/dev/null 2>&1 || true
    echo "🐍💅 Ruff manicured $name. Look at those tidy indents! 🎀"
    ;;
  *)
    echo "🤷 No formatter for $name — leaving it as-is. 👀"
    ;;
esac

exit 0
```

`stdout` from a `PostToolUse` hook shows up in the transcript, so every edit gets a
little celebration message.

---

## Example 2 — `PreToolUse`: block dangerous Bash commands

Runs *before* the tool executes. Exit `2` cancels the call and tells Claude why, so it
picks a safer command instead of just failing.

`.claude/settings.json`

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/guard-bash.sh"
          }
        ]
      }
    ]
  }
}
```

`.claude/hooks/guard-bash.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail

cmd=$(jq -r '.tool_input.command // empty')

deny() {
  echo "🚨🙅 NOPE! The bash bouncer says: $1 — try again, but nicer. 🧯" >&2
  exit 2   # exit 2 => Claude sees stderr and must adjust
}

case "$cmd" in
  *"rm -rf /"*)         deny "💀 you just tried to delete the whole planet" ;;
  *"git push --force"*) deny "🔫 force push detected, use --force-with-lease" ;;
  *"git reset --hard"*) deny "🕳️ that shreds uncommitted work, stash it first" ;;
  *"curl"*"| sh"*)      deny "🎣 curl-pipe-to-shell is how goblins get in" ;;
  *".env"*)             deny "🔐 secrets are off limits, no peeking" ;;
esac

echo "✅🛡️ Bash guard says this one looks harmless. Carry on! 🚀"
exit 0
```

The `deny` path exits `2`, so the emoji scolding on `stderr` goes straight back to
Claude, which then picks a safer command. The happy path prints its thumbs-up to the
transcript.

## Other useful events

| Event | Fires when | Typical use |
| --- | --- | --- |
| `UserPromptSubmit` | User sends a message | Inject context (branch, ticket id), block secrets in prompts |
| `SessionStart` | Session begins/resumes | Print open TODOs, warm caches |
| `SubagentStop` | A subagent finishes | Validate subagent output |
| `Notification` | Claude needs input | Desktop notification / Slack ping |
| `PreCompact` | Before context compaction | Persist notes to a file |

## Notes

- Make hook scripts executable: `chmod +x .claude/hooks/*.sh`.
- `$CLAUDE_PROJECT_DIR` points at the project root; use it so hooks work regardless of cwd.
- Hooks run with your user's credentials and no confirmation — review any hook you copy.
- Check registered hooks with `/hooks`; settings changes are picked up at session start.
