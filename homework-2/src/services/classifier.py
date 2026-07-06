"""Rule-based ticket auto-classification service."""
from __future__ import annotations

import logging
from datetime import datetime

from models import Category, ClassificationResult, Priority, Ticket

logger = logging.getLogger(__name__)

# ─── Category keyword map ────────────────────────────────────────────────────

_CATEGORY_KEYWORDS: dict[Category, list[str]] = {
    Category.account_access: [
        "login", "password", "sign in", "signin", "sign-in",
        "2fa", "two-factor", "two factor", "mfa", "auth", "authentication",
        "access denied", "locked out", "account locked", "forgot password",
        "reset password", "cannot log", "can't log",
    ],
    Category.technical_issue: [
        "error", "crash", "bug", "broken", "not working", "fails", "failure",
        "exception", "traceback", "500", "timeout", "slow", "performance",
        "not loading", "blank page", "white screen",
    ],
    Category.billing_question: [
        "billing", "invoice", "payment", "charge", "refund", "subscription",
        "plan", "pricing", "cost", "fee", "credit card", "receipt", "overcharged",
        "cancel subscription", "downgrade",
    ],
    Category.feature_request: [
        "feature", "request", "suggestion", "idea", "would be nice",
        "enhancement", "improve", "add support", "please add", "wishlist",
        "could you", "consider adding",
    ],
    Category.bug_report: [
        "reproduce", "steps to reproduce", "expected behavior", "actual behavior",
        "defect", "regression", "version", "os", "browser version",
        "screenshot attached", "workaround",
    ],
}

# ─── Priority keyword map ─────────────────────────────────────────────────────

_PRIORITY_KEYWORDS: dict[Priority, list[str]] = {
    Priority.urgent: [
        "can't access", "cannot access", "critical", "production down",
        "prod down", "security", "data breach", "data loss", "outage",
        "urgent", "emergency", "immediately",
    ],
    Priority.high: [
        "important", "blocking", "blocker", "asap", "as soon as possible",
        "high priority", "affects many", "multiple users",
    ],
    Priority.low: [
        "minor", "cosmetic", "suggestion", "low priority", "nice to have",
        "when you have time", "no rush",
    ],
}


def _text(ticket: Ticket) -> str:
    return f"{ticket.subject} {ticket.description}".lower()


def _score_category(text: str) -> tuple[Category, float, list[str]]:
    scores: dict[Category, int] = {}
    matched: dict[Category, list[str]] = {}

    for cat, keywords in _CATEGORY_KEYWORDS.items():
        hits = [kw for kw in keywords if kw in text]
        scores[cat] = len(hits)
        matched[cat] = hits

    best = max(scores, key=lambda c: scores[c])
    total_hits = sum(scores.values()) or 1
    best_hits = scores[best]

    if best_hits == 0:
        return Category.other, 0.3, []

    confidence = min(0.9, 0.4 + (best_hits / total_hits) * 0.6)
    return best, round(confidence, 2), matched[best]


def _score_priority(text: str) -> tuple[Priority, float, list[str]]:
    for priority in (Priority.urgent, Priority.high, Priority.low):
        hits = [kw for kw in _PRIORITY_KEYWORDS[priority] if kw in text]
        if hits:
            confidence = min(0.95, 0.5 + len(hits) * 0.15)
            return priority, round(confidence, 2), hits

    return Priority.medium, 0.5, []


def classify(ticket: Ticket, override: bool = False) -> ClassificationResult:
    """Classify a ticket by category and priority using keyword matching."""

    if ticket.classification and ticket.classification.manual_override and not override:
        logger.info("ticket=%s already has manual override, skipping", ticket.id)
        return ticket.classification

    text = _text(ticket)
    category, cat_conf, cat_keywords = _score_category(text)
    priority, pri_conf, pri_keywords = _score_priority(text)

    all_keywords = list(dict.fromkeys(cat_keywords + pri_keywords))
    confidence = round((cat_conf + pri_conf) / 2, 2)

    reasoning_parts = []
    if cat_keywords:
        reasoning_parts.append(
            f"Category '{category.value}' matched keywords: {', '.join(cat_keywords[:5])}"
        )
    else:
        reasoning_parts.append("No category keywords matched; defaulted to 'other'")

    if pri_keywords:
        reasoning_parts.append(
            f"Priority '{priority.value}' matched keywords: {', '.join(pri_keywords[:5])}"
        )
    else:
        reasoning_parts.append("No priority keywords matched; defaulted to 'medium'")

    result = ClassificationResult(
        category=category,
        priority=priority,
        confidence=confidence,
        reasoning=". ".join(reasoning_parts),
        keywords_found=all_keywords,
        classified_at=datetime.utcnow(),
        manual_override=False,
    )

    logger.info(
        "ticket=%s classified category=%s priority=%s confidence=%.2f",
        ticket.id,
        category.value,
        priority.value,
        confidence,
    )
    return result
