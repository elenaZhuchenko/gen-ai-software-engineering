"""Seed five sample bug pages in a Notion workspace for Homework 5 Task 3.

No external dependencies — uses only Python standard library.

Usage
-----
Export your Notion Internal Integration Token and a parent page ID, then run:

    export NOTION_TOKEN="ntn_your_token_here"
    export NOTION_PARENT_PAGE_ID="your_parent_page_id_here"
    python3 create_notion_bugs.py

How to find the parent page ID
--------------------------------
Open the target Notion page in your browser.
The 32-character hex string at the end of the URL is the page ID
(e.g. https://notion.so/My-Project-abc123def456... → abc123def456...).

The integration must have been shared with that parent page
(open the page → "..." menu → "Add connections" → select your integration).
"""

import json
import os
import sys
import urllib.request
from datetime import date, timedelta

NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
PARENT_PAGE_ID = os.environ.get("NOTION_PARENT_PAGE_ID")

if not NOTION_TOKEN:
    sys.exit("NOTION_TOKEN env var is not set.")
if not PARENT_PAGE_ID:
    sys.exit("NOTION_PARENT_PAGE_ID env var is not set.")

# Normalise: accept both 32-char hex and UUID-with-dashes.
_raw = PARENT_PAGE_ID.replace("-", "")
if len(_raw) == 32:
    PARENT_PAGE_ID = f"{_raw[0:8]}-{_raw[8:12]}-{_raw[12:16]}-{_raw[16:20]}-{_raw[20:32]}"

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}

BUGS = [
    {"title": "Bug: Login form crashes on empty password", "severity": "High", "status": "Open"},
    {"title": "Bug: Pagination skips last record on page 2", "severity": "Medium", "status": "In Progress"},
    {"title": "Bug: Dark mode colours not applied to modal dialogs", "severity": "Low", "status": "Open"},
    {"title": "Bug: Export to CSV truncates fields longer than 255 chars", "severity": "Medium", "status": "Open"},
    {"title": "Bug: Password reset email not sent when address contains plus sign", "severity": "High", "status": "Open"},
]


def create_page(bug: dict, index: int) -> dict:
    created_date = (date.today() - timedelta(days=index * 2)).isoformat()
    payload = {
        "parent": {"database_id": PARENT_PAGE_ID},
        "properties": {
            "title": {"title": [{"text": {"content": bug["title"]}}]}
        },
        "children": [
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"type": "text", "text": {"content": "Bug Details"}}]},
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"type": "text", "text": {"content": f"Severity: {bug['severity']}"}}]
                },
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"type": "text", "text": {"content": f"Status: {bug['status']}"}}]
                },
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"type": "text", "text": {"content": f"Reported: {created_date}"}}]
                },
            },
        ],
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        "https://api.notion.com/v1/pages",
        data=data,
        headers=HEADERS,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(f"\nNotion API error {exc.code}: {body}", file=sys.stderr)
        raise


def main() -> None:
    print(f"Creating {len(BUGS)} bug pages under parent {PARENT_PAGE_ID[:8]}...\n")
    for i, bug in enumerate(BUGS, start=1):
        result = create_page(bug, index=i)
        page_id = result.get("id", "unknown")
        print(f"  [{i}] Created: {bug['title']}")
        print(f"       Page ID: {page_id}\n")
    print("Done. Open Notion to verify the pages were created.")


if __name__ == "__main__":
    main()
