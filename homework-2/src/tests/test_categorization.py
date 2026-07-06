"""Classifier tests — 10 tests covering all categories, priorities, confidence, and edge cases."""
from services.classifier import classify
from models import ClassificationResult, Ticket


def mk(subject, description="x" * 20):
    return Ticket(
        customer_id="c",
        customer_email="a@b.com",
        customer_name="u",
        subject=subject,
        description=description,
    )


# ─── Category detection ────────────────────────────────────────────────────


def test_classify_account_access_by_login_keyword():
    t = mk("Cannot login", "I cannot login to my account")
    r = classify(t)
    assert r.category.value == "account_access"


def test_classify_technical_issue_by_error_keyword():
    t = mk("App crashes", "I keep getting an error traceback when loading")
    r = classify(t)
    assert r.category.value == "technical_issue"


def test_classify_billing_question_by_invoice_keyword():
    t = mk("Invoice overcharge", "Please check my billing invoice and refund")
    r = classify(t)
    assert r.category.value == "billing_question"


def test_classify_feature_request_by_suggestion_keyword():
    t = mk("Feature request", "I have a suggestion — please add dark mode enhancement")
    r = classify(t)
    assert r.category.value == "feature_request"


def test_classify_bug_report_by_reproduce_keyword():
    t = mk("Bug found", "Steps to reproduce: open app, click button, see defect")
    r = classify(t)
    assert r.category.value == "bug_report"


def test_classify_fallback_other():
    t = mk("Hello", "No relevant keywords here at all")
    r = classify(t)
    assert r.category.value == "other"
    assert r.priority.value == "medium"


# ─── Priority detection ────────────────────────────────────────────────────


def test_classify_urgent_priority():
    t = mk("CRITICAL issue", "Production down outage — urgent help needed")
    r = classify(t)
    assert r.priority.value == "urgent"


def test_classify_high_priority_by_blocking():
    t = mk("Blocking issue", "This is blocking our deployment asap")
    r = classify(t)
    assert r.priority.value == "high"


def test_classify_low_priority_by_minor():
    t = mk("Minor cosmetic issue", "This is a minor cosmetic no rush change")
    r = classify(t)
    assert r.priority.value == "low"


# ─── Result shape and manual override ─────────────────────────────────────


def test_classify_returns_classification_result_with_required_fields():
    t = mk("Cannot login", "My password is not working and I am locked out")
    r = classify(t)
    assert isinstance(r, ClassificationResult)
    assert 0.0 <= r.confidence <= 1.0
    assert isinstance(r.keywords_found, list)
    assert isinstance(r.reasoning, str) and len(r.reasoning) > 0
    assert r.manual_override is False
