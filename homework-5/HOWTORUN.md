# HOWTORUN — Homework 5: MCP Servers (Claude Code)

This guide covers how to install, run, connect, and test each of the four MCP servers
using the **Claude Code CLI** (`claude`).

---

## Prerequisites

- **Claude Code CLI** installed and authenticated (`claude --version`; see
  <https://code.claude.com/docs/en/quickstart> if you don't have it yet)
- **Node.js** v18+ with `npx` (for the Filesystem and Notion MCP servers)
- **Python 3.12+** (for the custom FastMCP server)
- A **GitHub Personal Access Token** (classic, scopes: `repo`, `read:org`)
- A **Notion Internal Integration Token** (`ntn_...`) and a workspace with pages

---

## 0. Project-scoped configuration (`.mcp.json`)

All four servers are already declared in [`homework-5/.mcp.json`](.mcp.json), which Claude
Code auto-discovers when you launch `claude` from inside `homework-5/`. Secrets and
machine-specific paths are **not** hard-coded in the file — they are pulled from
environment variables at launch time via `${VAR}` expansion, and the custom server's
path uses `${CLAUDE_PROJECT_DIR}` (the project root Claude Code injects automatically):

```json
{
  "mcpServers": {
    "github": {
      "type": "http",
      "url": "https://api.githubcopilot.com/mcp/",
      "headers": { "Authorization": "Bearer ${GITHUB_PAT}" }
    },
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "${CLAUDE_PROJECT_DIR:-.}"]
    },
    "notion": {
      "command": "npx",
      "args": ["-y", "@notionhq/notion-mcp-server"],
      "env": { "NOTION_TOKEN": "${NOTION_TOKEN}" }
    },
    "custom-mcp-server": {
      "command": "${CLAUDE_PROJECT_DIR:-.}/custom-mcp-server/.venv/bin/python",
      "args": ["${CLAUDE_PROJECT_DIR:-.}/custom-mcp-server/server.py"]
    }
  }
}
```

Because this file is committed to git, `claude` normally prompts you the first time you
open the project to approve each project-scoped server. This repo pre-approves them via
[`homework-5/.claude/settings.json`](.claude/settings.json):

```json
{ "enableAllProjectMcpServers": true }
```

so all four servers connect automatically — verified with `claude mcp list`:

```
github: https://api.githubcopilot.com/mcp/ (HTTP) - ✔ Connected
filesystem: npx -y @modelcontextprotocol/server-filesystem ${CLAUDE_PROJECT_DIR:-.} - ✔ Connected
notion: npx -y @notionhq/notion-mcp-server - ✔ Connected
custom-mcp-server: .../custom-mcp-server/.venv/bin/python .../server.py - ✔ Connected
```

Screenshot of this check run from inside a `claude` chat:
[`docs/screenshots/claude-mcp-list.png`](docs/screenshots/claude-mcp-list.png)

### Load your secrets, then start Claude Code

```bash
cd homework-5
cp .env.example .env        # first time only, then fill in real values
set -a && source .env && set +a
claude
```

Inside the session, run `/mcp` at any time to see the status of all four servers
(connected/failed) without leaving the chat.

> Alternative: instead of hand-editing `.mcp.json`, you can register/inspect servers with
> the CLI directly, e.g. `claude mcp add --scope project --transport http github https://api.githubcopilot.com/mcp/ --header "Authorization: Bearer $GITHUB_PAT"`.
> `claude mcp list` shows every configured server and its connection status.

---

## 1. GitHub MCP

### Setup

1. Create a GitHub PAT at <https://github.com/settings/tokens> with scopes `repo` and
   `read:org`. Put it in `homework-5/.env` as `GITHUB_PAT=...`.
2. The `github` entry in `.mcp.json` already points at the official remote server
   (`https://api.githubcopilot.com/mcp/`) and reads the token from `${GITHUB_PAT}`.
3. Start `claude` (after sourcing `.env`, see step 0) from `homework-5/` and approve the
   `github` server when prompted.

### Verify

In the Claude Code chat, ask:

```
Using the GitHub MCP, show me the 5 most recent pull requests in this repository and briefly summarize the last 5 commits on main.
```

You should see pull request and commit data returned from GitHub via the MCP tool calls
(visible in the transcript as `github.list_pull_requests`, `github.list_commits`, etc.).

Screenshot: [`docs/screenshots/github-mcp-result.png`](docs/screenshots/github-mcp-result.png)

---

## 2. Filesystem MCP

### Setup

No installation required — `npx` downloads the server on demand. The `filesystem` entry
in `.mcp.json` points at `${CLAUDE_PROJECT_DIR:-.}`, i.e. the `homework-5/` project root.

### Verify

In the Claude Code chat, ask:

```
Using the Filesystem MCP, list the files in the custom-mcp-server directory and read the contents of README.md.
```

The server returns a directory listing and file contents via MCP tool calls
(`filesystem.list_directory`, `filesystem.read_text_file`).

Screenshot: [`docs/screenshots/filesystem-mcp-result.png`](docs/screenshots/filesystem-mcp-result.png)

---

## 3. Notion MCP

### Set up a Notion Integration

1. Go to <https://www.notion.so/profile/integrations> → **New integration**.
2. Give it a name (e.g. "Homework 5 MCP"), set **Read content** capability, and save.
3. Copy the token that starts with `ntn_` into `homework-5/.env` as `NOTION_TOKEN=...`.
4. Open a Notion page (or database) you want the integration to access → click **"..."** →
   **"Add connections"** → select your integration.

### Seed test bug pages (optional but recommended)

```bash
cd homework-5
export NOTION_TOKEN="ntn_your_token"
export NOTION_PARENT_PAGE_ID="your_32char_page_id"
python3 create_notion_bugs.py
```

Five "Bug: ..." sub-pages will be created under the target page.

### Verify

After starting `claude` with `.env` sourced, ask in the chat (exactly as required by the
assignment):

```
Give me the tickets/pages of the last 5 bugs on a project.
```

You should see the five bug pages returned from your Notion workspace via
`notion.API-post-search`.

Screenshot: [`docs/screenshots/jira-or-notion-mcp-result.png`](docs/screenshots/jira-or-notion-mcp-result.png)

---

## 4. Custom FastMCP Server

### Install dependencies

```bash
cd homework-5/custom-mcp-server
python3.12 -m venv .venv
source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

`fastmcp` is declared in [`requirements.txt`](custom-mcp-server/requirements.txt).

### Run the server standalone (for testing)

```bash
# From custom-mcp-server/ with .venv activated:
python server.py
```

The server starts and listens on stdio, ready for an MCP client to connect.

### Connect to Claude Code

Already wired up in `.mcp.json` via `${CLAUDE_PROJECT_DIR:-.}/custom-mcp-server/.venv/bin/python`
— no manual configuration needed as long as the virtualenv above has been created. Confirm
with:

```bash
claude mcp list
```

`custom-mcp-server` should show as connected.

### Test the `read` tool

Claude Code has a **built-in** file tool also named `Read`, so be explicit that you mean
the MCP tool from `custom-mcp-server` (otherwise Claude may try to read a file path
instead). In the Claude Code chat:

```
Call the custom-mcp-server MCP tool named "read" (not the file Read tool) with word_count=15, and show me its output.
```

Expected response: the first 15 words of the lorem ipsum text.

You can also request the resource directly:

```
Read the MCP resource lorem://text/30 from custom-mcp-server.
```

Screenshots:
[`docs/screenshots/custom-mcp-read-tool-result.png`](docs/screenshots/custom-mcp-read-tool-result.png)
(resource read via `lorem://text/30`) and
[`docs/screenshots/custom-mcp-read-tool-result-1.png`](docs/screenshots/custom-mcp-read-tool-result-1.png)
(explicit `read` tool call with `word_count=15`).

> **Important:** these prompts only work if `claude` was launched with `homework-5/` as
> the working directory (see step 0) — that's what makes `custom-mcp-server` show up at
> all. Run `/mcp` first to confirm it's listed before calling the tool.

`word_count` is clamped to `[0, total_words]` inside `server.py`, so negative, zero, or
overly large values return a sensible (empty or full-length) result instead of relying on
Python's raw slice semantics (e.g. `word_count=-1` would otherwise silently return all but
the last word).

---

## Full `.mcp.json` reference (all four servers)

See [`homework-5/.mcp.json`](.mcp.json) — this file is committed as-is (no real secrets),
and is the single source of truth for all four server configurations.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Server shows "failed" in `claude mcp list` / `/mcp` | Confirm the required env var (`GITHUB_PAT`, `NOTION_TOKEN`) was exported **before** launching `claude` |
| `claude` never prompts to approve project servers | Run `claude mcp reset-project-choices` from `homework-5/`, then restart `claude` |
| GitHub MCP not appearing | Check PAT scopes (`repo`, `read:org`); confirm `${GITHUB_PAT}` resolves with `echo $GITHUB_PAT` |
| `npx: command not found` | Install Node.js v18+ |
| Notion returns empty results | Ensure the integration is shared with the target page ("..." → "Add connections") |
| Custom server fails to start | Run `python server.py` directly from `custom-mcp-server/` to see the error; confirm `.venv` was created with Python 3.12+ |
| `${CLAUDE_PROJECT_DIR}` not resolving for the custom server | Make sure you launched `claude` from inside `homework-5/` (or a subdirectory of it) so it is detected as the project root |
| `custom-mcp-server` missing from `/mcp` even though `claude mcp list` shows it connected | You launched the interactive session from a different directory than the terminal check (e.g. the repo root). `.mcp.json` is only auto-discovered when `homework-5/` is the actual working directory Claude Code starts in — `cd` there first, then run `claude` |
| Claude says "there's no MCP tool matching that description" / confuses `read` with the built-in `Read` file tool | Rephrase the prompt to explicitly say "the custom-mcp-server MCP tool named read" (see Section 4 above) |
