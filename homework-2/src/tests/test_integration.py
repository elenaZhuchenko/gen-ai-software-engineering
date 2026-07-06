import asyncio
from http import HTTPStatus

from httpx import ASGITransport, AsyncClient

from main import app


def make_payload(index: int = 1, **overrides):
    payload = {
        "customer_id": f"cust-{index}",
        "customer_email": f"user{index}@example.com",
        "customer_name": "Integration User",
        "subject": f"Integration subject {index}",
        "description": "Integration test description " + "x" * 20,
    }
    payload.update(overrides)
    return payload


def test_full_ticket_lifecycle(client):
    create = client.post("/tickets", json=make_payload(1))
    assert create.status_code == HTTPStatus.CREATED
    ticket_id = create.json()["id"]

    get_by_id = client.get(f"/tickets/{ticket_id}")
    assert get_by_id.status_code == HTTPStatus.OK
    assert get_by_id.json()["id"] == ticket_id

    update = client.put(f"/tickets/{ticket_id}", json={"status": "resolved"})
    assert update.status_code == HTTPStatus.OK
    assert update.json()["status"] == "resolved"

    delete = client.delete(f"/tickets/{ticket_id}")
    assert delete.status_code == HTTPStatus.NO_CONTENT
    assert client.get(f"/tickets/{ticket_id}").status_code == HTTPStatus.NOT_FOUND


def test_bulk_import_with_auto_classification_verification(client):
    csv_body = (
        "customer_id,customer_email,customer_name,subject,description\n"
        "1,user1@example.com,User One,Cannot login,Need urgent help cannot login\n"
        "2,user2@example.com,User Two,Invoice overcharge,Please check billing invoice issue\n"
    )
    response = client.post(
        "/tickets/import",
        files={"file": ("tickets.csv", csv_body, "text/csv")},
        params={"auto_classify": "true"},
    )
    assert response.status_code == HTTPStatus.OK
    summary = response.json()
    assert summary["total"] == 2
    assert summary["successful"] == 2
    assert summary["failed"] == 0

    for imported_ticket in summary["tickets"]:
        assert imported_ticket["category"] is not None
        assert imported_ticket["priority"] is not None
        assert imported_ticket["classification"] is not None


def test_concurrent_operations_20_plus_simultaneous_requests():
    async def _run():
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as async_client:
            tasks = [
                async_client.post("/tickets", json=make_payload(i))
                for i in range(1, 26)
            ]
            return await asyncio.gather(*tasks)

    responses = asyncio.run(_run())
    assert len(responses) == 25
    assert all(resp.status_code == HTTPStatus.CREATED for resp in responses)


def test_import_json_then_classify_and_list(client):
    """Import via JSON, auto-classify, then verify tickets appear in listing."""
    body = (
        '[{"customer_id":"j1","customer_email":"j1@test.com","customer_name":"JSON User",'
        '"subject":"Cannot login urgent","description":"Production down cannot login immediately"}]'
    )
    import_resp = client.post(
        "/tickets/import",
        files={"file": ("t.json", body, "application/json")},
        params={"auto_classify": "true"},
    )
    assert import_resp.status_code == HTTPStatus.OK
    assert import_resp.json()["successful"] == 1

    ticket_id = import_resp.json()["tickets"][0]["id"]
    classify_resp = client.post(f"/tickets/{ticket_id}/auto-classify")
    assert classify_resp.status_code == HTTPStatus.OK
    assert classify_resp.json()["priority"] in {"urgent", "high", "medium", "low"}

    list_resp = client.get("/tickets", params={"customer_id": "j1"})
    assert list_resp.status_code == HTTPStatus.OK
    assert list_resp.json()["total"] >= 1


def test_combined_filtering_by_category_and_priority(client):
    tickets = [
        make_payload(101, category="billing_question", priority="high"),
        make_payload(102, category="billing_question", priority="high"),
        make_payload(103, category="billing_question", priority="low"),
        make_payload(104, category="technical_issue", priority="high"),
    ]
    for ticket in tickets:
        response = client.post("/tickets", json=ticket)
        assert response.status_code == HTTPStatus.CREATED

    filtered = client.get(
        "/tickets",
        params={"category": "billing_question", "priority": "high"},
    )
    assert filtered.status_code == HTTPStatus.OK
    body = filtered.json()
    assert body["total"] == 2
    assert all(item["category"] == "billing_question" for item in body["tickets"])
    assert all(item["priority"] == "high" for item in body["tickets"])

