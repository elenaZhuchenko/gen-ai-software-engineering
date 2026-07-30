# Test Report — Expense Tracker (Run 001)

## Summary
- Functions targeted: `get_expenses`, `add_expense`, `get_total`
- Tests generated: 13
- Tests passed: 13 / 13 (full suite: 31 / 31)
- FIRST compliance: see assessment below

## Tests Generated

### TestGetExpensesBug003Fix
- `test_get_expenses_mutating_returned_dict_preserves_internal_amount_bug003` — covers BUG-003 fix (defensive dict copies, unfiltered)
- `test_get_expenses_filtered_dict_copy_is_independent_bug003` — covers BUG-003 fix (defensive dict copies, filtered)

### TestAddExpenseBug001Fix
- `test_add_expense_nan_amount_raises_value_error_bug001` — covers BUG-001 fix (reject NaN)
- `test_add_expense_positive_infinity_raises_value_error_bug001` — covers BUG-001 fix (reject +Infinity)
- `test_add_expense_negative_infinity_raises_value_error_bug001` — covers BUG-001 fix (reject -Infinity)
- `test_add_expense_finite_amount_is_accepted_bug001` — covers BUG-001 happy path

### TestAddExpenseBug002Fix
- `test_add_expense_empty_category_raises_value_error_bug002` — covers BUG-002 fix (reject empty category)
- `test_add_expense_whitespace_category_raises_value_error_bug002` — covers BUG-002 edge case (whitespace-only category)
- `test_add_expense_valid_category_is_accepted_bug002` — covers BUG-002 happy path

### TestGetExpensesBug002FilterFix
- `test_get_expenses_empty_string_filter_returns_empty_list_bug002` — covers BUG-002 fix (empty-string filter bypass)
- `test_get_expenses_none_returns_all_expenses_bug002` — covers BUG-002 happy path (`None` returns all)

### TestGetTotalBug002Fix
- `test_get_total_empty_string_returns_zero_not_full_sum_bug002` — covers BUG-002 fix (empty-string filter bypass)
- `test_get_total_none_returns_full_sum_bug002` — covers BUG-002 happy path (`None` sums all)

## FIRST Compliance Assessment

- [x] Fast        — all 13 generated tests complete in < 100 ms each; no network, disk I/O, or `time.sleep()`; full suite finishes in 0.03 s.
- [x] Independent — autouse `reset_expenses` fixture in `conftest.py` clears module state before and after every test; no test reads another test's data.
- [x] Repeatable  — no randomness, system time, or environment dependencies; expected values are hardcoded literals.
- [x] Self-validating — every test has ≥1 assert or `pytest.raises`; float comparisons use `pytest.approx`; failure messages name the bug ID and expected behaviour.
- [x] Timely      — tests target only functions changed in `fix-summary.md` (Run 001); no duplication of scenarios already covered in `test_expense_tracker.py` (list-copy independence, negative amounts, case-insensitive filter basics).

## Test Run Output
```
pytest tests/ -v
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

## References
- Fix summary: `context/bugs/001/fix-summary.md`
- FIRST skill: `skills/unit-tests-FIRST.md`
- Generated file: `tests/test_generated.py`
