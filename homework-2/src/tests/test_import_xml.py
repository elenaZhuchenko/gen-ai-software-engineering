"""XML import tests — 5 tests covering valid data, edge cases, and error handling."""
from http import HTTPStatus

import pytest

from services.importers import parse_xml


# ─── Unit tests for parse_xml ──────────────────────────────────────────────


def test_parse_xml_single_ticket_returns_list():
    content = """<?xml version="1.0"?>
<tickets>
  <ticket>
    <customer_id>1</customer_id>
    <customer_email>a@b.com</customer_email>
    <customer_name>Alice</customer_name>
    <subject>Test subject</subject>
    <description>Long enough description here</description>
  </ticket>
</tickets>"""
    result = parse_xml(content)
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["customer_email"] == "a@b.com"


def test_parse_xml_multiple_tickets():
    content = """<?xml version="1.0"?>
<tickets>
  <ticket>
    <customer_id>1</customer_id><customer_email>a@b.com</customer_email>
    <customer_name>A</customer_name><subject>Sub1</subject><description>Desc one xxxx</description>
  </ticket>
  <ticket>
    <customer_id>2</customer_id><customer_email>b@c.com</customer_email>
    <customer_name>B</customer_name><subject>Sub2</subject><description>Desc two xxxx</description>
  </ticket>
</tickets>"""
    result = parse_xml(content)
    assert len(result) == 2


def test_parse_xml_no_ticket_elements_raises():
    content = "<data><item>no tickets here</item></data>"
    with pytest.raises(ValueError, match="no <ticket>"):
        parse_xml(content)


def test_parse_xml_invalid_syntax_raises():
    with pytest.raises(ValueError, match="Invalid XML"):
        parse_xml("<tickets><ticket>unclosed")


def test_parse_xml_tags_field_normalised():
    content = """<?xml version="1.0"?>
<tickets>
  <ticket>
    <customer_id>1</customer_id>
    <customer_email>a@b.com</customer_email>
    <customer_name>A</customer_name>
    <subject>Sub</subject>
    <description>Long enough description here</description>
    <tags>billing, urgent, api</tags>
  </ticket>
</tickets>"""
    result = parse_xml(content)
    assert isinstance(result[0]["tags"], list)
    assert "billing" in result[0]["tags"]


# ─── Integration test via HTTP endpoint ────────────────────────────────────


def test_xml_import_via_api_success(client):
    body = """<?xml version="1.0"?>
<tickets>
  <ticket>
    <customer_id>42</customer_id>
    <customer_email>xml@test.com</customer_email>
    <customer_name>XML User</customer_name>
    <subject>XML subject test</subject>
    <description>A valid description long enough</description>
  </ticket>
</tickets>"""
    resp = client.post(
        "/tickets/import",
        files={"file": ("tickets.xml", body, "application/xml")},
    )
    assert resp.status_code == HTTPStatus.OK
    data = resp.json()
    assert data["total"] == 1
    assert data["successful"] == 1
