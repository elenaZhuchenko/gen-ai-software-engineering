"""Fraud Detector Agent — Agent 2.

Scores validated transactions for risk based on transaction amount,
geography, and timing. Transactions scoring >= 60 are flagged for
fraud review; others are approved.

PII policy: account numbers are never written to logs.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from decimal import Decimal

logger = logging.getLogger(__name__)

HIGH_VALUE_THRESHOLD = Decimal("10000")
FRAUD_RISK_THRESHOLD = 60

# Risk contribution scores
SCORE_HIGH_VALUE = 60
SCORE_CROSS_BORDER = 20
SCORE_OFF_HOURS = 20

# Off-hours: 00:00 – 05:59 UTC (inclusive)
OFF_HOURS_START = 0
OFF_HOURS_END = 6  # exclusive


def _make_message(source: str, target: str, msg_type: str, data: dict) -> dict:
    return {
        "message_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source_agent": source,
        "target_agent": target,
        "message_type": msg_type,
        "data": data,
    }


def compute_risk_score(data: dict) -> tuple[int, list[str]]:
    """Compute a risk score (0–100) and list of triggered reasons.

    Parameters
    ----------
    data:
        Transaction data dict from a validated message.

    Returns
    -------
    tuple[int, list[str]]
        ``(risk_score, reasons)`` where *reasons* explains each
        contributing factor.
    """
    score = 0
    reasons: list[str] = []

    amount = Decimal(str(data.get("amount", "0")))
    if amount > HIGH_VALUE_THRESHOLD:
        score += SCORE_HIGH_VALUE
        reasons.append(f"HIGH_VALUE:{amount}")

    metadata = data.get("metadata", {})
    country = metadata.get("country", "US")
    if country != "US":
        score += SCORE_CROSS_BORDER
        reasons.append(f"CROSS_BORDER:{country}")

    txn_ts = data.get("timestamp", "")
    try:
        dt = datetime.fromisoformat(txn_ts.replace("Z", "+00:00"))
        if OFF_HOURS_START <= dt.hour < OFF_HOURS_END:
            score += SCORE_OFF_HOURS
            reasons.append(f"OFF_HOURS:{dt.hour:02d}:00 UTC")
    except (ValueError, AttributeError):
        pass

    return min(score, 100), reasons


def process_message(message: dict) -> dict:
    """Score a validated transaction for fraud risk.

    Parameters
    ----------
    message:
        Pipeline message from ``transaction_validator`` with
        ``data['status'] == 'validated'``.

    Returns
    -------
    dict
        New message directed at ``reporting_agent`` with
        ``data['status']`` set to ``'approved'`` or ``'fraud_review'``
        and ``data['risk_score']`` populated.
    """
    data = message.get("data", {})
    txn_id = data.get("transaction_id", "<unknown>")

    if data.get("status") != "validated":
        # Pass-through rejected messages without re-processing
        return _make_message(
            source="fraud_detector",
            target="reporting_agent",
            msg_type="transaction",
            data=data,
        )

    risk_score, risk_reasons = compute_risk_score(data)

    if risk_score >= FRAUD_RISK_THRESHOLD:
        status = "fraud_review"
    else:
        status = "approved"

    logger.info(
        "[fraud_detector] txn=%s outcome=%s risk_score=%d reasons=%s",
        txn_id,
        status,
        risk_score,
        risk_reasons,
    )

    return _make_message(
        source="fraud_detector",
        target="reporting_agent",
        msg_type="transaction",
        data={
            **data,
            "status": status,
            "risk_score": risk_score,
            "risk_reasons": risk_reasons,
        },
    )
