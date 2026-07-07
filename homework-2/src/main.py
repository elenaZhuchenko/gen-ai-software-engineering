"""FastAPI application entry point."""
from __future__ import annotations

import json
import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import database
from models import Ticket, TicketCreate
from routers.imports import router as import_router
from routers.tickets import router as tickets_router
from services.classifier import classify

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Support Ticket System",
    description="Multi-format ticket import with auto-classification",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import router must be registered BEFORE the tickets router so that the more
# specific /tickets/import path wins over /tickets/{ticket_id}.
app.include_router(import_router)
app.include_router(tickets_router)


def _seed_from_file() -> None:
    seed_path = Path(__file__).parent.parent / "demo" / "seed_data.json"
    if not seed_path.exists():
        logger.warning("seed_data.json not found at %s", seed_path)
        return
    try:
        records = json.loads(seed_path.read_text())
        count = 0
        for raw in records:
            payload = TicketCreate(**raw)
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
                tags=payload.tags or [],
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
            count += 1
        logger.info("Seeded %d tickets from %s", count, seed_path)
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to seed tickets: %s", exc)


@app.on_event("startup")
def on_startup() -> None:
    _seed_from_file()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
