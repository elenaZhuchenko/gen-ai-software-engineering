# Fix Summary — Expense Tracker (Run 001)

## Overall Status
COMPLETE — All three fixes applied per implementation plan; individual and full test suites passed (31/31).

## Changes Made

### Fix 1: BUG-003 — Return defensive dict copies from `get_expenses()`
- **File**: `src/expense_tracker.py`
- **Function**: `get_expenses`
- **Lines changed**: 81–84
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
- **Test command**: `pytest tests/test_expense_tracker.py::TestGetExpenses::test_get_expenses_returns_independent_copy -v`
- **Test result**: PASS
- **Test output** (first 15 lines):
  ```
  ============================= test session starts ==============================
  platform darwin -- Python 3.9.6, pytest-8.3.4, pluggy-1.6.0 -- /Library/Developer/CommandLineTools/usr/bin/python3
  cachedir: .pytest_cache
  rootdir: /Users/wildix/QA/gen-ai-software-engineering/homework-4
  configfile: pyproject.toml
  plugins: anyio-4.12.1, cov-6.0.0
  collecting ... collected 1 item

  tests/test_expense_tracker.py::TestGetExpenses::test_get_expenses_returns_independent_copy PASSED [100%]

  ============================== 1 passed in 0.02s ===============================
  ```

### Fix 2: BUG-001 — Reject `NaN` and `Infinity` in `add_expense()`
- **File**: `src/expense_tracker.py`
- **Function**: `add_expense`
- **Lines changed**: 12, 46–47
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
- **Test command**: `pytest tests/test_expense_tracker.py::TestAddExpense::test_add_expense_negative_amount_raises_value_error -v`
- **Test result**: PASS
- **Test output** (first 15 lines):
  ```
  ============================= test session starts ==============================
  platform darwin -- Python 3.9.6, pytest-8.3.4, pluggy-1.6.0 -- /Library/Developer/CommandLineTools/usr/bin/python3
  cachedir: .pytest_cache
  rootdir: /Users/wildix/QA/gen-ai-software-engineering/homework-4
  configfile: pyproject.toml
  plugins: anyio-4.12.1, cov-6.0.0
  collecting ... collected 1 item

  tests/test_expense_tracker.py::TestAddExpense::test_add_expense_negative_amount_raises_value_error PASSED [100%]

  ============================== 1 passed in 0.01s ===============================
  ```

### Fix 3: BUG-002 — Reject blank categories and fix empty-string filter bypass
- **File**: `src/expense_tracker.py`
- **Function**: `add_expense`, `get_total`, `get_expenses`
- **Lines changed**: 49–50, 68–69, 81–83
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
- **Test command**: `pytest tests/test_expense_tracker.py::TestGetExpenses::test_filter_by_category_exact_case -v`
- **Test result**: PASS
- **Test output** (first 15 lines):
  ```
  ============================= test session starts ==============================
  platform darwin -- Python 3.9.6, pytest-8.3.4, pluggy-1.6.0 -- /Library/Developer/CommandLineTools/usr/bin/python3
  cachedir: .pytest_cache
  rootdir: /Users/wildix/QA/gen-ai-software-engineering/homework-4
  configfile: pyproject.toml
  plugins: anyio-4.12.1, cov-6.0.0
  collecting ... collected 1 item

  tests/test_expense_tracker.py::TestGetExpenses::test_filter_by_category_exact_case PASSED [100%]

  ============================== 1 passed in 0.01s ===============================
  ```

## Full Test Suite Result
PASS — 31 passed, 0 failed, 0 errors

```
============================= test session starts ==============================
platform darwin -- Python 3.9.6, pytest-8.3.4, pluggy-1.6.0 -- /Library/Developer/CommandLineTools/usr/bin/python3
cachedir: .pytest_cache
rootdir: /Users/wildix/QA/gen-ai-software-engineering/homework-4
configfile: pyproject.toml
plugins: anyio-4.12.1, cov-6.0.0
collecting ... collected 31 items

tests/test_expense_tracker.py::TestAddExpense::test_add_expense_returns_complete_record PASSED [  3%]
tests/test_expense_tracker.py::TestAddExpense::test_add_multiple_expenses_increments_id PASSED [  6%]
tests/test_expense_tracker.py::TestAddExpense::test_add_expense_integer_string_accepted PASSED [  9%]
tests/test_expense_tracker.py::TestAddExpense::test_add_expense_non_numeric_amount_raises_value_error PASSED [ 12%]
tests/test_expense_tracker.py::TestAddExpense::test_add_expense_negative_amount_raises_value_error PASSED [ 16%]
tests/test_expense_tracker.py::TestAddExpense::test_add_expense_code_injection_is_rejected PASSED [ 19%]
tests/test_expense_tracker.py::TestGetTotal::test_total_empty_store_returns_zero PASSED [ 22%]
tests/test_expense_tracker.py::TestGetTotal::test_total_single_expense_returns_its_amount PASSED [ 25%]
tests/test_expense_tracker.py::TestGetTotal::test_total_two_expenses_sums_both PASSED [ 29%]
tests/test_expense_tracker.py::TestGetTotal::test_total_multiple_categories_sums_all PASSED [ 32%]
tests/test_expense_tracker.py::TestGetTotal::test_total_by_category_sums_matching_only PASSED [ 35%]
tests/test_expense_tracker.py::TestGetTotal::test_total_by_category_zero_when_no_match PASSED [ 38%]
tests/test_expense_tracker.py::TestGetExpenses::test_get_all_returns_all_expenses PASSED [ 41%]
tests/test_expense_tracker.py::TestGetExpenses::test_filter_by_category_exact_case PASSED [ 45%]
tests/test_expense_tracker.py::TestGetExpenses::test_filter_by_category_uppercase_matches_lowercase PASSED [ 48%]
tests/test_expense_tracker.py::TestGetExpenses::test_filter_by_category_mixed_case_matches PASSED [ 51%]
tests/test_expense_tracker.py::TestGetExpenses::test_filter_no_match_returns_empty_list PASSED [ 54%]
tests/test_expense_tracker.py::TestGetExpenses::test_get_expenses_returns_independent_copy PASSED [ 58%]
tests/test_generated.py::TestGetExpensesBug003Fix::test_get_expenses_mutating_returned_dict_preserves_internal_amount_bug003 PASSED [ 61%]
tests/test_generated.py::TestGetExpensesBug003Fix::test_get_expenses_filtered_dict_copy_is_independent_bug003 PASSED [ 64%]
tests/test_generated.py::TestAddExpenseBug001Fix::test_add_expense_nan_amount_raises_value_error_bug001 PASSED [ 67%]
tests/test_generated.py::TestAddExpenseBug001Fix::test_add_expense_positive_infinity_raises_value_error_bug001 PASSED [ 70%]
tests/test_generated.py::TestAddExpenseBug001Fix::test_add_expense_negative_infinity_raises_value_error_bug001 PASSED [ 74%]
tests/test_generated.py::TestAddExpenseBug001Fix::test_add_expense_finite_amount_is_accepted_bug001 PASSED [ 77%]
tests/test_generated.py::TestAddExpenseBug002Fix::test_add_expense_empty_category_raises_value_error_bug002 PASSED [ 80%]
tests/test_generated.py::TestAddExpenseBug002Fix::test_add_expense_whitespace_category_raises_value_error_bug002 PASSED [ 83%]
tests/test_generated.py::TestAddExpenseBug002Fix::test_add_expense_valid_category_is_accepted_bug002 PASSED [ 87%]
tests/test_generated.py::TestGetExpensesBug002FilterFix::test_get_expenses_empty_string_filter_returns_empty_list_bug002 PASSED [ 90%]
tests/test_generated.py::TestGetExpensesBug002FilterFix::test_get_expenses_none_returns_all_expenses_bug002 PASSED [ 93%]
tests/test_generated.py::TestGetTotalBug002Fix::test_get_total_empty_string_returns_zero_not_full_sum_bug002 PASSED [ 96%]
tests/test_generated.py::TestGetTotalBug002Fix::test_get_total_none_returns_full_sum_bug002 PASSED [100%]

============================== 31 passed in 0.03s ==============================
```

## Manual Verification Steps
1. Run: `python -m src.main`
2. Enter: `add food 15.00 Lunch`
3. Enter: `add food 10.00 Breakfast`
4. Enter: `total` — should display `$25.00`
5. Enter: `list Food` — should list both food expenses (case-insensitive filter)
6. Enter: `add food nan Poison` — should show error
   `Amount must be a finite non-negative number` (BUG-001 fix verification)
7. Enter: `add food inf Poison` — should show the same finite-number error
   (BUG-001 fix verification)
8. Enter: `total` — should still display `$25.00`, proving no `NaN`/`inf`
   was stored (BUG-001 fix verification)
9. Enter: `add test __import__('os').getcwd() Injection` — should show error
   `Invalid amount` (safe parsing; SEC-001 eval() vector remains closed)
10. Enter: `quit`

> BUG-002 (blank-category rejection / empty-string filter) and BUG-003
> (defensive dict copies) are not directly reachable through the REPL parser and
> are covered by the generated regression tests in `tests/test_generated.py`.

## References
- Plan: `context/bugs/001/implementation-plan.md`
- Modified files: `src/expense_tracker.py`
