# Bug Context — Expense Tracker (Pipeline Run 001)

## Application Description

A minimal Python CLI expense tracker (`src/expense_tracker.py`, `src/main.py`).
Users can add expenses, list them by category, and compute totals.

The application was intentionally seeded with defects so the 4-agent pipeline has
concrete work to discover, verify, plan, fix, security-review, and test. The seeds
fall into **two tiers**, mirroring the Bug Researcher's report
(`research/codebase-research.md`):

1. **Originally seeded issues** — the first, most obvious defects (including a
   CRITICAL `eval()` RCE). These were remediated in an earlier hardening pass and
   are retained here for traceability; the Security Verifier re-confirms the RCE is
   closed in `security-report.md`.
2. **Run 001 findings** — subtler defects that survived the first pass and were
   discovered, fixed, and regression-tested by **this** pipeline run.

---

## Tier 1 — Originally Seeded Issues (remediated in an earlier pass)

These IDs carry an asterisk (`*`) to distinguish them from the run-001 active
findings below, matching the convention used in `research/codebase-research.md`.

| ID       | Type              | Severity | Original defect                                   | Current source (fixed)                                                  |
|----------|-------------------|----------|---------------------------------------------------|-------------------------------------------------------------------------|
| BUG-001* | Functional        | HIGH     | `get_total()` used `EXPENSES[1:]` — first expense skipped | `return sum(e["amount"] for e in EXPENSES)`                      |
| BUG-002* | Functional        | MEDIUM   | `get_expenses()` used `==` — case-sensitive filter | `... if e["category"].lower() == category.lower()`                      |
| SEC-001* | Security (CWE-94) | CRITICAL | `add_expense()` used `eval(amount)` — arbitrary code execution | `value = float(amount)` guarded by `try/except (ValueError, TypeError)` |

**SEC-001\* proof-of-concept (pre-fix):**
```
add food __import__('os').system('id') Lunch
```
An attacker-supplied `amount` was passed straight to `eval()`, allowing arbitrary
Python execution. The fix replaces `eval()` with `float()` + explicit validation,
closing the RCE. The Security Verifier confirms this as **RESOLVED** (see
`security-report.md`, FINDING-001).

---

## Tier 2 — Run 001 Findings (discovered & fixed by this pipeline run)

These are the active defects the pipeline actually processed end-to-end
(research → verify → plan → fix → security review → tests) in run 001.

### BUG-001 — `add_expense()` accepts `NaN` / `Infinity`, poisoning all totals

| Field       | Value |
|-------------|-------|
| **File**    | `src/expense_tracker.py` |
| **Function**| `add_expense()` |
| **Line**    | 39 (conversion) / 45 (insufficient guard), pre-fix |
| **Severity**| MEDIUM |

**Buggy code (pre-fix):**
```python
value = float(amount)
...
if value < 0:
    raise ValueError(f"Amount must be non-negative, got {value}.")
```

**Problem:** `float("nan")`, `float("inf")`, `float("-inf")` all parse
successfully, and `float("nan") < 0` / `float("inf") < 0` are both `False`, so the
only guard is bypassed. A single stored `NaN` makes `get_total()` return `nan` for
**every** subsequent call; a stored `inf` makes totals `inf`.

**Impact:** Data-integrity defect — one poisoned record corrupts all reporting.

**Fix applied:** `if not math.isfinite(value) or value < 0: raise ValueError(...)`.

---

### BUG-002 — Blank category accepted; empty-string filter silently disables filtering

| Field       | Value |
|-------------|-------|
| **File**    | `src/expense_tracker.py` |
| **Function**| `add_expense()`, `get_total()`, `get_expenses()` |
| **Line**    | 48–53 (storage) / 64 / 77 (falsy filter), pre-fix |
| **Severity**| LOW |

**Problem:** `add_expense()` stored `category`/`description` with no validation, so
`""` or whitespace was accepted as a category. Separately, `get_total()` and
`get_expenses()` gated filtering on `if category:` — a falsy test — so an
empty-string query was treated as "no filter" (returning **all** expenses) rather
than "match the empty category".

**Fix applied:** reject blank categories at input
(`if not category or not category.strip(): raise ValueError(...)`) and replace the
falsy filter test with `if category is not None:` in both `get_total()` and
`get_expenses()`.

---

### BUG-003 — `get_expenses()` returns live dict references (shallow copy)

| Field       | Value |
|-------------|-------|
| **File**    | `src/expense_tracker.py` |
| **Function**| `get_expenses()` |
| **Line**    | 79–80, pre-fix |
| **Severity**| LOW |

**Problem:** Both return paths returned a new *list* but the same dict objects held
in the module-level `EXPENSES` store. A caller mutating a returned dict (e.g.
`get_expenses()[0]["amount"] = 999`) silently corrupted the canonical store.

**Fix applied:** defensively copy each record —
`return [dict(e) for e in EXPENSES if ...]` and `return [dict(e) for e in EXPENSES]`.

---

### SEC-001 (INFO) — Untrusted `amount` reflected in error message (CWE-209)

| Field       | Value |
|-------------|-------|
| **File**    | `src/expense_tracker.py` |
| **Function**| `add_expense()` |
| **Line**    | 42 |
| **Severity**| INFO (no change required for a local CLI) |

**Note:** The invalid-amount error interpolates the raw user input via
`{amount!r}`. In a local CLI there is no meaningful trust boundary, so this is
informational only. It is flagged for completeness in case the logic is ever
reused behind a network service. Per verified research, **no code change** is
required.

---

## Post-Pipeline State

After the 4-agent pipeline ran (run 001):

| Issue    | Tier | Status   | Fix applied |
|----------|------|----------|-------------|
| SEC-001* | 1    | RESOLVED | `eval(amount)` → `float(amount)` + validation (re-confirmed by Security Verifier) |
| BUG-001* | 1    | RESOLVED | `EXPENSES[1:]` → `EXPENSES` |
| BUG-002* | 1    | RESOLVED | `== category` → `.lower() == category.lower()` |
| BUG-001  | 2    | RESOLVED | added `math.isfinite()` guard |
| BUG-002  | 2    | RESOLVED | blank-category rejection + `if category is not None` |
| BUG-003  | 2    | RESOLVED | `list(EXPENSES)` → `[dict(e) for e in EXPENSES]` |
| SEC-001  | 2    | INFO     | no change required (CWE-209, CLI context) |

Full suite: **31 passed, 0 failed**. See `fix-summary.md` for per-change details,
`security-report.md` for the post-fix security verdict (PASS — 0 CRITICAL / 0 HIGH),
and `test-report.md` for the 13 generated FIRST-compliant regression tests.
