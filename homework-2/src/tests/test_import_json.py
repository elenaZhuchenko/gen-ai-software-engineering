"""JSON import tests — 5 tests covering valid data, edge cases, and error handling."""
from http import HTTPStatus

import pytest

from services.importers import parse_json


# ─── Unit tests for parse_json ─────────────────────────────────────────────


def test_parse_json_array_returns_list():
    content = '[{"customer_id":"1","customer_email":"a@b.com","customer_name":"A","subject":"Sub","description":"Description long enough"}]'
    result = parse_json(content)
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["customer_email"] == "a@b.com"


def test_parse_json_single_object_wrapped_in_list():
    content = '{"customer_id":"2","customer_email":"b@c.com","customer_name":"B","subject":"Sub","description":"Description long enough"}'
    result = parse_json(content)
    assert isinstance(result, list)
    assert len(result) == 1


def test_parse_json_empty_array_raises():
    with pytest.raises(ValueError, match="empty"):
        parse_json("[]")


def test_parse_json_invalid_syntax_raises():
    with pytest.raises(ValueError, match="Invalid JSON"):
        parse_json("{not valid json}")


def test_parse_json_non_array_non_object_raises():
    with pytest.raises(ValueError):
        parse_json('"just a string"')


# ─── Integration tests via HTTP endpoint ───────────────────────────────────


def test_json_import_via_api_success(client):
    body = '[{"customer_id":"3","customer_email":"c@d.com","customer_name":"C","subject":"Sub","description":"Valid description text"}]'
    resp = client.post(
        "/tickets/import",
        files={"file": ("tickets.json", body, "application/json")},
    )
    assert resp.status_code == HTTPStatus.OK
    data = resp.json()
    assert data["total"] == 1
    assert data["successful"] == 1
    assert data["failed"] == 0
