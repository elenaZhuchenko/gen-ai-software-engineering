Generate a complete technical specification for the AI-Powered Multi-Agent Banking Transaction Pipeline.

Write or update `homework-6/specification.md` using **exactly** this five-section structure:

---

## 1. High-Level Objective
One sentence describing what the pipeline does end-to-end.

## 2. Mid-Level Objectives (4–5 items)
Concrete, testable requirements, for example:
- Transactions above $10,000 are flagged for fraud review with a numeric risk score
- Rejected transactions are written to `shared/results/` with a `reason` field
- All agent operations are logged with ISO 8601 timestamps
- Currency codes are validated against the ISO 4217 allowlist
- Pipeline produces a summary report in `shared/results/pipeline-summary.json`

## 3. Implementation Notes
- **Money**: use `decimal.Decimal` — never `float`; amounts as decimal strings in JSON
- **Currency**: ISO 4217 alpha-3 codes only; validate at the agent layer
- **Logging**: structured audit trail — timestamp (ISO 8601 UTC), agent name, transaction_id, outcome
- **PII**: account numbers and names are sensitive — never log raw values; mask or omit entirely

## 4. Context
- **Beginning state**: `sample-transactions.json` with 8 raw transaction records in `homework-6/`
- **Ending state**: every transaction record in `shared/results/`; `shared/results/pipeline-summary.json`; unit-test coverage ≥ 90%

## 5. Low-Level Tasks
One entry per agent, exactly this format:
```
Task: [Agent Name]
Prompt: "[Exact prompt you give the AI to build this agent]"
File to CREATE: agents/<agent_name>.py
Function to CREATE: process_message(message: dict) -> dict
Details: [What the agent checks, transforms, or decides]
```
Include all four agents: Transaction Validator, Fraud Detector, Reporting Agent, and Integrator/Orchestrator.

---

After writing the file confirm the path and summarise the Mid-Level Objectives you chose.
