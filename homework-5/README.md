# Homework 5 — Configure MCP Servers (GitHub, Filesystem, Notion, Custom)

**Course:** GenAI and Agentic AI for Software Engineering
**Author:** Elena Zhuchenko
**Stack:** Python 3.12 · FastMCP · Node.js (npx) · Claude Code CLI

---

## Overview

This submission configures **three external MCP servers** (GitHub, Filesystem, Notion) and builds
**one custom MCP server** with FastMCP. Each server is demonstrated through a live interaction
inside the **Claude Code CLI** (`claude`), with screenshots of every call result.

### What is MCP?

The **Model Context Protocol (MCP)** is an open standard that lets AI clients (e.g. Claude Code,
Claude Desktop, Cursor) connect to external data sources and tools via a uniform interface.
Servers are registered in the project-scoped `.mcp.json`; Claude Code auto-discovers this file
when launched from `homework-5/`, spawns each server, and exposes their capabilities to the AI.

### Resources vs Tools

| Concept | What it is | When the AI uses it |
|---------|-----------|---------------------|
| **Resource** | A URI-addressable data source the AI can *read* (like a GET endpoint). Identified by a scheme, e.g. `lorem://text/30`. | When the AI needs to fetch or display data without side effects. |
| **Tool** | A callable function the AI can *invoke* with arguments and receive a result. | When the AI needs to perform a parameterized operation, e.g. `read(word_count=15)`. |

---

## MCP Servers Configured

| # | Server | Type | Auth |
|---|--------|------|------|
| 1 | GitHub (`github`) | Remote HTTP | GitHub PAT |
| 2 | Filesystem (`filesystem`) | Local stdio (npx) | None |
| 3 | Notion (`notion`) | Local stdio (npx) | Notion Integration Token |
| 4 | Custom lorem-ipsum (`custom-mcp-server`) | Local stdio (python) | None |

Configuration lives in [`homework-5/.mcp.json`](.mcp.json) — committed as-is, with **no real
tokens** hard-coded. Secrets are injected via `${GITHUB_PAT}` / `${NOTION_TOKEN}` environment
variable expansion (Claude Code's native `.mcp.json` substitution), sourced from a local,
gitignored `.env` file before `claude` starts. Machine-specific paths use Claude Code's built-in
`${CLAUDE_PROJECT_DIR}` placeholder instead of an absolute path.

All four connections verified together with `claude mcp list`:
[`docs/screenshots/claude-mcp-list.png`](docs/screenshots/claude-mcp-list.png)

---

## Task 1 — GitHub MCP

Uses the official remote GitHub MCP server at `https://api.githubcopilot.com/mcp/`.
Authenticated via a Personal Access Token (classic, scope: `repo`, `read:org`).

Demonstrated interaction: listing recent pull requests in this repository.

Screenshot: [`docs/screenshots/github-mcp-result.png`](docs/screenshots/github-mcp-result.png)

---

## Task 2 — Filesystem MCP

Uses `@modelcontextprotocol/server-filesystem` (npx, no install required) pointed at the
repository root. Allows the AI to list directories, read files, and summarise project structure.

Demonstrated interaction: listing all files in `homework-5/`.

Screenshot: [`docs/screenshots/filesystem-mcp-result.png`](docs/screenshots/filesystem-mcp-result.png)

---

## Task 3 — Notion MCP

Uses `@notionhq/notion-mcp-server` (npx) with a Notion Internal Integration Token.
A helper script (`create_notion_bugs.py`) seeds five sample bug pages into the target workspace.

Demonstrated interaction: *"Give me the tickets/pages of the last 5 bugs on a project."*

Screenshot: [`docs/screenshots/jira-or-notion-mcp-result.png`](docs/screenshots/jira-or-notion-mcp-result.png)

---

## Task 4 — Custom FastMCP Server

`custom-mcp-server/server.py` exposes lorem ipsum text from `lorem-ipsum.md`:

- **Resource** `lorem://text` — returns 30 words (default).
- **Resource** `lorem://text/{word_count}` — returns exactly `word_count` words.
- **Tool** `read(word_count: int = 30)` — callable by the AI with an optional word count.
- Out-of-range `word_count` values (negative, zero, or larger than the source file) are
  clamped to `[0, total_words]` rather than relying on raw Python slice semantics, so the
  tool never silently returns the wrong number of words.

Demonstrated interaction: reading the `lorem://text/30` resource, then calling the `read`
tool with `word_count=15`.

Screenshots:
[`docs/screenshots/custom-mcp-read-tool-result.png`](docs/screenshots/custom-mcp-read-tool-result.png)
(resource read via `lorem://text/30`) and
[`docs/screenshots/custom-mcp-read-tool-result-1.png`](docs/screenshots/custom-mcp-read-tool-result-1.png)
(explicit `read` tool call with `word_count=15`, disambiguated from the built-in `Read` file tool).

---

## Repository Structure

```
homework-5/
├── README.md                       ← this file
├── HOWTORUN.md                     ← setup and usage guide
├── .mcp.json                       ← Claude Code project-scoped MCP config (no real secrets)
├── .claude/settings.json           ← auto-approves the project-scoped MCP servers above
├── create_notion_bugs.py           ← helper: seeds 5 bug pages into Notion via API
├── run-mcp.sh                      ← optional: exercise all 4 servers from the terminal via fastmcp CLI
├── .env.example                    ← template for GITHUB_PAT / NOTION_TOKEN
├── .gitignore
├── custom-mcp-server/
│   ├── server.py                   ← FastMCP server (resource + read tool)
│   ├── lorem-ipsum.md              ← source text
│   └── requirements.txt            ← includes fastmcp
└── docs/screenshots/
    ├── github-mcp-result.png
    ├── filesystem-mcp-result.png
    ├── jira-or-notion-mcp-result.png
    ├── custom-mcp-read-tool-result.png
    ├── custom-mcp-read-tool-result-1.png   (extra: explicit `read` tool call)
    └── claude-mcp-list.png                 (extra: `claude mcp list` showing all 4 connected)
```

---

## AI Tools Used

- **Claude Code CLI** — client used to configure, connect, and interact with all four MCP servers
- **Cursor AI Agent** (Sonnet 4.5) — generated code, configuration, and documentation
- **FastMCP** — framework for the custom MCP server
- **Notion API** — used in `create_notion_bugs.py` to seed test data
