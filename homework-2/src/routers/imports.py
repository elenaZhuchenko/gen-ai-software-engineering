"""Bulk import router: POST /tickets/import."""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, File, HTTPException, Query, UploadFile, status
from pydantic import ValidationError

import database
from models import ImportSummary, Ticket, TicketCreate
from services.classifier import classify
from services.importers import parse_csv, parse_json, parse_xml

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tickets", tags=["import"])

_PARSERS = {
    "text/csv": parse_csv,
    "application/json": parse_json,
    "text/xml": parse_xml,
    "application/xml": parse_xml,
}

_EXT_FALLBACK = {
    ".csv": parse_csv,
    ".json": parse_json,
    ".xml": parse_xml,
}


@router.post("/import", response_model=ImportSummary, status_code=status.HTTP_200_OK)
async def import_tickets(
    file: UploadFile = File(...),
    auto_classify: bool = Query(default=False),
) -> ImportSummary:
    content_bytes = await file.read()

    try:
        content = content_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"File encoding error: {exc}",
        ) from exc

    parser = _resolve_parser(file)
    if parser is None:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported file type '{file.content_type}'. "
                "Accepted formats: CSV, JSON, XML"
            ),
        )

    try:
        raw_rows = parser(content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    summary = ImportSummary(total=len(raw_rows), successful=0, failed=0)

    for index, row in enumerate(raw_rows):
        row_num = index + 1
        try:
            payload = _row_to_ticket_create(row)
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

            if auto_classify:
                result = classify(ticket)
                ticket.classification = result
                if ticket.category is None:
                    ticket.category = result.category
                if ticket.priority is None:
                    ticket.priority = result.priority

            database.store.create(ticket)
            summary.successful += 1
            summary.tickets.append(ticket)

        except (ValidationError, ValueError, KeyError, TypeError) as exc:
            summary.failed += 1
            summary.errors.append({"row": row_num, "error": _format_error(exc)})
            logger.warning("import row=%d error=%s", row_num, exc)

    logger.info(
        "import complete file=%s total=%d ok=%d failed=%d",
        file.filename,
        summary.total,
        summary.successful,
        summary.failed,
    )
    return summary


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _resolve_parser(file: UploadFile):
    if file.content_type and file.content_type in _PARSERS:
        return _PARSERS[file.content_type]

    if file.filename:
        for ext, parser in _EXT_FALLBACK.items():
            if file.filename.lower().endswith(ext):
                return parser

    return None


def _row_to_ticket_create(row: dict[str, Any]) -> TicketCreate:
    metadata_raw = row.get("metadata", {})
    if not isinstance(metadata_raw, dict):
        metadata_raw = {}

    return TicketCreate(
        customer_id=row.get("customer_id", ""),
        customer_email=row.get("customer_email", ""),
        customer_name=row.get("customer_name", ""),
        subject=row.get("subject", ""),
        description=row.get("description", ""),
        category=row.get("category") or None,
        priority=row.get("priority") or None,
        status=row.get("status", "new"),
        assigned_to=row.get("assigned_to") or None,
        tags=row.get("tags", []),
        metadata=metadata_raw,
    )


def _format_error(exc: Exception) -> str:
    if isinstance(exc, ValidationError):
        errors = exc.errors()
        return "; ".join(
            f"{'.'.join(str(loc) for loc in e['loc'])}: {e['msg']}"
            for e in errors
        )
    return str(exc)
