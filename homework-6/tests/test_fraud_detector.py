"""Unit tests for agents/fraud_detector.py."""
from __future__ import annotations

import pytest

from agents.fraud_detector import (
    FRAUD_RISK_THRESHOLD,
    SCORE_CROSS_BORDER,
    SCORE_HIGH_VALUE,
    SCORE_OFF_HOURS,
    compute_risk_score,
    process_message,
)
from tests.conftest import make_input_message, make_raw_transaction


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _validated_message(txn: dict) -> dict:
    txn_copy = dict(txn)
    txn_copy["status"] = "validated"
    return {
        "message_id": "test-id",
        "timestamp": "2026-03-16T10:00:00Z",
        "source_agent": "transaction_validator",
        "target_agent": "fraud_detector",
        "message_type": "transaction",
        "data": txn_copy,
    }


# ---------------------------------------------------------------------------
# compute_risk_score tests
# ---------------------------------------------------------------------------

class TestComputeRiskScore:
    def test_low_value_us_daytime_score_is_zero(self):
        txn = make_raw_transaction(amount="1500.00", country="US",
                                   timestamp="2026-03-16T10:00:00Z")
        txn["status"] = "validated"
        score, reasons = compute_risk_score(txn)
        assert score == 0
        assert reasons == []

    def test_high_value_adds_sixty_points(self):
        txn = make_raw_transaction(amount="25000.00", country="US",
                                   timestamp="2026-03-16T10:00:00Z")
        txn["status"] = "validated"
        score, reasons = compute_risk_score(txn)
        assert score == SCORE_HIGH_VALUE
        assert any("HIGH_VALUE" in r for r in reasons)

    def test_cross_border_adds_twenty_points(self):
        txn = make_raw_transaction(amount="500.00", country="DE",
                                   timestamp="2026-03-16T10:00:00Z")
        txn["status"] = "validated"
        score, reasons = compute_risk_score(txn)
        assert score == SCORE_CROSS_BORDER
        assert any("CROSS_BORDER" in r for r in reasons)

    def test_off_hours_adds_twenty_points(self):
        txn = make_raw_transaction(amount="200.00", country="US",
                                   timestamp="2026-03-16T02:47:00Z")
        txn["status"] = "validated"
        score, reasons = compute_risk_score(txn)
        assert score == SCORE_OFF_HOURS
        assert any("OFF_HOURS" in r for r in reasons)

    def test_all_three_factors_max_at_100(self):
        txn = make_raw_transaction(amount="75000.00", country="DE",
                                   timestamp="2026-03-16T01:00:00Z")
        txn["status"] = "validated"
        score, _ = compute_risk_score(txn)
        assert score == 100  # 60+20+20=100, capped at 100

    def test_high_value_and_cross_border_combined(self):
        txn = make_raw_transaction(amount="15000.00", country="GB",
                                   timestamp="2026-03-16T12:00:00Z")
        txn["status"] = "validated"
        score, reasons = compute_risk_score(txn)
        assert score == SCORE_HIGH_VALUE + SCORE_CROSS_BORDER
        assert len(reasons) == 2

    def test_invalid_timestamp_does_not_crash(self):
        txn = make_raw_transaction(amount="500.00")
        txn["status"] = "validated"
        txn["timestamp"] = "not-a-date"
        score, _ = compute_risk_score(txn)
        # Should not raise; off-hours check is skipped silently
        assert score >= 0

    def test_exactly_10000_is_not_high_value(self):
        txn = make_raw_transaction(amount="10000.00")
        txn["status"] = "validated"
        score, _ = compute_risk_score(txn)
        assert score == 0  # 10000 is not > 10000

    def test_10001_is_high_value(self):
        txn = make_raw_transaction(amount="10000.01")
        txn["status"] = "validated"
        score, _ = compute_risk_score(txn)
        assert score == SCORE_HIGH_VALUE

    def test_hour_zero_is_off_hours(self):
        txn = make_raw_transaction(timestamp="2026-03-16T00:00:00Z")
        txn["status"] = "validated"
        _, reasons = compute_risk_score(txn)
        assert any("OFF_HOURS" in r for r in reasons)

    def test_hour_six_is_not_off_hours(self):
        txn = make_raw_transaction(timestamp="2026-03-16T06:00:00Z")
        txn["status"] = "validated"
        _, reasons = compute_risk_score(txn)
        assert not any("OFF_HOURS" in r for r in reasons)


# ---------------------------------------------------------------------------
# process_message tests
# ---------------------------------------------------------------------------

class TestProcessMessage:
    def test_low_risk_returns_approved(self):
        txn = make_raw_transaction(amount="1500.00", country="US",
                                   timestamp="2026-03-16T10:00:00Z")
        result = process_message(_validated_message(txn))
        assert result["data"]["status"] == "approved"

    def test_high_value_returns_fraud_review(self):
        txn = make_raw_transaction(amount="25000.00")
        result = process_message(_validated_message(txn))
        assert result["data"]["status"] == "fraud_review"

    def test_risk_score_included_in_output(self):
        txn = make_raw_transaction(amount="25000.00")
        result = process_message(_validated_message(txn))
        assert "risk_score" in result["data"]
        assert result["data"]["risk_score"] == 60

    def test_risk_reasons_included_in_output(self):
        txn = make_raw_transaction(amount="25000.00")
        result = process_message(_validated_message(txn))
        assert "risk_reasons" in result["data"]
        assert len(result["data"]["risk_reasons"]) > 0

    def test_source_agent_is_fraud_detector(self):
        txn = make_raw_transaction()
        result = process_message(_validated_message(txn))
        assert result["source_agent"] == "fraud_detector"

    def test_target_agent_is_reporting_agent(self):
        txn = make_raw_transaction()
        result = process_message(_validated_message(txn))
        assert result["target_agent"] == "reporting_agent"

    def test_rejected_message_passes_through_unchanged(self):
        txn = make_raw_transaction()
        txn["status"] = "rejected"
        txn["reason"] = "INVALID_CURRENCY"
        msg = {
            "message_id": "test-id",
            "timestamp": "2026-03-16T10:00:00Z",
            "source_agent": "transaction_validator",
            "target_agent": "reporting_agent",
            "message_type": "transaction",
            "data": txn,
        }
        result = process_message(msg)
        assert result["data"]["status"] == "rejected"
        assert result["target_agent"] == "reporting_agent"

    def test_txn004_cross_border_off_hours_below_threshold(self):
        # TXN004: EUR, Germany, 02:47 UTC, $500 → cross-border(20) + off-hours(20) = 40 < 60
        txn = make_raw_transaction(
            transaction_id="TXN004",
            amount="500.00",
            currency="EUR",
            country="DE",
            timestamp="2026-03-16T02:47:00Z",
        )
        result = process_message(_validated_message(txn))
        assert result["data"]["status"] == "approved"
        assert result["data"]["risk_score"] == 40

    def test_message_id_is_new_uuid(self):
        txn = make_raw_transaction()
        result = process_message(_validated_message(txn))
        assert result["message_id"] != "test-id"
