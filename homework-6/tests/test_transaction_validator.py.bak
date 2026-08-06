"""Unit tests for agents/transaction_validator.py."""
from __future__ import annotations

from decimal import Decimal

import pytest

from agents.transaction_validator import (
    ISO_4217_CURRENCIES,
    REQUIRED_FIELDS,
    process_message,
)
from tests.conftest import make_input_message, make_raw_transaction


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _validate(txn_override: dict | None = None, **kwargs) -> dict:
    txn = make_raw_transaction(**kwargs) if not txn_override else txn_override
    return process_message(make_input_message(txn))


# ---------------------------------------------------------------------------
# Happy-path tests
# ---------------------------------------------------------------------------

class TestValidTransaction:
    def test_valid_usd_returns_validated_status(self):
        result = _validate(amount="1500.00", currency="USD")
        assert result["data"]["status"] == "validated"

    def test_valid_eur_passes(self):
        result = _validate(amount="500.00", currency="EUR", country="DE")
        assert result["data"]["status"] == "validated"

    def test_source_agent_is_transaction_validator(self):
        result = _validate()
        assert result["source_agent"] == "transaction_validator"

    def test_target_agent_is_fraud_detector(self):
        result = _validate()
        assert result["target_agent"] == "fraud_detector"

    def test_amount_normalised_to_string(self):
        result = _validate(amount="1500.00")
        assert result["data"]["amount"] == "1500.00"

    def test_currency_uppercased(self):
        result = _validate(currency="usd")
        assert result["data"]["currency"] == "USD"

    def test_message_has_message_id(self):
        result = _validate()
        assert "message_id" in result
        assert len(result["message_id"]) > 0

    def test_message_has_timestamp(self):
        result = _validate()
        assert "timestamp" in result

    def test_all_required_fields_preserved_in_output(self):
        result = _validate()
        for field in REQUIRED_FIELDS:
            assert field in result["data"]


# ---------------------------------------------------------------------------
# Rejection: missing fields
# ---------------------------------------------------------------------------

class TestMissingFields:
    def test_missing_transaction_id_rejected(self):
        txn = make_raw_transaction()
        del txn["transaction_id"]
        result = process_message(make_input_message(txn))
        assert result["data"]["status"] == "rejected"
        assert "MISSING_FIELD" in result["data"]["reason"]

    def test_missing_amount_rejected(self):
        txn = make_raw_transaction()
        del txn["amount"]
        result = process_message(make_input_message(txn))
        assert result["data"]["status"] == "rejected"

    def test_missing_currency_rejected(self):
        txn = make_raw_transaction()
        del txn["currency"]
        result = process_message(make_input_message(txn))
        assert result["data"]["status"] == "rejected"

    def test_missing_source_account_rejected(self):
        txn = make_raw_transaction()
        del txn["source_account"]
        result = process_message(make_input_message(txn))
        assert result["data"]["status"] == "rejected"

    def test_missing_field_goes_to_reporting_agent(self):
        txn = make_raw_transaction()
        del txn["transaction_id"]
        result = process_message(make_input_message(txn))
        assert result["target_agent"] == "reporting_agent"

    def test_multiple_missing_fields_listed_in_reason(self):
        txn = make_raw_transaction()
        del txn["amount"]
        del txn["currency"]
        result = process_message(make_input_message(txn))
        assert "amount" in result["data"]["reason"] or "currency" in result["data"]["reason"]


# ---------------------------------------------------------------------------
# Rejection: invalid amount
# ---------------------------------------------------------------------------

class TestInvalidAmount:
    def test_negative_amount_rejected(self):
        result = _validate(amount="-100.00")
        assert result["data"]["status"] == "rejected"
        assert result["data"]["reason"] == "INVALID_AMOUNT"

    def test_zero_amount_rejected(self):
        result = _validate(amount="0.00")
        assert result["data"]["status"] == "rejected"
        assert result["data"]["reason"] == "INVALID_AMOUNT"

    def test_non_numeric_amount_rejected(self):
        result = _validate(amount="abc")
        assert result["data"]["status"] == "rejected"
        assert result["data"]["reason"] == "INVALID_AMOUNT"

    def test_amount_uses_decimal_comparison(self):
        # 9999.99 is below 10000 — should be validated, not rejected
        result = _validate(amount="9999.99")
        assert result["data"]["status"] == "validated"

    def test_small_positive_amount_valid(self):
        result = _validate(amount="0.01")
        assert result["data"]["status"] == "validated"


# ---------------------------------------------------------------------------
# Rejection: invalid currency
# ---------------------------------------------------------------------------

class TestInvalidCurrency:
    def test_unknown_currency_rejected(self):
        result = _validate(currency="XYZ")
        assert result["data"]["status"] == "rejected"
        assert result["data"]["reason"] == "INVALID_CURRENCY"

    def test_numeric_currency_rejected(self):
        result = _validate(currency="840")
        assert result["data"]["status"] == "rejected"

    def test_empty_currency_rejected(self):
        result = _validate(currency="")
        assert result["data"]["status"] == "rejected"

    def test_valid_currencies_accepted(self):
        for currency in ["USD", "EUR", "GBP", "JPY", "CHF"]:
            result = _validate(currency=currency)
            assert result["data"]["status"] == "validated", f"{currency} should be valid"

    def test_iso_4217_list_is_non_empty(self):
        assert len(ISO_4217_CURRENCIES) > 10


# ---------------------------------------------------------------------------
# PII safety
# ---------------------------------------------------------------------------

class TestPIISafety:
    def test_account_numbers_not_in_status_validated(self, caplog):
        import logging
        with caplog.at_level(logging.INFO, logger="agents.transaction_validator"):
            _validate(source_account="ACC-SECRET-9876")
        # Account number should not appear in any log record
        for record in caplog.records:
            assert "ACC-SECRET-9876" not in record.getMessage()
