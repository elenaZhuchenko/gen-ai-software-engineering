# AI-Powered Multi-Agent Banking Transaction Pipeline

**Created by Elena Zhuchenko**  
Homework 6 — Capstone Project | GenAI and Agentic AI for Software Engineering

---

## Overview

This project implements a **four-agent banking transaction pipeline** that validates, risk-scores, and reports on financial transactions using a file-based message-passing architecture. The system processes raw transaction records from `sample-transactions.json` through three cooperating agents — Transaction Validator, Fraud Detector, and Reporting Agent — orchestrated by an Integrator. Every result is written to `shared/results/` with a full audit trail.

All monetary values use `decimal.Decimal` for exact arithmetic (never `float`). Currency codes are validated against the ISO 4217 alpha-3 standard. Account numbers and PII never appear in log output.

---

## Pipeline Architecture

```
sample-transactions.json
          │
          ▼
    ┌───────────┐
    │ Integrator│  ← sets up shared/ dirs, loads input, orchestrates agents
    └─────┬─────┘
          │ writes JSON message → shared/input/<TXN_ID>.json
          ▼
   shared/input/ ──(moved while working)──▶ shared/processing/
          │                                         │
          │                    ┌────────────────────┘
          ▼                    ▼
┌─────────────────────┐   writes result →  shared/output/<TXN_ID>.json
│ Transaction Validator│  ← checks fields, Decimal amount > 0, ISO 4217 currency
└──────────┬──────────┘
           │ status: validated → shared/output/ picked up by fraud_detector
           │ status: rejected  → shared/output/ picked up by reporting_agent
           ▼
   shared/output/ ──(moved while working)──▶ shared/processing/
          │                                         │
          │                    ┌────────────────────┘
          ▼                    ▼
  ┌─────────────────┐    writes result →  shared/output/<TXN_ID>.json
  │  Fraud Detector  │  ← risk score 0–100 (HIGH_VALUE +60, CROSS_BORDER +20, OFF_HOURS +20)
  └────────┬─────────┘    score ≥ 60 → fraud_review; below → approved
           │
           ▼
   shared/output/ ──(moved while working)──▶ shared/processing/
          │                                         │
          │                    ┌────────────────────┘
          ▼                    ▼
  ┌─────────────────────┐
  │   Reporting Agent    │  ← writes shared/results/<TXN_ID>.json per transaction
  └──────────┬───────────┘    writes shared/results/pipeline-summary.json
             │
             ▼
      shared/results/
      ├── TXN001.json
      ├── TXN002.json
      ├── ...
      └── pipeline-summary.json
```

Every arrow above is a real file on disk, not just an in-memory Python
call: `shared/input/`, `shared/processing/`, and `shared/output/` are
transient mailboxes (cleared before every run and left empty once a run
completes — every message is consumed by the next stage); `shared/results/`
is the only durable directory.

---

## Agent Responsibilities

| Agent | File | Role |
|-------|------|------|
| **Integrator** | `integrator.py` | Orchestrates the pipeline; loads input; manages `shared/` dirs |
| **Transaction Validator** | `agents/transaction_validator.py` | Required-field check; positive `decimal.Decimal` amount; ISO 4217 currency |
| **Fraud Detector** | `agents/fraud_detector.py` | Risk scoring: high-value (+60), cross-border (+20), off-hours (+20); flags ≥60 |
| **Reporting Agent** | `agents/reporting_agent.py` | Writes per-transaction result JSON and `pipeline-summary.json` |

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.12 |
| Money arithmetic | `decimal.Decimal` (never `float`) |
| MCP server | FastMCP 3.x |
| Testing | pytest + pytest-cov |
| Slash commands | `.cursor/commands/*.md` |
| Coverage gate | Git `pre-push` hook + `.cursor/hooks.json` |
| Agent communication | File-based JSON messages (`shared/`) |

---

## Message Protocol

```json
{
  "message_id": "uuid4-string",
  "timestamp": "2026-03-16T10:00:00Z",
  "source_agent": "transaction_validator",
  "target_agent": "fraud_detector",
  "message_type": "transaction",
  "data": {
    "transaction_id": "TXN001",
    "amount": "1500.00",
    "currency": "USD",
    "status": "validated"
  }
}
```

---

## MCP Servers

| Server | Config key | Purpose |
|--------|-----------|---------|
| context7 | `context7` | Framework documentation lookup during development |
| Pipeline Status | `pipeline-status` | `get_transaction_status`, `list_pipeline_results`, `pipeline://summary` |

Configure via `.cursor/mcp.json` (see `mcp.json` for the canonical config).

---

## Slash Commands

| Command | File | Usage |
|---------|------|-------|
| `/write-spec` | `.cursor/commands/write-spec.md` | Generate `specification.md` from the 5-section template |
| `/run-pipeline` | `.cursor/commands/run-pipeline.md` | Run the full pipeline end-to-end |
| `/validate-transactions` | `.cursor/commands/validate-transactions.md` | Dry-run validation without writing results |

---

## Coverage Gate

A git `pre-push` hook (`scripts/git-hooks/pre-push`) runs `pytest --cov` and blocks the push if coverage falls below **80%**. A `.cursor/hooks.json` `beforeShellExecution` hook mirrors this gate for pushes initiated by the Cursor agent. Since this repo is a shared monorepo, both hooks first check whether the push actually touches `homework-6/` (by branch name or diff against `origin/main`) and skip the check entirely otherwise — so pushing another homework's branch never requires `homework-6/.venv` to exist.

Install once:
```bash
bash scripts/install-git-hooks.sh
```

---

## Quick Start

```bash
# Setup
cd homework-6
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Run pipeline
python integrator.py

# Run tests
pytest

# Check results
cat shared/results/pipeline-summary.json
```

See `HOWTORUN.md` for the full step-by-step guide.
