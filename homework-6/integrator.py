"""Integrator / Orchestrator — routes transactions through the pipeline.

Flow: sample-transactions.json
  → TransactionValidator
  → FraudDetector (for validated transactions)
  → ReportingAgent (for all transactions)
  → shared/results/<txn_id>.json + shared/results/pipeline-summary.json

Usage:
    python integrator.py [--input PATH] [--shared-dir PATH]
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path

from agents.fraud_detector import process_message as fraud_detect
from agents.reporting_agent import process_message as report, write_summary
from agents.transaction_validator import process_message as validate

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent
DEFAULT_INPUT = BASE_DIR / "sample-transactions.json"
DEFAULT_SHARED = BASE_DIR / "shared"


def _setup_dirs(shared_dir: Path) -> None:
    """Ensure shared/ subdirectories exist and clear transient ones."""
    for sub in ("input", "processing", "output", "results"):
        (shared_dir / sub).mkdir(parents=True, exist_ok=True)
    for sub in ("processing", "output"):
        for f in (shared_dir / sub).iterdir():
            if f.name != ".gitkeep":
                f.unlink()


def _make_input_message(txn: dict) -> dict:
    return {
        "message_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source_agent": "integrator",
        "target_agent": "transaction_validator",
        "message_type": "transaction",
        "data": txn,
    }


def run_pipeline(transactions: list[dict], shared_dir: str | Path = DEFAULT_SHARED) -> list[dict]:
    """Run all transactions through the three-agent pipeline.

    Parameters
    ----------
    transactions:
        Raw transaction records loaded from ``sample-transactions.json``.
    shared_dir:
        Root of the ``shared/`` directory tree.

    Returns
    -------
    list[dict]
        Final result records (one per transaction) suitable for
        ``write_summary()``.
    """
    shared = Path(shared_dir)
    results_dir = str(shared / "results")
    final_results: list[dict] = []

    for txn in transactions:
        txn_id = txn.get("transaction_id", "<unknown>")
        logger.info("[integrator] processing txn=%s", txn_id)

        # Stage 1: validation
        input_msg = _make_input_message(txn)
        validated_msg = validate(input_msg)

        # Stage 2: fraud detection (only for validated records)
        if validated_msg["data"].get("status") == "validated":
            fraud_msg = fraud_detect(validated_msg)
        else:
            fraud_msg = validated_msg

        # Stage 3: report result
        ack = report(fraud_msg, results_dir=results_dir)
        final_results.append(
            {
                "transaction_id": txn_id,
                "status": fraud_msg["data"].get("status"),
            }
        )

    return final_results


def main() -> None:
    parser = argparse.ArgumentParser(description="Banking transaction pipeline integrator")
    parser.add_argument(
        "--input",
        default=str(DEFAULT_INPUT),
        help="Path to sample-transactions.json",
    )
    parser.add_argument(
        "--shared-dir",
        default=str(DEFAULT_SHARED),
        help="Root of the shared/ directory",
    )
    args = parser.parse_args()

    shared_dir = Path(args.shared_dir)
    _setup_dirs(shared_dir)

    with open(args.input, encoding="utf-8") as f:
        transactions = json.load(f)

    logger.info("[integrator] loaded %d transactions from %s", len(transactions), args.input)

    results = run_pipeline(transactions, shared_dir=shared_dir)

    write_summary(results, output_dir=str(shared_dir / "results"))

    approved = sum(1 for r in results if r["status"] == "approved")
    fraud = sum(1 for r in results if r["status"] == "fraud_review")
    rejected = sum(1 for r in results if r["status"] == "rejected")

    print(
        f"\n✓ Pipeline complete: {len(results)} transactions processed "
        f"| approved={approved} fraud_review={fraud} rejected={rejected}"
    )


if __name__ == "__main__":
    main()
