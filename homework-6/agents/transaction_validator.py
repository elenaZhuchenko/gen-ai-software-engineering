"""Transaction Validator Agent — Agent 1.

Validates raw transaction records for required fields, positive decimal
amounts, and ISO 4217 currency codes. Rejects malformed records with a
structured reason code before any further processing.

PII policy: account numbers are never written to logs.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

logger = logging.getLogger(__name__)

# ISO 4217 alpha-3 currency allow-list (representative subset used in tests)
ISO_4217_CURRENCIES: frozenset[str] = frozenset(
    {
        "USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD", "NZD",
        "SEK", "NOK", "DKK", "HKD", "SGD", "CNY", "INR", "BRL",
        "MXN", "ZAR", "RUB", "KRW", "TRY", "PLN", "CZK", "HUF",
    }
)

REQUIRED_FIELDS: tuple[str, ...] = (
    "transaction_id",
    "timestamp",
    "source_account",
    "destination_account",
    "amount",
    "currency",
    "transaction_type",
)


def _make_message(
    source: str,
    target: str,
    msg_type: str,
    data: dict,
) -> dict:
    return {
        "message_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source_agent": source,
        "target_agent": target,
        "message_type": msg_type,
        "data": data,
    }


def process_message(message: dict) -> dict:
    """Validate a raw transaction message and return a new message.

    Parameters
    ----------
    message:
        Standard pipeline message whose ``data`` field contains a raw
        transaction record from ``sample-transactions.json``.

    Returns
    -------
    dict
        New message directed at ``fraud_detector`` with
        ``data['status']`` set to ``'validated'`` or ``'rejected'``.
    """
    raw = message.get("data", {})
    txn_id = raw.get("transaction_id", "<unknown>")

    # --- required field check ---
    missing = [f for f in REQUIRED_FIELDS if f not in raw or raw[f] is None]
    if missing:
        reason = f"MISSING_FIELD:{','.join(missing)}"
        logger.warning("[transaction_validator] txn=%s outcome=rejected reason=%s", txn_id, reason)
        return _make_message(
            source="transaction_validator",
            target="reporting_agent",
            msg_type="transaction",
            data={
                **raw,
                "status": "rejected",
                "reason": reason,
                "message": f"Missing required fields: {', '.join(missing)}",
            },
        )

    # --- amount validation ---
    try:
        amount = Decimal(str(raw["amount"]))
    except (InvalidOperation, ValueError):
        reason = "INVALID_AMOUNT"
        logger.warning("[transaction_validator] txn=%s outcome=rejected reason=%s", txn_id, reason)
        return _make_message(
            source="transaction_validator",
            target="reporting_agent",
            msg_type="transaction",
            data={
                **raw,
                "status": "rejected",
                "reason": reason,
                "message": "Amount must be a valid decimal number.",
            },
        )

    if amount <= Decimal("0"):
        reason = "INVALID_AMOUNT"
        logger.warning("[transaction_validator] txn=%s outcome=rejected reason=%s", txn_id, reason)
        return _make_message(
            source="transaction_validator",
            target="reporting_agent",
            msg_type="transaction",
            data={
                **raw,
                "amount": str(amount),
                "status": "rejected",
                "reason": reason,
                "message": "Amount must be greater than zero.",
            },
        )

    # --- currency validation ---
    currency = str(raw["currency"]).upper()
    if currency not in ISO_4217_CURRENCIES:
        reason = "INVALID_CURRENCY"
        logger.warning("[transaction_validator] txn=%s outcome=rejected reason=%s", txn_id, reason)
        return _make_message(
            source="transaction_validator",
            target="reporting_agent",
            msg_type="transaction",
            data={
                **raw,
                "amount": str(amount),
                "currency": currency,
                "status": "rejected",
                "reason": reason,
                "message": f"Currency '{currency}' is not a valid ISO 4217 code.",
            },
        )

    logger.info("[transaction_validator] txn=%s outcome=validated", txn_id)
    return _make_message(
        source="transaction_validator",
        target="fraud_detector",
        msg_type="transaction",
        data={
            **raw,
            "amount": str(amount),
            "currency": currency,
            "status": "validated",
        },
    )
