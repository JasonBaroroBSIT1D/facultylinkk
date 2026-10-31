"""Per-document estimated points for non–SET/SEF evidence (shared Faculty / Reviewer / Admin)."""

from __future__ import annotations

from models import Document

_EXCLUDED_STATUSES = frozenset({"rejected", "needs_revision", "draft"})
_PENDING_STATUSES = frozenset({"pending_review", "reviewer_required"})
_APPROVED_STATUSES = frozenset({"approved", "valid"})


def _info(doc: Document) -> dict:
    raw = doc.extracted_info
    return raw if isinstance(raw, dict) else {}


def _parse_score(raw: str | None) -> float | None:
    text = (raw or "").strip()
    if not text:
        return None
    try:
        val = float(text)
    except ValueError:
        return None
    if val < 0:
        return None
    return round(val, 2)


def _is_duplicate(doc: Document) -> bool:
    info = _info(doc)
    dup = (info.get("Duplicate status") or info.get("duplicateStatus") or "").strip().lower()
    return dup == "duplicate"


def _simulation_eligible(doc: Document) -> bool:
    info = _info(doc)
    flag = (info.get("Simulation eligible") or info.get("simulationEligible") or "").strip().lower()
    if flag == "yes":
        return True
    if (info.get("Scoring status") or "").strip() == "Score unavailable":
        return False
    if doc.ocr_status == "completed" and doc.status in _PENDING_STATUSES | _APPROVED_STATUSES:
        return _parse_score(info.get("System-calculated score") or info.get("Provisional score")) is not None
    return False


def effective_document_points(doc: Document) -> float | None:
    """Points this document may contribute to the unified estimated KRA total."""
    if doc.deleted_at is not None:
        return None
    if doc.status in _EXCLUDED_STATUSES:
        return None
    if _is_duplicate(doc):
        return None
    if doc.indicator_id in (
        "kra1-a-student",
        "kra1-a-supervisor",
        "kra1-a-teaching-evidence",
    ):
        return None

    if doc.status in _APPROVED_STATUSES:
        if doc.verified_points is not None and doc.verified_points >= 0:
            return round(float(doc.verified_points), 2)
        if doc.reviewer_score is not None and doc.reviewer_score >= 0:
            return round(float(doc.reviewer_score), 2)

    if doc.estimated_points is not None and float(doc.estimated_points) > 0:
        return round(float(doc.estimated_points), 2)

    if doc.status in _PENDING_STATUSES or doc.status in _APPROVED_STATUSES:
        info = _info(doc)
        if info.get("Scoring status") == "Score unavailable":
            return None
        if _simulation_eligible(doc):
            score = _parse_score(info.get("System-calculated score") or info.get("Provisional score"))
            if score is not None:
                return score
    return None


def document_counts_toward_estimate(doc: Document) -> bool:
    return effective_document_points(doc) is not None
