"""CSV, JSON and XML import helpers.

Each importer returns a list of raw dicts that are then validated by the
ticket router.  Parsing errors raise ValueError with a human-readable message.
"""
from __future__ import annotations

import csv
import io
import json
from typing import Any

from lxml import etree


# ─── CSV ──────────────────────────────────────────────────────────────────────

def parse_csv(content: str) -> list[dict[str, Any]]:
    """Parse CSV text into a list of raw ticket dicts."""
    reader = csv.DictReader(io.StringIO(content))
    rows = list(reader)
    if not rows:
        raise ValueError("CSV file is empty or has no data rows")
    return [_normalise(row) for row in rows]


# ─── JSON ─────────────────────────────────────────────────────────────────────

def parse_json(content: str) -> list[dict[str, Any]]:
    """Parse JSON text (array or single object) into raw ticket dicts."""
    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON: {exc}") from exc

    if isinstance(data, dict):
        data = [data]

    if not isinstance(data, list):
        raise ValueError("JSON must be an array of ticket objects or a single object")

    if not data:
        raise ValueError("JSON array is empty")

    return [_normalise(item) for item in data]


# ─── XML ──────────────────────────────────────────────────────────────────────

def parse_xml(content: str) -> list[dict[str, Any]]:
    """Parse XML text into raw ticket dicts.

    Expected structure::

        <tickets>
          <ticket>
            <subject>…</subject>
            <description>…</description>
            …
          </ticket>
        </tickets>

    The root element can be named anything; we look for ``<ticket>`` children.
    """
    try:
        root = etree.fromstring(content.encode())
    except etree.XMLSyntaxError as exc:
        raise ValueError(f"Invalid XML: {exc}") from exc

    ticket_elements = root.findall(".//ticket")
    if not ticket_elements:
        raise ValueError("XML contains no <ticket> elements")

    return [_xml_element_to_dict(el) for el in ticket_elements]


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _xml_element_to_dict(element: etree._Element) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for child in element:
        tag = child.tag
        if len(child):
            result[tag] = _xml_element_to_dict(child)
        else:
            result[tag] = child.text or ""
    return _normalise(result)


def _normalise(row: dict[str, Any]) -> dict[str, Any]:
    """Strip whitespace from string values; handle nested 'metadata' key."""
    out: dict[str, Any] = {}
    for k, v in row.items():
        key = k.strip() if isinstance(k, str) else k
        if isinstance(v, str):
            v = v.strip()
        if key == "tags" and isinstance(v, str):
            v = [t.strip() for t in v.split(",") if t.strip()]
        if key == "metadata" and isinstance(v, str):
            try:
                v = json.loads(v)
            except json.JSONDecodeError:
                pass
        out[key] = v
    return out
