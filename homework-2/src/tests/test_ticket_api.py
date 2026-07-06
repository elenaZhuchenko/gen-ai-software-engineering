import uuid
from http import HTTPStatus


def make_payload(i=1):
    return {
        "customer_id": f"cust-{i}",
        "customer_email": f"user{i}@example.com",
        "customer_name": "User",
        "subject": f"Subject {i}",
        "description": "Valid description " + "x" * 20,
    }


def test_create_ticket_success(client):
    resp = client.post("/tickets", json=make_payload())
    assert resp.status_code == HTTPStatus.CREATED
    body = resp.json()
    assert "id" in body


def test_create_ticket_missing_required_field(client):
    p = make_payload()
    del p["customer_email"]
    resp = client.post("/tickets", json=p)
    assert resp.status_code == 422


def test_create_ticket_invalid_email(client):
    p = make_payload()
    p["customer_email"] = "not-an-email"
    resp = client.post("/tickets", json=p)
    assert resp.status_code == 422


def test_create_ticket_auto_classify_flag(client):
    # create payload requesting auto_classify; classifier returns predictable result
    p = make_payload()
    p["auto_classify"] = True

    resp = client.post("/tickets", json=p)
    assert resp.status_code == HTTPStatus.CREATED
    body = resp.json()
    assert body.get("category") is not None or body.get("classification") is not None


def test_get_ticket_by_id_found(client):
    p = make_payload()
    create = client.post("/tickets", json=p).json()
    tid = create["id"]
    resp = client.get(f"/tickets/{tid}")
    assert resp.status_code == HTTPStatus.OK
    assert resp.json()["id"] == tid


def test_get_ticket_by_id_not_found(client):
    resp = client.get(f"/tickets/{uuid.uuid4()}")
    assert resp.status_code == HTTPStatus.NOT_FOUND


def test_list_tickets_no_filters(client):
    # create 3 tickets
    for i in range(3):
        client.post("/tickets", json=make_payload(i))
    resp = client.get("/tickets")
    assert resp.status_code == HTTPStatus.OK
    data = resp.json()
    assert data["total"] == 3


def test_list_tickets_filter_by_category(client):
    # create 5 tickets where 2 have billing_question
    for i in range(3):
        client.post("/tickets", json=make_payload(i))
    p = make_payload(99)
    p["category"] = "billing_question"
    client.post("/tickets", json=p)
    q = make_payload(100)
    q["category"] = "billing_question"
    client.post("/tickets", json=q)

    resp = client.get("/tickets", params={"category": "billing_question"})
    assert resp.status_code == HTTPStatus.OK
    assert resp.json()["total"] == 2


def test_update_ticket_success(client):
    p = make_payload()
    tid = client.post("/tickets", json=p).json()["id"]
    resp = client.put(f"/tickets/{tid}", json={"status": "in_progress"})
    assert resp.status_code == HTTPStatus.OK
    assert resp.json()["status"] == "in_progress"


def test_update_ticket_not_found(client):
    resp = client.put(f"/tickets/{uuid.uuid4()}", json={"status": "in_progress"})
    assert resp.status_code == HTTPStatus.NOT_FOUND


def test_delete_ticket(client):
    p = make_payload()
    tid = client.post("/tickets", json=p).json()["id"]
    resp = client.delete(f"/tickets/{tid}")
    assert resp.status_code == HTTPStatus.NO_CONTENT
    # subsequent get returns 404
    assert client.get(f"/tickets/{tid}").status_code == HTTPStatus.NOT_FOUND

