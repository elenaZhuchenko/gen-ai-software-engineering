"""Integrator / Orchestrator — routes transactions through the pipeline.

Flow (file-based hand-off, per the message protocol in ``agents.md``):
  sample-transactions.json
    → shared/input/<txn_id>.json        (integrator drops the initial message)
    → shared/processing/<txn_id>.json   (agent moves the message here while working)
    → shared/output/<txn_id>.json       (agent writes its result here for the next agent)
    → TransactionValidator  → FraudDetector (validated only) → ReportingAgent
    → shared/results/<txn_id>.json + shared/results/pipeline-summary.json

Each stage physically reads and writes JSON message files under ``shared/``;
no message is ever passed between agents as an in-memory object only — the
file is the source of truth at every hand-off, which is what makes re-runs
and crash recovery possible (a message sitting in ``processing/`` shows
exactly which agent was working on it when the pipeline stopped).

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
    """Ensure shared/ subdirectories exist and clear the transient mailboxes.

    ``input/``, ``processing/``, and ``output/`` only ever hold messages
    that are in-flight between agents, so they are safe to clear before
    every run. ``results/`` holds the durable, final outcome of previous
    runs and is intentionally left untouched.
    """
    for sub in ("input", "processing", "output", "results"):
        (shared_dir / sub).mkdir(parents=True, exist_ok=True)
    for sub in ("input", "processing", "output"):
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


def _write_message(path: Path, message: dict) -> None:
    path.write_text(json.dumps(message, indent=2, default=str), encoding="utf-8")


def _read_message(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _run_stage(message_path: Path, processing_dir: Path, output_dir: Path, handler) -> dict:
    """Hand a message file from a mailbox to one agent and file its result.

    Implements the ``input/output`` → ``processing`` → ``output`` hand-off:
    the message file is moved into ``processing/`` for the duration of the
    call (marking which agent currently owns it), the agent's pure
    ``process_message`` handler is invoked on its contents, the resulting
    message is written to ``output/<txn_id>.json`` for the next stage to
    pick up, and the transient ``processing/`` copy is removed.

    Parameters
    ----------
    message_path:
        Path to the JSON message file to hand off (currently sitting in
        ``input/`` or ``output/``).
    processing_dir:
        Directory the message is moved into while the agent is "working".
    output_dir:
        Directory the agent's result message is written to.
    handler:
        Agent's ``process_message(message: dict) -> dict`` function.

    Returns
    -------
    dict
        The result message returned by ``handler``.
    """
    txn_id = message_path.stem
    processing_path = processing_dir / message_path.name
    shutil.move(str(message_path), str(processing_path))

    message = _read_message(processing_path)
    result_message = handler(message)

    output_path = output_dir / f"{txn_id}.json"
    _write_message(output_path, result_message)
    processing_path.unlink()

    return result_message


def _finalize_stage(message_path: Path, processing_dir: Path, results_dir: Path) -> dict:
    """Hand the final message off to the reporting agent and clear its mailbox copy.

    Mirrors :func:`_run_stage` for the last hop in the pipeline: the
    reporting agent writes directly to ``results/`` (its output *is* the
    durable result, not another in-flight message), so there is no
    ``output/`` write here.
    """
    processing_path = processing_dir / message_path.name
    shutil.move(str(message_path), str(processing_path))

    message = _read_message(processing_path)
    ack = report(message, results_dir=str(results_dir))
    processing_path.unlink()

    return ack


def run_pipeline(transactions: list[dict], shared_dir: str | Path = DEFAULT_SHARED) -> list[dict]:
    """Run all transactions through the three-agent, file-based pipeline.

    Each transaction's message is physically written to ``shared/input/``,
    then handed off through ``shared/processing/`` and ``shared/output/``
    to each agent in turn, exactly as described in the file-based message
    protocol (see ``agents.md``). No message is only ever an in-memory
    object — every hand-off is backed by a JSON file on disk.

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
    input_dir = shared / "input"
    processing_dir = shared / "processing"
    output_dir = shared / "output"
    results_dir = shared / "results"
    for d in (input_dir, processing_dir, output_dir, results_dir):
        d.mkdir(parents=True, exist_ok=True)
    final_results: list[dict] = []

    for txn in transactions:
        txn_id = txn.get("transaction_id", "<unknown>")
        logger.info("[integrator] processing txn=%s", txn_id)

        # Stage 0: drop the initial message into shared/input/
        input_msg = _make_input_message(txn)
        input_path = input_dir / f"{txn_id}.json"
        _write_message(input_path, input_msg)

        # Stage 1: TransactionValidator — input/ -> processing/ -> output/
        validated_msg = _run_stage(input_path, processing_dir, output_dir, validate)

        # Stage 2: FraudDetector — output/ -> processing/ -> output/ (validated only)
        if validated_msg["data"].get("status") == "validated":
            output_path = output_dir / f"{txn_id}.json"
            fraud_msg = _run_stage(output_path, processing_dir, output_dir, fraud_detect)
        else:
            fraud_msg = validated_msg

        # Stage 3: ReportingAgent — output/ -> processing/ -> results/
        output_path = output_dir / f"{txn_id}.json"
        _finalize_stage(output_path, processing_dir, results_dir)

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
