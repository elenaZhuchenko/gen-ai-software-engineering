# Homework 4 — 4-Agent Bug/Security/Test Pipeline

**Course:** GenAI and Agentic AI for Software Engineering  
**Author:** Elena Zhuchenko
**Stack:** Python 3.10+ · Cursor Python SDK · pytest

---

## Overview

This submission implements a **6-stage agentic pipeline** (4 required + 2
supporting agents) that autonomously discovers, verifies, plans, fixes, audits,
and tests bugs in a small Python application — all triggered by a single command.

```
./run-pipeline.sh
```

### Pipeline flow

```
Bug Researcher ──► Research Verifier ──► Bug Planner ──► Bug Fixer
                                                              │
                                    Security Verifier ◄───────┤
                                    Unit Test Generator ◄─────┘
```

| Stage | Agent | Model | Role |
|-------|-------|-------|------|
| 1 | Bug Researcher | claude-opus-4-8 | Reads source, documents bugs/security issues |
| 2 | Research Verifier | claude-opus-4-8 | Fact-checks every file:line reference; assigns quality level |
| 3 | Bug Planner | composer-2.5 | Translates verified findings into before/after code plan |
| 4 | Bug Fixer | composer-2.5 | Applies plan changes, runs tests after each fix |
| 5 | Security Verifier | claude-opus-4-8 | Reviews fixed code for remaining vulnerabilities |
| 6 | Unit Test Generator | composer-2.5 | Generates FIRST-compliant regression tests |

---

## Model Selection Rationale

| Agent | Model | Justification |
|-------|-------|---------------|
| Bug Researcher | **claude-opus-4-8** | Deep reading of unfamiliar code requires strong reasoning to identify subtle logic bugs and security anti-patterns. A weaker model risks missing SEC-001's eval() or BUG-001's slice. |
| Research Verifier | **claude-opus-4-8** | Fact-checking demands precision: the model must navigate to exact line numbers, compare snippets byte-by-byte, and apply the quality rubric without hallucinating. Requires the same level as Researcher. |
| Bug Planner | **composer-2.5** | Creating before/after code blocks from verified findings is a structured, deterministic task. Composer-2.5 is fast and sufficient for this planning workload. |
| Bug Fixer | **composer-2.5** | Applying minimal, targeted code changes and running pytest is routine edit-verify work — no deep reasoning required. Speed matters for quick iteration. |
| Security Verifier | **claude-opus-4-8** | Security review requires adversarial thinking to imagine exploit scenarios, map to CWE classifications, and spot subtle issues (e.g. exception chaining leaking internals). Needs deep reasoning. |
| Unit Test Generator | **composer-2.5** | Generating pytest tests from a spec (fix-summary.md + FIRST skill) is a code-scaffolding task. Composer-2.5 produces clean Python quickly and cost-effectively. |

---

## Sample Application

`src/expense_tracker.py` is a minimal in-memory expense tracker with three functions:

| Function | Description |
|----------|-------------|
| `add_expense(category, amount, description)` | Records an expense |
| `get_total(category=None)` | Returns total (optionally filtered) |
| `get_expenses(category=None)` | Returns expense list (optionally filtered) |

### Seeded issues (pre-pipeline)

| ID | Type | Description |
|----|------|-------------|
| BUG-001 | Functional | `get_total()` used `EXPENSES[1:]` — first expense always skipped |
| BUG-002 | Functional | `get_expenses(category)` used `==` — case-sensitive category filter |
| SEC-001 | Security (CRITICAL) | `add_expense()` used `eval(amount)` — arbitrary code execution |

### After pipeline

All three issues resolved. Full test suite: **34 passed, 0 failed**.

---

## Pipeline Artifacts

All outputs are in `context/bugs/001/`:

| Artifact | Produced by | Description |
|----------|-------------|-------------|
| `research/codebase-research.md` | Bug Researcher | Bug and security findings with file:line refs |
| `research/verified-research.md` | Research Verifier | Fact-checked research with quality level |
| `implementation-plan.md` | Bug Planner | Before/after code for each fix |
| `fix-summary.md` | Bug Fixer | Applied changes + per-fix test results |
| `security-report.md` | Security Verifier | Post-fix security scan (PASS — 0 CRITICAL/HIGH) |
| `test-report.md` | Unit Test Generator | 16 generated FIRST-compliant tests; all pass |

---

## Skills

| Skill | Used by | Purpose |
|-------|---------|---------|
| `skills/research-quality-measurement.md` | Research Verifier | 4-level rubric (VERIFIED → UNVERIFIED) for research quality |
| `skills/unit-tests-FIRST.md` | Unit Test Generator | FIRST principles (Fast, Independent, Repeatable, Self-validating, Timely) |

---

## Repository Structure

```
homework-4/
├── README.md                        ← this file
├── HOWTORUN.md                      ← step-by-step run guide
├── run-pipeline.sh                  ← single-command entry point
├── run-pipeline.py                  ← Cursor SDK orchestrator
├── requirements.txt
├── pyproject.toml                   ← pytest config
├── agents/
│   ├── researcher.agent.md          ← supporting: Bug Researcher
│   ├── research-verifier.agent.md   ← required (Task 1)
│   ├── bug-planner.agent.md         ← supporting: Bug Planner
│   ├── bug-fixer.agent.md           ← required (Task 2)
│   ├── security-verifier.agent.md   ← required (Task 3)
│   └── unit-test-generator.agent.md ← required (Task 4)
├── skills/
│   ├── research-quality-measurement.md  ← Task 1.2
│   └── unit-tests-FIRST.md              ← Task 4.2
├── src/
│   ├── __init__.py
│   ├── expense_tracker.py           ← fixed application code
│   └── main.py                      ← CLI entry point
├── tests/
│   ├── conftest.py
│   ├── test_expense_tracker.py      ← 18 tests (core + bug regressions)
│   └── test_generated.py            ← 16 FIRST-compliant tests (generated by Unit Test Generator)
├── context/bugs/001/
│   ├── bug-context.md               ← seeded issue documentation
│   ├── research/
│   │   ├── codebase-research.md     ← Researcher output
│   │   └── verified-research.md     ← Verifier output
│   ├── implementation-plan.md       ← Planner output
│   ├── fix-summary.md               ← Fixer output
│   ├── security-report.md           ← Security Verifier output
│   └── test-report.md               ← Unit Test Generator output
└── docs/screenshots/                ← Pipeline run screenshots
```

---

## AI Tools Used

- **Cursor IDE** — agent definitions (`.agent.md`), skill-driven prompting
- **Cursor Python SDK** (`cursor-sdk`) — single-command pipeline orchestration
- **claude-opus-4** — reasoning-heavy agents (Research Verifier, Security Verifier,
  Bug Researcher)
- **composer-2.5** — routine code agents (Bug Planner, Bug Fixer, Unit Test Generator)

---

## How to Run

See [HOWTORUN.md](HOWTORUN.md) for full setup and execution instructions.

Quick start:
```bash
cd homework-4
export CURSOR_API_KEY=cursor_...
./run-pipeline.sh
```

Tests only (no API key needed):
```bash
pytest tests/ -v
```
