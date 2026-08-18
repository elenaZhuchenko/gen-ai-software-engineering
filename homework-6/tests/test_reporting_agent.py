"""Unit tests for agents/reporting_agent.py."""
from __future__ import annotations

import json
import os

import pytest

from agents.reporting_agent import process_message, write_summary
from tests.conftest import make_raw_transaction


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_fraud_message(
    txn_id: str = "TXN-TEST",
    status: str = "approved",
    amount: str = "1500.00",
    currency: str = "USD",
    risk_score: int = 0,
    risk_reasons: list | None = None,
) -> dict:
    return {
        "message_id": "test-msg-id",
        "timestamp": "2026-03-16T10:00:00Z",
        "source_agent": "fraud_detector",
        "target_agent": "reporting_agent",
        "message_type": "transaction",
        "data": {
            "transaction_id": txn_id,
            "amount": amount,
            "currency": currency,
            "transaction_type": "transfer",
            "status": status,
            "risk_score": risk_score,
            "risk_reasons": risk_reasons or [],
        },
    }


def _make_rejected_message(txn_id: str = "TXN-REJ", reason: str = "INVALID_CURRENCY") -> dict:
    return {
        "message_id": "test-msg-id",
        "timestamp": "2026-03-16T10:00:00Z",
        "source_agent": "transaction_validator",
        "target_agent": "reporting_agent",
        "message_type": "transaction",
        "data": {
            "transaction_id": txn_id,
            "amount": "200.00",
            "currency": "XYZ",
            "transaction_type": "transfer",
            "status": "rejected",
            "reason": reason,
            "message": "Currency is not valid.",
        },
    }


# ---------------------------------------------------------------------------
# process_message tests
# ---------------------------------------------------------------------------

class TestProcessMessage:
    def test_writes_result_file(self, tmp_path):
        msg = _make_fraud_message("TXN001")
        result_dir = str(tmp_path / "results")
        process_message(msg, results_dir=result_dir)
        assert (tmp_path / "results" / "TXN001.json").exists()

    def test_result_file_contains_valid_json(self, tmp_path):
        msg = _make_fraud_message("TXN002", status="fraud_review", risk_score=60)
        result_dir = str(tmp_path / "results")
        process_message(msg, results_dir=result_dir)
        path = tmp_path / "results" / "TXN002.json"
        data = json.loads(path.read_text())
        assert data["status"] == "fraud_review"
        assert data["risk_score"] == 60

    def test_result_includes_transaction_id(self, tmp_path):
        msg = _make_fraud_message("TXN003")
        result_dir = str(tmp_path / "results")
        process_message(msg, results_dir=result_dir)
        data = json.loads((tmp_path / "results" / "TXN003.json").read_text())
        assert data["transaction_id"] == "TXN003"

    def test_rejected_transaction_written_with_reason(self, tmp_path):
        msg = _make_rejected_message("TXN006", reason="INVALID_CURRENCY")
        result_dir = str(tmp_path / "results")
        process_message(msg, results_dir=result_dir)
        data = json.loads((tmp_path / "results" / "TXN006.json").read_text())
        assert data["status"] == "rejected"
        assert data["reason"] == "INVALID_CURRENCY"

    def test_ack_message_has_correct_source(self, tmp_path):
        msg = _make_fraud_message()
        ack = process_message(msg, results_dir=str(tmp_path / "results"))
        assert ack["source_agent"] == "reporting_agent"

    def test_ack_message_includes_written_path(self, tmp_path):
        msg = _make_fraud_message("TXN007")
        ack = process_message(msg, results_dir=str(tmp_path / "results"))
        assert "written_path" in ack["data"]
        assert "TXN007" in ack["data"]["written_path"]

    def test_ack_message_contains_status(self, tmp_path):
        msg = _make_fraud_message("TXN008", status="approved")
        ack = process_message(msg, results_dir=str(tmp_path / "results"))
        assert ack["data"]["status"] == "approved"

    def test_creates_results_dir_if_missing(self, tmp_path):
        msg = _make_fraud_message("TXN009")
        new_dir = str(tmp_path / "deep" / "nested" / "results")
        process_message(msg, results_dir=new_dir)
        assert os.path.isdir(new_dir)

    def test_file_written_atomically(self, tmp_path):
        # After writing there should be no .tmp file leftover
        msg = _make_fraud_message("TXN010")
        result_dir = str(tmp_path / "results")
        process_message(msg, results_dir=result_dir)
        tmp_files = list((tmp_path / "results").glob("*.tmp"))
        assert tmp_files == []


# ---------------------------------------------------------------------------
# write_summary tests
# ---------------------------------------------------------------------------

class TestWriteSummary:
    def _sample_results(self) -> list[dict]:
        return [
            {"transaction_id": "TXN001", "status": "approved"},
            {"transaction_id": "TXN002", "status": "fraud_review"},
            {"transaction_id": "TXN003", "status": "approved"},
            {"transaction_id": "TXN004", "status": "approved"},
            {"transaction_id": "TXN005", "status": "fraud_review"},
            {"transaction_id": "TXN006", "status": "rejected"},
            {"transaction_id": "TXN007", "status": "rejected"},
            {"transaction_id": "TXN008", "status": "approved"},
        ]

    def test_writes_summary_file(self, tmp_path):
        write_summary(self._sample_results(), output_dir=str(tmp_path))
        assert (tmp_path / "pipeline-summary.json").exists()

    def test_total_count_correct(self, tmp_path):
        write_summary(self._sample_results(), output_dir=str(tmp_path))
        data = json.loads((tmp_path / "pipeline-summary.json").read_text())
        assert data["total"] == 8

    def test_rejected_count_correct(self, tmp_path):
        write_summary(self._sample_results(), output_dir=str(tmp_path))
        data = json.loads((tmp_path / "pipeline-summary.json").read_text())
        assert data["rejected"] == 2

    def test_fraud_review_count_correct(self, tmp_path):
        write_summary(self._sample_results(), output_dir=str(tmp_path))
        data = json.loads((tmp_path / "pipeline-summary.json").read_text())
        assert data["fraud_review"] == 2

    def test_approved_count_correct(self, tmp_path):
        write_summary(self._sample_results(), output_dir=str(tmp_path))
        data = json.loads((tmp_path / "pipeline-summary.json").read_text())
        assert data["approved"] == 4

    def test_validated_count_is_total_minus_rejected(self, tmp_path):
        write_summary(self._sample_results(), output_dir=str(tmp_path))
        data = json.loads((tmp_path / "pipeline-summary.json").read_text())
        assert data["validated"] == data["total"] - data["rejected"]

    def test_summary_has_run_timestamp(self, tmp_path):
        write_summary(self._sample_results(), output_dir=str(tmp_path))
        data = json.loads((tmp_path / "pipeline-summary.json").read_text())
        assert "run_timestamp" in data
        assert "T" in data["run_timestamp"]

    def test_empty_results_writes_zeros(self, tmp_path):
        write_summary([], output_dir=str(tmp_path))
        data = json.loads((tmp_path / "pipeline-summary.json").read_text())
        assert data["total"] == 0
        assert data["approved"] == 0
        assert data["rejected"] == 0
