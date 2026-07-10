import pytest
from pydantic import ValidationError

from models import TicketCreate, Ticket


def sample_payload():
    return {
        "customer_id": "cust-1",
        "customer_email": "user@example.com",
        "customer_name": "User",
        "subject": "Help",
        "description": "A" * 20,
    }


def test_valid_ticket_creation():
    payload = sample_payload()
    tc = TicketCreate(**payload)
    t = Ticket(**tc.model_dump())
    assert t.customer_email == payload["customer_email"]


def test_subject_too_short():
    payload = sample_payload()
    payload["subject"] = ""
    with pytest.raises(ValidationError):
        TicketCreate(**payload)


def test_subject_too_long():
    payload = sample_payload()
    payload["subject"] = "x" * 201
    with pytest.raises(ValidationError):
        TicketCreate(**payload)


def test_description_too_short():
    payload = sample_payload()
    payload["description"] = "123456789"
    with pytest.raises(ValidationError):
        TicketCreate(**payload)


def test_description_too_long():
    payload = sample_payload()
    payload["description"] = "x" * 2001
    with pytest.raises(ValidationError):
        TicketCreate(**payload)


def test_invalid_category_enum():
    payload = sample_payload()
    payload["category"] = "unknown"
    with pytest.raises(ValidationError):
        TicketCreate(**payload)


def test_invalid_priority_enum():
    payload = sample_payload()
    payload["priority"] = "critical"
    with pytest.raises(ValidationError):
        TicketCreate(**payload)


def test_invalid_status_enum():
    payload = sample_payload()
    payload["status"] = "pending"
    with pytest.raises(ValidationError):
        TicketCreate(**payload)


def test_metadata_defaults():
    payload = sample_payload()
    tc = TicketCreate(**payload)
    assert tc.metadata.source.value == "api"

