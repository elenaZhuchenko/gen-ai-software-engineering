# Implementation Plan — Expense Tracker (Run 001)

## Overview

Three confirmed functional defects in `src/expense_tracker.py` will be fixed:
non-finite `NaN`/`Infinity` amounts that poison totals (BUG-001), empty/blank
category acceptance and falsy filter bypass (BUG-002), and shallow-copy aliasing
in `get_expenses()` return values (BUG-003). SEC-001 (INFO — raw input echoed in
error messages) requires no change per verified research. Fixes are ordered
safest-first: defensive copies first, then input validation, then multi-site
filter semantics.

## Fixes

### Fix 1: BUG-003 — Return defensive dict copies from `get_expenses()`

- **File**: `src/expense_tracker.py`
- **Function**: `get_expenses`
- **Lines**: 77–80
- **Change type**: Bug fix
- **Before**:
  ```python
      if category:
          # BUG-002 FIX: case-insensitive comparison
          return [e for e in EXPENSES if e["category"].lower() == category.lower()]
      return list(EXPENSES)
  ```
- **After**:
  ```python
      if category:
          # BUG-002 FIX: case-insensitive comparison
          return [dict(e) for e in EXPENSES if e["category"].lower() == category.lower()]
      return [dict(e) for e in EXPENSES]
  ```
- **Rationale**: Wrapping each stored expense in `dict(e)` breaks aliasing so callers cannot mutate internal state through the returned list.
- **Test command**: `pytest tests/test_expense_tracker.py::TestGetExpenses::test_get_expenses_returns_independent_copy -v`
- **Expected result**: PASS

### Fix 2: BUG-001 — Reject `NaN` and `Infinity` in `add_expense()`

- **File**: `src/expense_tracker.py`
- **Function**: `add_expense`
- **Lines**: 12, 45–46
- **Change type**: Bug fix
- **Before**:
  ```python
  from typing import Optional
  ```
  ```python
      if value < 0:
          raise ValueError(f"Amount must be non-negative, got {value}.")
  ```
- **After**:
  ```python
  import math
  from typing import Optional
  ```
  ```python
      if not math.isfinite(value) or value < 0:
          raise ValueError(f"Amount must be a finite non-negative number, got {value}.")
  ```
- **Rationale**: `float("nan")` and `float("inf")` bypass `< 0`; `math.isfinite()` rejects all non-finite values before storage.
- **Test command**: `pytest tests/test_expense_tracker.py::TestAddExpense::test_add_expense_negative_amount_raises_value_error -v`
- **Expected result**: PASS

### Fix 3: BUG-002 — Reject blank categories and fix empty-string filter bypass

- **File**: `src/expense_tracker.py`
- **Function**: `add_expense`, `get_total`, `get_expenses`
- **Lines**: 47–48 (post Fix 2), 65–66 (post Fix 2), 78–80 (post Fix 1)
- **Change type**: Bug fix
- **Before**:
  ```python
      if not math.isfinite(value) or value < 0:
          raise ValueError(f"Amount must be a finite non-negative number, got {value}.")

      expense: dict = {
  ```
  ```python
      if category:
          return sum(e["amount"] for e in get_expenses(category))
  ```
  ```python
      if category:
          # BUG-002 FIX: case-insensitive comparison
          return [dict(e) for e in EXPENSES if e["category"].lower() == category.lower()]
  ```
- **After**:
  ```python
      if not math.isfinite(value) or value < 0:
          raise ValueError(f"Amount must be a finite non-negative number, got {value}.")

      if not category or not category.strip():
          raise ValueError("Category must be a non-empty string.")

      expense: dict = {
  ```
  ```python
      if category is not None:
          return sum(e["amount"] for e in get_expenses(category))
  ```
  ```python
      if category is not None:
          # BUG-002 FIX: case-insensitive comparison
          return [dict(e) for e in EXPENSES if e["category"].lower() == category.lower()]
  ```
- **Rationale**: Blank categories are rejected at input time, and `if category is not None` replaces the falsy check so an empty-string filter is not silently treated as "no filter".
- **Test command**: `pytest tests/test_expense_tracker.py::TestGetExpenses::test_filter_by_category_exact_case -v`
- **Expected result**: PASS

## Full Test Suite Verification

After all individual fixes are applied:

```
pytest tests/ -v
```

Expected: all tests PASS (31 passed).

## References

- Verified research: `context/bugs/001/research/verified-research.md`
