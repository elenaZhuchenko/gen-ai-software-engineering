# agents.md — AI-Powered Multi-Agent Banking Transaction Pipeline

## Project Context

This is Homework 6 Capstone: a four-agent banking pipeline that processes transactions from `sample-transactions.json` through validation, fraud detection, and reporting stages. Agents communicate via JSON files in `shared/` directories.

## Agent Roster

| Agent | File | Role |
|-------|------|------|
| Transaction Validator | `agents/transaction_validator.py` | Validates required fields, positive decimal amounts, ISO 4217 currency codes |
| Fraud Detector | `agents/fraud_detector.py` | Scores risk (0–100) based on amount, geography, timing |
| Reporting Agent | `agents/reporting_agent.py` | Writes per-transaction results and aggregate summary |
| Integrator | `integrator.py` | Orchestrates the pipeline; manages `shared/` directories |

## File-Based Message Protocol

Agents pass messages as JSON files through `shared/` subdirectories:

```
shared/
├── input/       ← Integrator drops initial messages here
├── processing/  ← Agent moves message here while working
├── output/      ← Agent writes result here for next agent
└── results/     ← Final per-transaction outcomes and summary
```

### Standard Message Schema

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
    "status": "validated",
    "risk_score": 0
  }
}
```

## Decision Rules

### Transaction Validator
- **MISSING_FIELD**: required keys absent → reject
- **INVALID_AMOUNT**: `Decimal(amount) <= 0` → reject
- **INVALID_CURRENCY**: currency not in ISO 4217 alpha-3 allow-list → reject

### Fraud Detector
| Condition | Risk Points |
|-----------|------------|
| amount > $10,000 | +60 |
| metadata.country ≠ "US" | +20 |
| Transaction hour UTC 00:00–05:59 | +20 |
| **Total ≥ 60** | → `fraud_review` |
| **Total < 60** | → `approved` |

### Reporting Agent
Writes `shared/results/<transaction_id>.json` for each transaction, then `pipeline-summary.json`:
```json
{
  "run_timestamp": "2026-03-16T10:00:00Z",
  "total": 8,
  "validated": 6,
  "rejected": 2,
  "approved": 3,
  "fraud_review": 3
}
```

## File-Based Hand-Off Mechanics

The integrator does not pass messages between agents as in-memory objects
only. For every transaction it:
1. Writes the initial message to `shared/input/<txn_id>.json`.
2. Moves that file into `shared/processing/<txn_id>.json` before invoking
   the next agent (marking which agent currently "owns" the message).
3. Writes the agent's result to `shared/output/<txn_id>.json` for the next
   stage to pick up, and removes the `processing/` copy.
4. Repeats for the next agent (`shared/output/` → `shared/processing/` →
   `shared/output/`), until the reporting agent consumes the last
   `output/` message and writes the durable result straight to
   `shared/results/<txn_id>.json`.

`shared/input/`, `shared/processing/`, and `shared/output/` are transient
mailboxes — cleared by the integrator before every run — and end up empty
once a run completes, since every message is consumed by the next stage.
`shared/results/` is the only durable directory.

## Fintech Safety Constraints

- `decimal.Decimal` for all monetary arithmetic — never `float`
- ISO 4217 currency validation at the validator layer
- Account numbers never appear in logs — masked to last 4 chars only
- All results written atomically (write to tmp, rename) to avoid partial reads
- Every agent logs: `[ISO8601] [AGENT] txn=<id> outcome=<outcome>`

## MCP Servers

| Server | Purpose |
|--------|---------|
| `context7` | Framework docs lookup during development |
| `pipeline-status` | Queries pipeline results (`get_transaction_status`, `list_pipeline_results`) |

## Slash Commands

| Command | File | Purpose |
|---------|------|---------|
| `/write-spec` | `.cursor/commands/write-spec.md` | Generate specification.md from template |
| `/run-pipeline` | `.cursor/commands/run-pipeline.md` | Run full pipeline end-to-end |
| `/validate-transactions` | `.cursor/commands/validate-transactions.md` | Dry-run validation only |

## Coverage Gate

A git `pre-push` hook (`scripts/git-hooks/pre-push`) blocks any push when unit-test coverage is below **80%**. A `.cursor/hooks.json` `beforeShellExecution` hook mirrors this gate for pushes initiated by the Cursor agent.
