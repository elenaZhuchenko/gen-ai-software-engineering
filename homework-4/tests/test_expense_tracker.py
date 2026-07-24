"""Core tests for src/expense_tracker.py.

These tests cover both the happy path and the behaviours that were broken
in the pre-pipeline (buggy) version of the code.  All tests must pass
against the post-pipeline (fixed) source.
"""
import pytest
from src.expense_tracker import add_expense, get_expenses, get_total


# ---------------------------------------------------------------------------
# add_expense
# ---------------------------------------------------------------------------

class TestAddExpense:
    def test_add_expense_returns_complete_record(self):
        e = add_expense("food", "9.99", "Lunch")
        assert e["id"] == 1
        assert e["category"] == "food"
        assert e["amount"] == pytest.approx(9.99)
        assert e["description"] == "Lunch"

    def test_add_multiple_expenses_increments_id(self):
        e1 = add_expense("food", "10.0", "Breakfast")
        e2 = add_expense("food", "20.0", "Dinner")
        assert e2["id"] == e1["id"] + 1

    def test_add_expense_integer_string_accepted(self):
        e = add_expense("transport", "5", "Bus")
        assert e["amount"] == pytest.approx(5.0)

    def test_add_expense_non_numeric_amount_raises_value_error(self):
        """SEC-001 fix: eval() replaced by float(); non-numeric input must raise."""
        with pytest.raises(ValueError, match="Invalid amount"):
            add_expense("food", "not-a-number", "Bad")

    def test_add_expense_negative_amount_raises_value_error(self):
        with pytest.raises(ValueError, match="non-negative"):
            add_expense("food", "-5.0", "Refund")

    def test_add_expense_code_injection_is_rejected(self):
        """SEC-001 regression: eval('__import__(\"os\").getcwd()') must not execute."""
        with pytest.raises(ValueError):
            add_expense("food", '__import__("os").getcwd()', "Injection attempt")


# ---------------------------------------------------------------------------
# get_total  (BUG-001 fixed: was EXPENSES[1:])
# ---------------------------------------------------------------------------

class TestGetTotal:
    def test_total_empty_store_returns_zero(self):
        assert get_total() == 0.0

    def test_total_single_expense_returns_its_amount(self):
        """BUG-001 regression: single expense must NOT be skipped."""
        add_expense("food", "15.00", "Lunch")
        assert get_total() == pytest.approx(15.0)

    def test_total_two_expenses_sums_both(self):
        """BUG-001 regression: first expense must be included in total."""
        add_expense("food", "10.0", "Breakfast")
        add_expense("food", "20.0", "Lunch")
        assert get_total() == pytest.approx(30.0)

    def test_total_multiple_categories_sums_all(self):
        add_expense("food", "10.0", "Breakfast")
        add_expense("food", "20.0", "Lunch")
        add_expense("transport", "5.0", "Bus")
        assert get_total() == pytest.approx(35.0)

    def test_total_by_category_sums_matching_only(self):
        add_expense("food", "10.0", "Breakfast")
        add_expense("food", "20.0", "Lunch")
        add_expense("transport", "5.0", "Bus")
        assert get_total("food") == pytest.approx(30.0)

    def test_total_by_category_zero_when_no_match(self):
        add_expense("food", "10.0", "Breakfast")
        assert get_total("transport") == 0.0


# ---------------------------------------------------------------------------
# get_expenses  (BUG-002 fixed: was case-sensitive)
# ---------------------------------------------------------------------------

class TestGetExpenses:
    def test_get_all_returns_all_expenses(self):
        add_expense("food", "10.0", "Breakfast")
        add_expense("transport", "5.0", "Bus")
        assert len(get_expenses()) == 2

    def test_filter_by_category_exact_case(self):
        add_expense("food", "10.0", "Breakfast")
        add_expense("transport", "5.0", "Bus")
        food = get_expenses("food")
        assert len(food) == 1
        assert food[0]["category"] == "food"

    def test_filter_by_category_uppercase_matches_lowercase(self):
        """BUG-002 regression: 'Food' must match expenses stored as 'food'."""
        add_expense("food", "10.0", "Breakfast")
        result = get_expenses("Food")
        assert len(result) == 1

    def test_filter_by_category_mixed_case_matches(self):
        """BUG-002 regression: 'FOOD' and 'fOoD' must match 'food'."""
        add_expense("food", "10.0", "Breakfast")
        assert len(get_expenses("FOOD")) == 1
        assert len(get_expenses("fOoD")) == 1

    def test_filter_no_match_returns_empty_list(self):
        add_expense("food", "10.0", "Breakfast")
        assert get_expenses("entertainment") == []

    def test_get_expenses_returns_independent_copy(self):
        """Mutating the returned list must not affect internal state."""
        add_expense("food", "10.0", "Breakfast")
        result = get_expenses()
        result.clear()
        assert len(get_expenses()) == 1
