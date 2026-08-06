# HOWTORUN — AI-Powered Multi-Agent Banking Pipeline

Step-by-step guide from initial setup to running the full demo.

---

## Prerequisites

- Python 3.12+ (`python3.12 --version`)
- Node.js + npx (for context7 MCP server: `node --version`)
- Git

---

## 1. Clone and Navigate

```bash
git clone https://github.com/<your-username>/gen-ai-software-engineering.git
cd gen-ai-software-engineering/homework-6
```

---

## 2. Create Virtual Environment

```bash
python3.12 -m venv .venv
source .venv/bin/activate          # macOS/Linux
# .venv\Scripts\activate.bat       # Windows
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 4. Install Coverage Gate Hook (once per clone)

```bash
bash scripts/install-git-hooks.sh
```

This configures `git config core.hooksPath` to point at `scripts/git-hooks/`. The `pre-push` hook will run `pytest --cov` and block any push if coverage is below 80%.

---

## 5. Run the Pipeline

```bash
python integrator.py
```

Expected output:
```
2026-08-06T...Z INFO [integrator] loaded 8 transactions from .../sample-transactions.json
...
✓ Pipeline complete: 8 transactions processed | approved=4 fraud_review=2 rejected=2
```

Results are written to `shared/results/`:
- `TXN001.json` … `TXN008.json` — per-transaction results
- `pipeline-summary.json` — aggregate summary

---

## 6. View Results

```bash
# Summary
cat shared/results/pipeline-summary.json

# Individual transaction
cat shared/results/TXN002.json     # high-value → fraud_review
cat shared/results/TXN006.json     # invalid currency → rejected
```

---

## 7. Run Tests

```bash
pytest
```

This runs 81 tests against all three agents and the integrator. Coverage is printed at the end; you should see ≥ 90%.

```bash
# Verbose output
pytest -v

# Coverage only (no test output)
pytest --cov=agents --cov=integrator --cov-report=term-missing -q
```

---

## 8. Use Slash Commands in Cursor

Open the project in Cursor, then type `/` in the Agent chat input to see available commands:

| Command | Action |
|---------|--------|
| `/run-pipeline` | Runs the full pipeline and reports results |
| `/validate-transactions` | Dry-run validation without writing files |
| `/write-spec` | Generates `specification.md` from the template |

---

## 9. Start the Custom MCP Server (pipeline-status)

The MCP server is configured in `.cursor/mcp.json` and starts automatically when Cursor loads. To run it manually:

```bash
.venv/bin/python mcp/server.py
```

To query it in Cursor, ask the agent:
- "Call `get_transaction_status` for TXN002"
- "Call `list_pipeline_results`"
- "Show me the `pipeline://summary` resource"

---

## 10. Demonstrate the Coverage Gate Hook

```bash
# Test the git pre-push hook manually
bash scripts/git-hooks/pre-push

# To see the block in action — temporarily break coverage, then try pushing:
# (comment out one test file, run: git push origin homework-6-submission)
# The hook will print "🚫 PUSH BLOCKED — test coverage is below 80%."
# Restore the test file, then push succeeds.
```

---

## 11. Create a Submission PR

```bash
git add .
git commit -m "Complete Homework 6 capstone pipeline"
git push origin homework-6-submission
# → Pre-push hook runs and confirms coverage ≥ 80% before allowing the push
```

Then create a Pull Request on GitHub targeting your fork's `main` branch and assign `Alexey-Popov` as reviewer.

---

## Directory Reference

```
homework-6/
├── agents/              ← Three pipeline agents
├── mcp/server.py        ← FastMCP pipeline-status server
├── tests/               ← 81 unit + integration tests
├── shared/              ← Runtime message directories (gitignored except .gitkeep)
├── .cursor/commands/    ← Slash commands (/run-pipeline, /validate-transactions, /write-spec)
├── .cursor/hooks.json   ← Cursor coverage-gate hook
├── scripts/git-hooks/   ← Native git pre-push hook
├── integrator.py        ← Orchestrator
├── sample-transactions.json
├── specification.md
├── agents.md
├── research-notes.md
├── mcp.json             ← MCP server configuration
├── pyproject.toml       ← pytest + coverage config
└── docs/screenshots/    ← Required screenshots
```
