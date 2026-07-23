# How to Run — Homework 4: 4-Agent Pipeline

## Prerequisites

| Requirement | Version | Purpose |
|-------------|---------|---------|
| Python | ≥ 3.10 | `cursor-sdk` minimum requirement |
| pip | ≥ 22 | Package installation |
| Cursor API key | — | Required to invoke SDK agents |

> **Tests only** (no pipeline execution): Python 3.9+ is sufficient.

---

## 1. Clone / Navigate

```bash
cd /path/to/gen-ai-software-engineering/homework-4
```

---

## 2. Set Up Python 3.10+ and Install Dependencies

`cursor-sdk` requires **Python 3.10 or later**. If you only have the macOS system
Python (3.9), install Python 3.12 first:

```bash
# macOS — install Python 3.12 via Homebrew
brew install python@3.12
```

Then create a virtual environment inside the homework-4 folder and install deps:

```bash
python3.12 -m venv .venv          # create venv (one-time)
.venv/bin/pip install -r requirements.txt
```

`run-pipeline.sh` automatically detects and uses `.venv/bin/python` if it exists,
so no activation step is needed when running via the shell script.

This installs:
- `cursor-sdk` — Cursor Python SDK for agent orchestration
- `PyYAML` — reads frontmatter from `*.agent.md` files
- `pytest`, `pytest-cov` — test runner

> **Tests only** (no pipeline): the system Python 3.9 works fine.
> ```bash
> /usr/bin/python3 -m pytest tests/ -v
> ```

---

## 3. Set Your Cursor API Key

Get your key from [cursor.com/dashboard/integrations](https://cursor.com/dashboard/integrations).

```bash
export CURSOR_API_KEY=cursor_...
```

> The key is read from the environment; it is never hard-coded or logged.

---

## 4. Run the Full Pipeline (single command)

```bash
./run-pipeline.sh
```

Or equivalently:

```bash
python run-pipeline.py
```

**What happens:**

| Step | Agent | Model | Output |
|------|-------|-------|--------|
| 1 | Bug Researcher | claude-opus-4 | `context/bugs/001/research/codebase-research.md` |
| 2 | Research Verifier | claude-opus-4 | `context/bugs/001/research/verified-research.md` |
| 3 | Bug Planner | composer-2.5 | `context/bugs/001/implementation-plan.md` |
| 4 | Bug Fixer | composer-2.5 | `context/bugs/001/fix-summary.md` + patches to `src/` |
| 5 | Security Verifier | claude-opus-4 | `context/bugs/001/security-report.md` |
| 6 | Unit Test Generator | composer-2.5 | `tests/test_generated.py` + `context/bugs/001/test-report.md` |

The orchestrator validates each output artifact before proceeding. A failed stage
stops the pipeline and reports which stage failed.

### Dry run (no API calls)

Validates agent file parsing and skill loading without making any API calls:

```bash
./run-pipeline.sh --dry-run
```

### Resume from a specific stage

If the pipeline failed at stage 4, restart from there:

```bash
python run-pipeline.py --from-stage 4
```

---

## 5. Run Tests

After the pipeline completes, verify the fixes:

```bash
pytest tests/ -v
```

Expected result: **34 passed, 0 failed**.

With coverage:

```bash
pytest tests/ -v --cov=src --cov-report=term-missing
```

---

## 6. Run the Application Manually

```bash
python -m src.main
```

Try the following commands in the interactive REPL:

```
tracker> add food 15.00 Lunch
tracker> add food 10.00 Breakfast
tracker> add transport 3.50 Bus
tracker> total
  Total (all categories): $28.50
tracker> total food
  Total (category 'food'): $25.00
tracker> list Food
  #1  food          $   15.00 | Lunch
  #2  food          $   10.00 | Breakfast
tracker> add hack __import__('os').getcwd() Injection
  Error: Invalid amount '__import__(...)': must be a numeric value (e.g. '9.99').
tracker> quit
```

---

## 7. Validate Pipeline Configuration (without running)

Verify all agent files and skills are present and parseable:

```bash
python run-pipeline.py --dry-run
```

Expected output:

```
==============================
  4-Agent Bug/Security/Test Pipeline
==============================
  Working directory : …/homework-4
  Dry run           : True
  Starting at stage : 1
…
[1/6] Bug Researcher
  Agent  : researcher.agent.md
  Model  : claude-opus-4
  Skills : (none)
  → [DRY RUN] skipping API call
…
Pipeline completed successfully ✓
```

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `cursor-sdk is not installed` | Run `pip install cursor-sdk` (requires Python 3.10+) |
| `CURSOR_API_KEY not set` | `export CURSOR_API_KEY=cursor_...` |
| `Agent startup failed (retryable=False)` | Check API key validity at cursor.com/dashboard |
| `Expected output not found` | Run `python run-pipeline.py --from-stage N` to re-run that stage |
| `python: command not found` in shell script | The script auto-detects `python3`; ensure Python 3.10+ is on your PATH |
| Tests fail with `ModuleNotFoundError: src` | Run `pytest` from the `homework-4/` directory (pyproject.toml sets pythonpath) |

---

## File Locations

| Item | Path |
|------|------|
| Orchestrator script | `run-pipeline.py` |
| Shell wrapper | `run-pipeline.sh` |
| Agent definitions | `agents/*.agent.md` |
| Skills | `skills/*.md` |
| Pipeline artifacts | `context/bugs/001/` |
| Application source | `src/expense_tracker.py` |
| Tests | `tests/` |
| Screenshots | `docs/screenshots/` |
