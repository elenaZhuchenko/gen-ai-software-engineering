# Technical Specification — AI-Powered Multi-Agent Banking Transaction Pipeline

**Project:** Homework 6 Capstone  
**Author:** Elena Zhuchenko  
**Stack:** Python 3.12, FastMCP, pytest

---

## 1. High-Level Objective

Build an automated, file-based multi-agent pipeline that validates, risk-scores, and reports on banking transactions, writing every result to `shared/results/` with a full audit trail.

---

## 2. Mid-Level Objectives

1. **Field validation** — every transaction must have `transaction_id`, `timestamp` (ISO 8601), `source_account`, `destination_account`, a positive `amount` (decimal string), and a valid ISO 4217 `currency`; missing or malformed records are rejected immediately with a structured `reason` field.
2. **Fraud scoring** — transactions above $10,000 are assigned a numeric risk score (0–100) and flagged with `status: fraud_review`; cross-border transactions (country ≠ "US") and unusual-hours transactions (00:00–06:00 UTC) add additional risk points.
3. **Reporting** — a `ReportingAgent` consolidates all per-transaction results into `shared/results/pipeline-summary.json` containing total count, valid count, rejected count, flagged-for-fraud count, and an ISO 8601 run timestamp.
4. **File-based message protocol** — agents communicate exclusively through JSON files in `shared/input/` → `shared/processing/` → `shared/output/` → `shared/results/`; each message includes `message_id` (UUID4), `timestamp`, `source_agent`, `target_agent`, `message_type`, and `data`.
5. **Audit logging** — every state-mutating operation emits a structured log line containing ISO 8601 timestamp, agent name, `transaction_id`, and outcome (`accepted` / `rejected` / `fraud_review`); PII (account numbers) is never logged in plaintext.

---

## 3. Implementation Notes

- **Money**: use `decimal.Decimal` throughout — never `float`; JSON `amount` fields are decimal strings (e.g. `"1500.00"`).
- **Currency**: validate against an explicit ISO 4217 alpha-3 allow-list at the validator layer.
- **Logging**: structured log lines (to stdout/stderr); format: `[ISO8601] [AGENT_NAME] txn=<id> outcome=<outcome>`.
- **PII**: `source_account` and `destination_account` are never written to logs; only masked references (last 4 chars) may appear.
- **Error envelope**: rejected messages carry `{"status": "rejected", "reason": "MACHINE_CODE", "message": "human text"}`.
- **Idempotency**: the integrator clears `shared/processing/` and `shared/output/` before each run so re-runs are safe.

---

## 4. Context

- **Beginning state**: `homework-6/sample-transactions.json` — 8 raw transaction records including valid, high-value, invalid-currency, and negative-amount examples.
- **Ending state**:  
  - `shared/results/TXN001.json` … `TXN008.json` — one result file per transaction  
  - `shared/results/pipeline-summary.json` — aggregate report  
  - Unit-test coverage ≥ 90% enforced by a git `pre-push` hook

---

## 5. Low-Level Tasks

```
Task: Transaction Validator (Agent 1)
Prompt: "Write agents/transaction_validator.py. Implement process_message(message: dict) -> dict.
         Read the raw transaction from message['data'], validate: required fields present,
         amount is a positive decimal.Decimal (reject negatives/zero), currency is in ISO 4217
         alpha-3 allow-list. Return a new message dict with source_agent='transaction_validator',
         target_agent='fraud_detector', and data['status']='validated' or 'rejected' plus a
         reason code. Use decimal.Decimal for all amount comparisons. Never log account numbers."
File to CREATE: agents/transaction_validator.py
Function to CREATE: process_message(message: dict) -> dict
Details: Checks required fields, positive Decimal amount, ISO 4217 currency code.
         Rejects with reason codes: MISSING_FIELD, INVALID_AMOUNT, INVALID_CURRENCY.
```

```
Task: Fraud Detector (Agent 2)
Prompt: "Write agents/fraud_detector.py. Implement process_message(message: dict) -> dict.
         Accept only messages with data['status']='validated'. Compute a risk_score 0-100:
         +60 if amount > 10000, +20 if metadata.country != 'US' (cross-border), +20 if
         transaction hour (UTC) is between 00:00 and 06:00 (unusual timing). If risk_score >= 60
         set status='fraud_review', else status='approved'. Return updated message with
         source_agent='fraud_detector', target_agent='reporting_agent'."
File to CREATE: agents/fraud_detector.py
Function to CREATE: process_message(message: dict) -> dict
Details: Risk scoring: high-value (+60), cross-border (+20), off-hours (+20).
         Threshold 60 → fraud_review; below → approved.
```

```
Task: Reporting Agent (Agent 3)
Prompt: "Write agents/reporting_agent.py. Implement process_message(message: dict) -> dict
         and write_summary(results: list[dict], output_dir: str) -> None.
         process_message writes the final result JSON to shared/results/<transaction_id>.json.
         write_summary aggregates all results into shared/results/pipeline-summary.json with
         fields: run_timestamp (ISO 8601 UTC), total, validated, rejected, fraud_review, approved."
File to CREATE: agents/reporting_agent.py
Function to CREATE: process_message(message: dict) -> dict; write_summary(results, output_dir)
Details: Writes per-transaction result files and a summary report.
```

```
Task: Integrator / Orchestrator
Prompt: "Write integrator.py. Load sample-transactions.json, set up shared/ subdirectories,
         pipe each transaction through TransactionValidator → FraudDetector → ReportingAgent
         in sequence using the file-based message protocol (UUID4 message_id, ISO 8601 timestamp,
         source_agent, target_agent, message_type, data). After all transactions, call
         write_summary(). Print a final status line: '✓ Pipeline complete: N transactions processed'."
File to CREATE: integrator.py
Function to CREATE: main() -> None; run_pipeline(transactions: list, shared_dir: str) -> list
Details: Orchestrates the three agents in order, manages shared/ directories, loads input,
         produces results and summary.
```
