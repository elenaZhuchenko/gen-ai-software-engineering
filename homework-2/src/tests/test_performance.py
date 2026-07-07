import asyncio
import time
from http import HTTPStatus

from httpx import ASGITransport, AsyncClient

import database
from main import app
from models import Ticket
from services.classifier import classify


def _payload(index: int):
    return {
        "customer_id": f"perf-{index}",
        "customer_email": f"perf{index}@example.com",
        "customer_name": "Perf User",
        "subject": f"Performance subject {index}",
        "description": "Performance test description " + "x" * 40,
    }


def test_create_100_tickets_under_1s(client):
    start = time.perf_counter()
    for i in range(100):
        response = client.post("/tickets", json=_payload(i))
        assert response.status_code == HTTPStatus.CREATED
    elapsed = time.perf_counter() - start
    assert elapsed < 1.0, f"100 sequential creates took {elapsed:.3f}s"


def test_list_1000_tickets_under_500ms(client):
    for i in range(1000):
        ticket = Ticket(**_payload(i))
        database.store.create(ticket)

    start = time.perf_counter()
    response = client.get("/tickets")
    elapsed = time.perf_counter() - start

    assert response.status_code == HTTPStatus.OK
    assert response.json()["total"] == 1000
    assert elapsed < 0.5, f"listing 1000 tickets took {elapsed:.3f}s"


def test_csv_import_50_rows_under_2s(client):
    rows = [
        "customer_id,customer_email,customer_name,subject,description",
    ]
    for i in range(50):
        rows.append(
            f"{i},user{i}@example.com,User {i},Subject {i},Description for import row {i} with enough text"
        )
    csv_body = "\n".join(rows)

    start = time.perf_counter()
    response = client.post(
        "/tickets/import",
        files={"file": ("sample.csv", csv_body, "text/csv")},
    )
    elapsed = time.perf_counter() - start

    assert response.status_code == HTTPStatus.OK
    body = response.json()
    assert body["total"] == 50
    assert body["successful"] == 50
    assert body["failed"] == 0
    assert elapsed < 2.0, f"importing 50 CSV rows took {elapsed:.3f}s"


def test_classify_1000_tickets_under_1s():
    tickets = [
        Ticket(
            customer_id=f"c-{i}",
            customer_email=f"classify{i}@example.com",
            customer_name="Classifier User",
            subject="Cannot login to account",
            description="Users are blocked and cannot access the dashboard",
        )
        for i in range(1000)
    ]

    start = time.perf_counter()
    results = [classify(ticket) for ticket in tickets]
    elapsed = time.perf_counter() - start

    assert len(results) == 1000
    assert all(result.category.value == "account_access" for result in results)
    assert elapsed < 1.0, f"classifying 1000 tickets took {elapsed:.3f}s"


def test_concurrent_20_creates():
    async def _run():
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as async_client:
            tasks = [async_client.post("/tickets", json=_payload(i)) for i in range(20)]
            return await asyncio.gather(*tasks)

    responses = asyncio.run(_run())
    assert len(responses) == 20
    assert all(response.status_code == HTTPStatus.CREATED for response in responses)

