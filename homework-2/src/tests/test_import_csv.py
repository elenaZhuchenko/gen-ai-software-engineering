"""CSV import tests — 6 tests covering valid data, headers, edge cases, and error handling."""
from http import HTTPStatus

import pytest

from services.importers import parse_csv


_HEADER = "customer_id,customer_email,customer_name,subject,description"
_VALID_ROW = "1,user@example.com,User,Hello,Valid description xxxxxxxxx"


# ─── Unit tests for parse_csv ──────────────────────────────────────────────


def test_parse_csv_valid_single_row_returns_list():
    content = f"{_HEADER}\n{_VALID_ROW}"
    result = parse_csv(content)
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["customer_email"] == "user@example.com"


def test_parse_csv_multiple_rows():
    rows = "\n".join([
        "2,a@b.com,Alice,Sub A,Long enough description here",
        "3,b@c.com,Bob,Sub B,Long enough description here",
    ])
    result = parse_csv(f"{_HEADER}\n{rows}")
    assert len(result) == 2


def test_parse_csv_tags_field_split_to_list():
    row = "4,t@test.com,T,Sub,Long enough description here,,,,,billing"
    header = f"{_HEADER},priority,status,category,assigned_to,tags"
    result = parse_csv(f"{header}\n{row}")
    assert "billing" in result[0]["tags"]


def test_parse_csv_whitespace_stripped_from_values():
    row = "  5  , spaced@example.com ,  User  ,  Sub  ,  Description long enough  "
    result = parse_csv(f"{_HEADER}\n{row}")
    assert result[0]["customer_id"] == "5"
    assert result[0]["customer_email"] == "spaced@example.com"


# ─── Error cases ───────────────────────────────────────────────────────────


def test_csv_empty_file_raises_via_api(client):
    resp = client.post("/tickets/import", files={"file": ("empty.csv", "", "text/csv")})
    assert resp.status_code == HTTPStatus.BAD_REQUEST
    assert "CSV file is empty" in resp.json().get("detail", "") or resp.text


def test_csv_valid_single_row_via_api(client):
    csv_body = f"{_HEADER}\n{_VALID_ROW}"
    resp = client.post("/tickets/import", files={"file": ("f.csv", csv_body, "text/csv")})
    assert resp.status_code == HTTPStatus.OK
    data = resp.json()
    assert data["total"] == 1 and data["successful"] == 1
