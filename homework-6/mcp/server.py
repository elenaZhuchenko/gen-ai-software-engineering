"""FastMCP server — pipeline-status.

Exposes:
- Tool ``get_transaction_status``: returns the processing result for a
  given ``transaction_id`` from ``shared/results/``.
- Tool ``list_pipeline_results``: returns a summary of all processed
  transactions from ``shared/results/``.
- Resource ``pipeline://summary``: returns the latest pipeline run
  summary as a JSON string.

Usage (stdio transport, default):
    python mcp/server.py

Or via Cursor MCP configuration in .cursor/mcp.json.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from fastmcp import FastMCP

# Resolve paths relative to the homework-6 project root
_HERE = Path(__file__).parent
_PROJECT_ROOT = _HERE.parent
_RESULTS_DIR = _PROJECT_ROOT / "shared" / "results"

mcp = FastMCP("pipeline-status")


def _load_result(transaction_id: str) -> dict | None:
    """Load a single transaction result JSON, or return None if missing."""
    path = _RESULTS_DIR / f"{transaction_id}.json"
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _load_summary() -> dict | None:
    """Load pipeline-summary.json, or return None if not yet generated."""
    path = _RESULTS_DIR / "pipeline-summary.json"
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _load_all_results() -> list[dict]:
    """Load all per-transaction result files from shared/results/."""
    results = []
    if not _RESULTS_DIR.exists():
        return results
    for path in sorted(_RESULTS_DIR.glob("TXN*.json")):
        with open(path, encoding="utf-8") as f:
            results.append(json.load(f))
    return results


@mcp.tool()
def get_transaction_status(transaction_id: str) -> dict:
    """Return the processing result for a specific transaction.

    Parameters
    ----------
    transaction_id:
        The ID of the transaction to look up, e.g. ``"TXN001"``.

    Returns
    -------
    dict
        Full result record including ``status``, ``risk_score``,
        ``risk_reasons``, and any rejection ``reason``. Returns an
        error dict if the transaction was not found.
    """
    result = _load_result(transaction_id)
    if result is None:
        return {
            "error": "NOT_FOUND",
            "message": f"No result found for transaction_id '{transaction_id}'. "
                       "Run the pipeline first (python integrator.py).",
            "transaction_id": transaction_id,
        }
    return result


@mcp.tool()
def list_pipeline_results() -> dict:
    """Return a summary of all processed transactions.

    Returns
    -------
    dict
        Dictionary with ``summary`` (from pipeline-summary.json) and
        ``transactions`` (list of all per-transaction result records).
        If the pipeline has not been run yet, returns an appropriate
        message.
    """
    summary = _load_summary()
    transactions = _load_all_results()

    if not transactions:
        return {
            "error": "NO_RESULTS",
            "message": "No results found. Run the pipeline first (python integrator.py).",
            "summary": None,
            "transactions": [],
        }

    return {
        "summary": summary,
        "transactions": transactions,
    }


@mcp.resource("pipeline://summary")
def pipeline_summary() -> str:
    """Return the latest pipeline run summary as a JSON string.

    This resource reflects the current state of
    ``shared/results/pipeline-summary.json``.
    """
    summary = _load_summary()
    if summary is None:
        return json.dumps(
            {
                "error": "NO_SUMMARY",
                "message": "pipeline-summary.json not found. Run the pipeline first.",
            },
            indent=2,
        )
    return json.dumps(summary, indent=2)


if __name__ == "__main__":
    mcp.run()
