"""Integration tests — full pipeline end-to-end."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from integrator import (
    _finalize_stage,
    _make_input_message,
    _run_stage,
    _setup_dirs,
    main,
    run_pipeline,
)
from agents.transaction_validator import process_message as validate

SAMPLE_TRANSACTIONS_PATH = Path(__file__).parent.parent / "sample-transactions.json"


def _load_sample_transactions() -> list[dict]:
    with open(SAMPLE_TRANSACTIONS_PATH, encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# run_pipeline() integration tests
# ---------------------------------------------------------------------------

class TestRunPipeline:
    def test_all_transactions_processed(self, tmp_path):
        txns = _load_sample_transactions()
        shared = tmp_path / "shared"
        _setup_dirs(shared)
        results = run_pipeline(txns, shared_dir=shared)
        assert len(results) == 8

    def test_approved_transactions_returned(self, tmp_path):
        txns = _load_sample_transactions()
        shared = tmp_path / "shared"
        _setup_dirs(shared)
        results = run_pipeline(txns, shared_dir=shared)
        approved = [r for r in results if r["status"] == "approved"]
        # TXN001, TXN003, TXN004, TXN008 → 4 approved
        assert len(approved) == 4

    def test_fraud_review_transactions_returned(self, tmp_path):
        txns = _load_sample_transactions()
        shared = tmp_path / "shared"
        _setup_dirs(shared)
        results = run_pipeline(txns, shared_dir=shared)
        fraud = [r for r in results if r["status"] == "fraud_review"]
        # TXN002 ($25k), TXN005 ($75k)
        assert len(fraud) == 2

    def test_rejected_transactions_returned(self, tmp_path):
        txns = _load_sample_transactions()
        shared = tmp_path / "shared"
        _setup_dirs(shared)
        results = run_pipeline(txns, shared_dir=shared)
        rejected = [r for r in results if r["status"] == "rejected"]
        # TXN006 (XYZ currency), TXN007 (negative amount)
        assert len(rejected) == 2

    def test_result_files_written_to_disk(self, tmp_path):
        txns = _load_sample_transactions()
        shared = tmp_path / "shared"
        _setup_dirs(shared)
        run_pipeline(txns, shared_dir=shared)
        result_files = list((shared / "results").glob("TXN*.json"))
        assert len(result_files) == 8

    def test_summary_file_written(self, tmp_path):
        txns = _load_sample_transactions()
        shared = tmp_path / "shared"
        _setup_dirs(shared)
        from agents.reporting_agent import write_summary
        results = run_pipeline(txns, shared_dir=shared)
        write_summary(results, output_dir=str(shared / "results"))
        assert (shared / "results" / "pipeline-summary.json").exists()

    def test_txn006_invalid_currency_rejected(self, tmp_path):
        txns = _load_sample_transactions()
        txn006 = next(t for t in txns if t["transaction_id"] == "TXN006")
        shared = tmp_path / "shared"
        _setup_dirs(shared)
        results = run_pipeline([txn006], shared_dir=shared)
        assert results[0]["status"] == "rejected"

    def test_txn007_negative_amount_rejected(self, tmp_path):
        txns = _load_sample_transactions()
        txn007 = next(t for t in txns if t["transaction_id"] == "TXN007")
        shared = tmp_path / "shared"
        _setup_dirs(shared)
        results = run_pipeline([txn007], shared_dir=shared)
        assert results[0]["status"] == "rejected"

    def test_txn002_high_value_fraud_review(self, tmp_path):
        txns = _load_sample_transactions()
        txn002 = next(t for t in txns if t["transaction_id"] == "TXN002")
        shared = tmp_path / "shared"
        _setup_dirs(shared)
        results = run_pipeline([txn002], shared_dir=shared)
        assert results[0]["status"] == "fraud_review"

    def test_txn001_standard_transfer_approved(self, tmp_path):
        txns = _load_sample_transactions()
        txn001 = next(t for t in txns if t["transaction_id"] == "TXN001")
        shared = tmp_path / "shared"
        _setup_dirs(shared)
        results = run_pipeline([txn001], shared_dir=shared)
        assert results[0]["status"] == "approved"

    def test_result_file_for_rejected_has_reason(self, tmp_path):
        txns = _load_sample_transactions()
        txn006 = next(t for t in txns if t["transaction_id"] == "TXN006")
        shared = tmp_path / "shared"
        _setup_dirs(shared)
        run_pipeline([txn006], shared_dir=shared)
        result_path = shared / "results" / "TXN006.json"
        data = json.loads(result_path.read_text())
        assert data["status"] == "rejected"
        assert data["reason"] is not None

    def test_empty_transactions_list_runs_cleanly(self, tmp_path):
        shared = tmp_path / "shared"
        _setup_dirs(shared)
        results = run_pipeline([], shared_dir=shared)
        assert results == []


# ---------------------------------------------------------------------------
# File-based message protocol tests — prove hand-offs are real files, not
# just in-memory dicts passed between Python calls.
# ---------------------------------------------------------------------------

class TestFileBasedProtocol:
    def test_transient_dirs_empty_after_full_run(self, tmp_path):
        """input/, processing/, and output/ are mailboxes: every message
        that passes through them must be consumed by the next stage, so
        none of them should hold leftover files once the run completes."""
        txns = _load_sample_transactions()
        shared = tmp_path / "shared"
        _setup_dirs(shared)
        run_pipeline(txns, shared_dir=shared)

        assert list((shared / "input").glob("*.json")) == []
        assert list((shared / "processing").glob("*.json")) == []
        assert list((shared / "output").glob("*.json")) == []

    def test_input_message_written_to_disk_before_validation(self, tmp_path):
        """The integrator must persist the raw message to shared/input/
        as a JSON file before handing it to the validator — not just
        keep it as a Python dict."""
        shared = tmp_path / "shared"
        _setup_dirs(shared)
        txn001 = next(
            t for t in _load_sample_transactions() if t["transaction_id"] == "TXN001"
        )
        input_msg = _make_input_message(txn001)
        input_path = shared / "input" / "TXN001.json"
        input_path.write_text(json.dumps(input_msg, default=str), encoding="utf-8")

        assert input_path.exists()
        on_disk = json.loads(input_path.read_text())
        assert on_disk["data"]["transaction_id"] == "TXN001"
        assert on_disk["target_agent"] == "transaction_validator"

    def test_run_stage_moves_message_through_processing_to_output(self, tmp_path):
        """_run_stage() must move the file into processing/ while the
        agent runs, then land the result in output/ — proving the hand-off
        is file-based rather than an in-memory function call."""
        shared = tmp_path / "shared"
        _setup_dirs(shared)
        txn001 = next(
            t for t in _load_sample_transactions() if t["transaction_id"] == "TXN001"
        )
        input_msg = _make_input_message(txn001)
        input_path = shared / "input" / "TXN001.json"
        input_path.write_text(json.dumps(input_msg, default=str), encoding="utf-8")

        result = _run_stage(input_path, shared / "processing", shared / "output", validate)

        assert not input_path.exists(), "message must be moved out of input/"
        assert not (shared / "processing" / "TXN001.json").exists(), (
            "processing/ copy must be cleared once the agent is done"
        )
        output_path = shared / "output" / "TXN001.json"
        assert output_path.exists(), "agent result must be written to output/"
        on_disk = json.loads(output_path.read_text())
        assert on_disk["data"]["status"] == "validated"
        assert result["data"]["status"] == "validated"

    def test_finalize_stage_writes_directly_to_results(self, tmp_path):
        shared = tmp_path / "shared"
        _setup_dirs(shared)
        txn006 = next(
            t for t in _load_sample_transactions() if t["transaction_id"] == "TXN006"
        )
        input_msg = _make_input_message(txn006)
        input_path = shared / "input" / "TXN006.json"
        input_path.write_text(json.dumps(input_msg, default=str), encoding="utf-8")
        validated_msg = _run_stage(input_path, shared / "processing", shared / "output", validate)

        output_path = shared / "output" / "TXN006.json"
        ack = _finalize_stage(output_path, shared / "processing", shared / "results")

        assert not output_path.exists()
        assert (shared / "results" / "TXN006.json").exists()
        assert ack["data"]["status"] == "rejected"


# ---------------------------------------------------------------------------
# _setup_dirs tests
# ---------------------------------------------------------------------------

class TestMain:
    def test_main_runs_on_sample_transactions(self, tmp_path, monkeypatch, capsys):
        import sys
        shared = tmp_path / "shared"
        monkeypatch.setattr(
            sys, "argv",
            [
                "integrator.py",
                "--input", str(SAMPLE_TRANSACTIONS_PATH),
                "--shared-dir", str(shared),
            ],
        )
        main()
        captured = capsys.readouterr()
        assert "Pipeline complete" in captured.out
        assert "8 transactions processed" in captured.out

    def test_main_creates_summary_file(self, tmp_path, monkeypatch):
        import sys
        shared = tmp_path / "shared"
        monkeypatch.setattr(
            sys, "argv",
            [
                "integrator.py",
                "--input", str(SAMPLE_TRANSACTIONS_PATH),
                "--shared-dir", str(shared),
            ],
        )
        main()
        assert (shared / "results" / "pipeline-summary.json").exists()


class TestSetupDirs:
    def test_creates_all_subdirs(self, tmp_path):
        shared = tmp_path / "shared"
        _setup_dirs(shared)
        for sub in ("input", "processing", "output", "results"):
            assert (shared / sub).is_dir()

    def test_clears_input_dir(self, tmp_path):
        shared = tmp_path / "shared"
        _setup_dirs(shared)
        (shared / "input" / "leftover.json").write_text("{}")
        _setup_dirs(shared)
        assert not (shared / "input" / "leftover.json").exists()

    def test_clears_processing_dir(self, tmp_path):
        shared = tmp_path / "shared"
        _setup_dirs(shared)
        (shared / "processing" / "leftover.json").write_text("{}")
        _setup_dirs(shared)
        assert not (shared / "processing" / "leftover.json").exists()

    def test_clears_output_dir(self, tmp_path):
        shared = tmp_path / "shared"
        _setup_dirs(shared)
        (shared / "output" / "leftover.json").write_text("{}")
        _setup_dirs(shared)
        assert not (shared / "output" / "leftover.json").exists()

    def test_preserves_results_between_runs(self, tmp_path):
        shared = tmp_path / "shared"
        _setup_dirs(shared)
        (shared / "results" / "TXN001.json").write_text('{"status": "approved"}')
        _setup_dirs(shared)
        # results/ is NOT cleared on re-setup
        assert (shared / "results" / "TXN001.json").exists()
