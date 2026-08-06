"""Reporting Agent — Agent 3.

Writes the final per-transaction result JSON to ``shared/results/`` and,
after all transactions are processed, aggregates them into
``pipeline-summary.json``.

PII policy: account numbers are never included in log lines; only masked
variants (last 4 chars) may appear if needed.
"""
from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from decimal import Decimal

logger = logging.getLogger(__name__)


def _make_message(source: str, target: str, msg_type: str, data: dict) -> dict:
    return {
        "message_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source_agent": source,
        "target_agent": target,
        "message_type": msg_type,
        "data": data,
    }


def _atomic_write(path: str, payload: dict) -> None:
    """Write JSON atomically (write to tmp then rename)."""
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, default=str)
    os.replace(tmp_path, path)


def process_message(message: dict, results_dir: str = "shared/results") -> dict:
    """Write the final result for one transaction to ``results_dir``.

    Parameters
    ----------
    message:
        Pipeline message from ``fraud_detector`` (or directly from
        ``transaction_validator`` for rejected records).
    results_dir:
        Directory where result JSON files are written.

    Returns
    -------
    dict
        Acknowledgement message with ``data['written_path']``.
    """
    data = message.get("data", {})
    txn_id = data.get("transaction_id", str(uuid.uuid4()))
    status = data.get("status", "unknown")

    result = {
        "transaction_id": txn_id,
        "status": status,
        "risk_score": data.get("risk_score", 0),
        "risk_reasons": data.get("risk_reasons", []),
        "reason": data.get("reason"),
        "message": data.get("message"),
        "currency": data.get("currency"),
        "amount": str(data.get("amount", "0")),
        "transaction_type": data.get("transaction_type"),
        "processed_at": datetime.now(timezone.utc).isoformat(),
    }

    os.makedirs(results_dir, exist_ok=True)
    out_path = os.path.join(results_dir, f"{txn_id}.json")
    _atomic_write(out_path, result)

    logger.info("[reporting_agent] txn=%s outcome=%s written=%s", txn_id, status, out_path)

    return _make_message(
        source="reporting_agent",
        target="integrator",
        msg_type="ack",
        data={"transaction_id": txn_id, "status": status, "written_path": out_path},
    )


def write_summary(results: list[dict], output_dir: str = "shared/results") -> None:
    """Aggregate all transaction results into ``pipeline-summary.json``.

    Parameters
    ----------
    results:
        List of result dicts, each with at least a ``status`` field.
    output_dir:
        Directory where ``pipeline-summary.json`` is written.
    """
    total = len(results)
    rejected = sum(1 for r in results if r.get("status") == "rejected")
    fraud_review = sum(1 for r in results if r.get("status") == "fraud_review")
    approved = sum(1 for r in results if r.get("status") == "approved")
    validated = total - rejected  # includes approved + fraud_review

    summary = {
        "run_timestamp": datetime.now(timezone.utc).isoformat(),
        "total": total,
        "validated": validated,
        "rejected": rejected,
        "approved": approved,
        "fraud_review": fraud_review,
    }

    os.makedirs(output_dir, exist_ok=True)
    summary_path = os.path.join(output_dir, "pipeline-summary.json")
    _atomic_write(summary_path, summary)
    logger.info(
        "[reporting_agent] summary written=%s total=%d rejected=%d fraud_review=%d approved=%d",
        summary_path,
        total,
        rejected,
        fraud_review,
        approved,
    )
