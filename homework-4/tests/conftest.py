"""Shared pytest fixtures for the Expense Tracker test suite."""
import pytest
from src.expense_tracker import clear_expenses


@pytest.fixture(autouse=True)
def reset_expenses():
    """Ensure a clean expense store before and after every test.

    This fixture satisfies the FIRST principle of Independence:
    no test depends on state left by a previous test.
    """
    clear_expenses()
    yield
    clear_expenses()
