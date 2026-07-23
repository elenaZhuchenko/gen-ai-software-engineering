"""Expense Tracker — core business logic.

Pipeline state: POST-FIX (bugs resolved by the 4-agent pipeline).

Bugs that existed BEFORE the pipeline (documented in context/bugs/001/bug-context.md):
  BUG-001: get_total() used ``EXPENSES[1:]`` — skipped the first expense in total.
  BUG-002: get_expenses(category) used ``==`` — case-sensitive category filter.
  SEC-001: add_expense() used ``eval(amount)`` — arbitrary code execution via user input.
"""
from __future__ import annotations

from typing import Optional

# In-memory store (shared module state; reset between tests via clear_expenses()).
EXPENSES: list[dict] = []
_next_id: int = 1


def add_expense(category: str, amount: str, description: str) -> dict:
    """Add a new expense record.

    Args:
        category:    Expense category (e.g. ``"food"``, ``"transport"``).
        amount:      Numeric string representing the expense amount.
        description: Short human-readable description.

    Returns:
        The newly created expense dict.

    Raises:
        ValueError: If ``amount`` is not a valid non-negative number.

    SEC-001 fix: Replaced ``eval(amount)`` with ``float()`` + explicit validation.
    """
    global _next_id

    # SEC-001 FIX: safe numeric conversion instead of eval()
    try:
        value = float(amount)
    except (ValueError, TypeError) as exc:
        raise ValueError(
            f"Invalid amount {amount!r}: must be a numeric value (e.g. '9.99')."
        ) from exc

    if value < 0:
        raise ValueError(f"Amount must be non-negative, got {value}.")

    expense: dict = {
        "id": _next_id,
        "category": category,
        "amount": value,
        "description": description,
    }
    _next_id += 1
    EXPENSES.append(expense)
    return expense


def get_total(category: Optional[str] = None) -> float:
    """Return the sum of all expenses, optionally filtered by category.

    BUG-001 fix: was ``EXPENSES[1:]`` (skipped first expense); now uses the full list.
    """
    if category:
        return sum(e["amount"] for e in get_expenses(category))

    # BUG-001 FIX: iterate all expenses, not EXPENSES[1:]
    return sum(e["amount"] for e in EXPENSES)


def get_expenses(category: Optional[str] = None) -> list[dict]:
    """Return all expenses, optionally filtered by category.

    BUG-002 fix: was ``e["category"] == category`` (case-sensitive);
    now compares lowercase on both sides.
    """
    if category:
        # BUG-002 FIX: case-insensitive comparison
        return [e for e in EXPENSES if e["category"].lower() == category.lower()]
    return list(EXPENSES)


def clear_expenses() -> None:
    """Clear all stored expenses and reset the ID counter.

    Used by test fixtures to ensure test isolation.
    """
    global _next_id
    EXPENSES.clear()
    _next_id = 1
