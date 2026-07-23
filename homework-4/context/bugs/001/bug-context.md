# Bug Context — Expense Tracker (Pipeline Run 001)

## Application Description

A minimal Python CLI expense tracker (`src/expense_tracker.py`, `src/main.py`).
Users can add expenses, list them by category, and compute totals.

---

## Seeded Issues (Pre-Pipeline State)

The following bugs and security vulnerabilities were intentionally planted in the
original version of `src/expense_tracker.py` for the 4-agent pipeline to discover
and fix.

---

### BUG-001 — Off-by-one in `get_total()`

| Field       | Value |
|-------------|-------|
| **File**    | `src/expense_tracker.py` |
| **Function**| `get_total()` |
| **Line**    | ~40 (pre-fix) |
| **Severity**| HIGH |

**Buggy code:**
```python
def get_total(category=None):
    if category:
        matching = get_expenses(category)
        return sum(e["amount"] for e in matching)
    # BUG: EXPENSES[1:] skips the very first expense
    return sum(e["amount"] for e in EXPENSES[1:])
```

**Expected behaviour:** `get_total()` returns the sum of ALL stored expenses.

**Actual behaviour (before fix):** Returns the sum of all expenses *except the first one*.
If only one expense exists, returns `0.0`.

**Impact:** Users see incorrect totals — every report under-counts by the first expense amount.

---

### BUG-002 — Case-sensitive category filter in `get_expenses()`

| Field       | Value |
|-------------|-------|
| **File**    | `src/expense_tracker.py` |
| **Function**| `get_expenses()` |
| **Line**    | ~52 (pre-fix) |
| **Severity**| MEDIUM |

**Buggy code:**
```python
def get_expenses(category=None):
    if category:
        # BUG: exact-case match — 'Food' won't find 'food'
        return [e for e in EXPENSES if e["category"] == category]
    return list(EXPENSES)
```

**Expected behaviour:** `get_expenses("Food")` returns all expenses whose category is
`"food"`, `"Food"`, `"FOOD"`, etc. (case-insensitive).

**Actual behaviour (before fix):** Only returns expenses whose category string is
byte-for-byte identical to the filter. `get_expenses("Food")` returns nothing when
expenses were added with category `"food"`.

**Impact:** Filtering and per-category totals silently return empty results when
capitalisation differs.

---

### SEC-001 — Code injection via `eval()` in `add_expense()`

| Field       | Value |
|-------------|-------|
| **File**    | `src/expense_tracker.py` |
| **Function**| `add_expense()` |
| **Line**    | ~22 (pre-fix) |
| **Severity**| CRITICAL |
| **CWE**     | CWE-78 / CWE-94 (Code Injection) |

**Vulnerable code:**
```python
def add_expense(category, amount, description):
    # SECURITY ISSUE: eval() on unsanitised user input
    value = eval(amount)   # allows arbitrary Python expression execution
    ...
```

**Impact:** Any caller passing a malicious string as `amount` can execute arbitrary
Python code in the server/CLI process — e.g. reading files, spawning shells, or
exfiltrating environment variables.

**Proof-of-concept payload:**
```
add food __import__('os').system('id') Lunch
```

**Fix applied:** Replaced with `float(amount)` guarded by `try/except ValueError`.

---

## Post-Pipeline State

After the 4-agent pipeline ran:

| Issue   | Status   | Fix applied |
|---------|----------|-------------|
| BUG-001 | RESOLVED | `EXPENSES[1:]` → `EXPENSES` |
| BUG-002 | RESOLVED | `== category` → `.lower() == category.lower()` |
| SEC-001 | RESOLVED | `eval(amount)` → `float(amount)` + validation |

All tests pass. See `fix-summary.md` for per-change details.
