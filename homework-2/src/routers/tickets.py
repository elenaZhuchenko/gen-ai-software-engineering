"""Ticket CRUD router + auto-classify endpoint."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status

import database
from models import (
    AutoClassifyRequest,
    Category,
    Priority,
    Status,
    Ticket,
    TicketCreate,
    TicketListResponse,
    TicketUpdate,
)
from services.classifier import classify

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tickets", tags=["tickets"])


# ─── POST /tickets ────────────────────────────────────────────────────────────

@router.post("", response_model=Ticket, status_code=status.HTTP_201_CREATED)
def create_ticket(payload: TicketCreate) -> Ticket:
    ticket = Ticket(
        customer_id=payload.customer_id,
        customer_email=payload.customer_email,
        customer_name=payload.customer_name,
        subject=payload.subject,
        description=payload.description,
        category=payload.category,
        priority=payload.priority,
        status=payload.status,
        assigned_to=payload.assigned_to,
        tags=payload.tags,
        metadata=payload.metadata,
    )

    if payload.auto_classify:
        result = classify(ticket)
        ticket.classification = result
        if ticket.category is None:
            ticket.category = result.category
        if ticket.priority is None:
            ticket.priority = result.priority

    database.store.create(ticket)
    logger.info("created ticket id=%s", ticket.id)
    return ticket


# ─── GET /tickets ─────────────────────────────────────────────────────────────

@router.get("", response_model=TicketListResponse)
def list_tickets(
    category: Optional[Category] = Query(default=None),
    priority: Optional[Priority] = Query(default=None),
    status: Optional[Status] = Query(default=None),
    customer_id: Optional[str] = Query(default=None),
) -> TicketListResponse:
    tickets = database.store.list(
        category=category.value if category else None,
        priority=priority.value if priority else None,
        status=status.value if status else None,
        customer_id=customer_id,
    )
    return TicketListResponse(total=len(tickets), tickets=tickets)


# ─── GET /tickets/:id ─────────────────────────────────────────────────────────

@router.get("/{ticket_id}", response_model=Ticket)
def get_ticket(ticket_id: str) -> Ticket:
    ticket = database.store.get(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket '{ticket_id}' not found")
    return ticket


# ─── PUT /tickets/:id ─────────────────────────────────────────────────────────

@router.put("/{ticket_id}", response_model=Ticket)
def update_ticket(ticket_id: str, payload: TicketUpdate) -> Ticket:
    ticket = database.store.get(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket '{ticket_id}' not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(ticket, field, value)

    ticket.updated_at = datetime.utcnow()

    if ticket.status in (Status.resolved, Status.closed) and ticket.resolved_at is None:
        ticket.resolved_at = datetime.utcnow()

    database.store.update(ticket)
    logger.info("updated ticket id=%s", ticket_id)
    return ticket


# ─── DELETE /tickets/:id ──────────────────────────────────────────────────────

@router.delete("/{ticket_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
def delete_ticket(ticket_id: str) -> None:
    deleted = database.store.delete(ticket_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Ticket '{ticket_id}' not found")
    logger.info("deleted ticket id=%s", ticket_id)


# ─── POST /tickets/:id/auto-classify ─────────────────────────────────────────

@router.post("/{ticket_id}/auto-classify")
def auto_classify(ticket_id: str, payload: AutoClassifyRequest = AutoClassifyRequest()) -> dict:
    ticket = database.store.get(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket '{ticket_id}' not found")

    result = classify(ticket, override=payload.override)

    if payload.override or ticket.classification is None:
        ticket.classification = result
        ticket.category = result.category
        ticket.priority = result.priority
        ticket.updated_at = datetime.utcnow()
        if result.manual_override:
            ticket.classification.manual_override = True
        database.store.update(ticket)

    logger.info(
        "auto-classified ticket=%s override=%s category=%s priority=%s",
        ticket_id,
        payload.override,
        result.category.value,
        result.priority.value,
    )
    return {
        "ticket_id": ticket_id,
        "category": result.category,
        "priority": result.priority,
        "confidence": result.confidence,
        "reasoning": result.reasoning,
        "keywords_found": result.keywords_found,
        "classified_at": result.classified_at,
    }
