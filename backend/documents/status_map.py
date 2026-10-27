"""Map PostgreSQL document statuses to web/mobile kebab-case labels."""

from __future__ import annotations

DB_TO_WEB = {
    "draft": "draft",
    "pending_review": "pending-review",
    "reviewer_required": "reviewer-required",
    "needs_revision": "revision",
    "approved": "approved",
    "rejected": "rejected",
    "valid": "approved",
}

WEB_TO_DB = {
    "draft": "draft",
    "pending-review": "pending_review",
    "reviewer-required": "reviewer_required",
    "revision": "needs_revision",
    "approved": "approved",
    "rejected": "rejected",
    "system-approved": "pending_review",
    "invalid": "reviewer_required",
}

PENDING_DB = frozenset({"pending_review", "needs_revision", "reviewer_required"})
QUEUE_DB = frozenset({"pending_review", "needs_revision", "reviewer_required"})


def status_to_web(db_status: str | None) -> str:
    if not db_status:
        return "pending-review"
    return DB_TO_WEB.get(db_status, db_status.replace("_", "-"))


def status_from_web(web_status: str | None) -> str:
    if not web_status:
        return "pending_review"
    return WEB_TO_DB.get(web_status, web_status.replace("-", "_"))
