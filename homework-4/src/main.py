"""Expense Tracker CLI — entry point.

Usage:
    python -m src.main

Commands (interactive REPL):
    add <category> <amount> <description>   Add an expense
    list [category]                         List expenses (optionally filtered)
    total [category]                        Show total (optionally by category)
    quit                                    Exit
"""
from __future__ import annotations

import sys
from src.expense_tracker import add_expense, get_expenses, get_total


BANNER = """
╔══════════════════════════════════════╗
║        Expense Tracker v1.0          ║
╠══════════════════════════════════════╣
║  add <cat> <amount> <desc>           ║
║  list [category]                     ║
║  total [category]                    ║
║  quit                                ║
╚══════════════════════════════════════╝
"""


def run_repl() -> int:
    """Interactive command loop. Returns exit code."""
    print(BANNER)
    while True:
        try:
            raw = input("tracker> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            return 0

        if not raw:
            continue

        parts = raw.split(maxsplit=3)
        cmd = parts[0].lower()

        if cmd == "quit":
            print("Goodbye!")
            return 0

        elif cmd == "add":
            if len(parts) < 4:
                print("Usage: add <category> <amount> <description>")
                continue
            category, amount, description = parts[1], parts[2], parts[3]
            try:
                expense = add_expense(category, amount, description)
                print(
                    f"  ✓ #{expense['id']:>3} | {expense['category']:<12} | "
                    f"${expense['amount']:>8.2f} | {expense['description']}"
                )
            except ValueError as exc:
                print(f"  Error: {exc}")

        elif cmd == "list":
            category = parts[1] if len(parts) > 1 else None
            expenses = get_expenses(category)
            if not expenses:
                print("  (no expenses found)")
            else:
                for e in expenses:
                    print(
                        f"  #{e['id']:>3} | {e['category']:<12} | "
                        f"${e['amount']:>8.2f} | {e['description']}"
                    )

        elif cmd == "total":
            category = parts[1] if len(parts) > 1 else None
            total = get_total(category)
            label = f"category '{category}'" if category else "all categories"
            print(f"  Total ({label}): ${total:.2f}")

        else:
            print(f"  Unknown command: {cmd!r}. Try: add, list, total, quit")

    return 0


def main() -> int:
    return run_repl()


if __name__ == "__main__":
    sys.exit(main())
