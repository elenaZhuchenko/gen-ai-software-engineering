"""Shared pytest fixtures for the banking pipeline tests."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest


def make_raw_transaction(
    transaction_id: str = "TXN-TEST",
    amount: str = "1500.00",
    currency: str = "USD",
    source_account: str = "ACC-0001",
    destination_account: str = "ACC-0002",
    transaction_type: str = "transfer",
    timestamp: str = "2026-03-16T10:00:00Z",
    country: str = "US",
    description: str = "Test payment",
) -> dict:
    return {
        "transaction_id": transaction_id,
        "timestamp": timestamp,
        "source_account": source_account,
        "destination_account": destination_account,
        "amount": amount,
        "currency": currency,
        "transaction_type": transaction_type,
        "description": description,
        "metadata": {"channel": "online", "country": country},
    }


def make_input_message(txn: dict, target: str = "transaction_validator") -> dict:
    return {
        "message_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source_agent": "integrator",
        "target_agent": target,
        "message_type": "transaction",
        "data": txn,
    }


@pytest.fixture
def standard_txn():
    return make_raw_transaction()


@pytest.fixture
def standard_msg(standard_txn):
    return make_input_message(standard_txn)


@pytest.fixture
def high_value_txn():
    return make_raw_transaction(transaction_id="TXN-HIGH", amount="25000.00")


@pytest.fixture
def cross_border_txn():
    return make_raw_transaction(
        transaction_id="TXN-CB", amount="500.00", currency="EUR", country="DE"
    )


@pytest.fixture
def off_hours_txn():
    return make_raw_transaction(
        transaction_id="TXN-OFF",
        amount="200.00",
        timestamp="2026-03-16T02:00:00Z",
    )
