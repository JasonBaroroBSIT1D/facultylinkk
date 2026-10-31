"""Faculty-owned document delete/replace rules (soft delete only)."""

from __future__ import annotations

from models import Document

_PROTECTED_STATUSES = frozenset({"approved", "valid"})
_DELETABLE_STATUSES = frozenset(
    {"draft", "pending_review", "reviewer_required", "needs_revision", "rejected"}
)


def normalize_ocr_status(raw: str | None) -> str:
    text = (raw or "").strip().lower()
    if text == "complete":
        return "completed"
    return text or "pending"


def faculty_can_delete(doc: Document) -> bool:
    if getattr(doc, "deleted_at", None) is not None:
        return False
    if doc.status in _PROTECTED_STATUSES:
        return False
    ocr = normalize_ocr_status(doc.ocr_status)
    if ocr == "failed":
        return True
    if doc.status in _DELETABLE_STATUSES:
        return True
    if ocr in ("pending", "processing") and doc.status not in _PROTECTED_STATUSES:
        return True
    return False


def faculty_can_replace(doc: Document) -> bool:
    if getattr(doc, "deleted_at", None) is not None:
        return False
    if doc.status in _PROTECTED_STATUSES:
        return False
    if doc.status == "needs_revision":
        return True
    ocr = normalize_ocr_status(doc.ocr_status)
    if ocr == "failed" and doc.status not in _PROTECTED_STATUSES:
        return True
    return False


def faculty_can_request_withdrawal(doc: Document) -> bool:
    if getattr(doc, "deleted_at", None) is not None:
        return False
    return doc.status in _PROTECTED_STATUSES and (
        doc.verified_points is not None and doc.verified_points > 0
    )
