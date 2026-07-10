"""In-memory ticket store (thread-safe for single-process use)."""
from __future__ import annotations

from models import Ticket


class TicketStore:
    def __init__(self) -> None:
        self._tickets: dict[str, Ticket] = {}

    def create(self, ticket: Ticket) -> Ticket:
        self._tickets[ticket.id] = ticket
        return ticket

    def get(self, ticket_id: str) -> Ticket | None:
        return self._tickets.get(ticket_id)

    def list(
        self,
        category: str | None = None,
        priority: str | None = None,
        status: str | None = None,
        customer_id: str | None = None,
    ) -> list[Ticket]:
        results = list(self._tickets.values())
        if category:
            results = [t for t in results if t.category and t.category.value == category]
        if priority:
            results = [t for t in results if t.priority and t.priority.value == priority]
        if status:
            results = [t for t in results if t.status.value == status]
        if customer_id:
            results = [t for t in results if t.customer_id == customer_id]
        return results

    def update(self, ticket: Ticket) -> Ticket:
        self._tickets[ticket.id] = ticket
        return ticket

    def delete(self, ticket_id: str) -> bool:
        if ticket_id in self._tickets:
            del self._tickets[ticket_id]
            return True
        return False

    def clear(self) -> None:
        self._tickets.clear()


store = TicketStore()
