"""Human-readable document information for faculty and reviewer clients (read-only)."""

from __future__ import annotations

from models import Document, FacultyProfile

from documents.faculty_name_display import (
    account_owner_name,
    extracted_name_from_document,
    resolve_faculty_name_fields,
)

from documents.ocr.queue import normalize_ocr_status
from documents.review_display import review_display_status
from documents.status_map import document_status_to_web
from faculty.rank_simulation_engine import KRA_LABELS

_CRITERION_LABELS: dict[str, str] = {
    "kra1-a": "Teaching Effectiveness",
    "kra2-a": "Research",
    "kra2-b": "Research",
    "kra3-a": "Extension",
    "kra4-a": "Professional Development",
}

_OCR_STATUS_LABELS = {
    "completed": "OCR completed",
    "processing": "Extracting text…",
    "failed": "Text extraction failed",
    "pending": "Waiting for OCR",
}


def _kra_label(kra_id: str | None) -> str:
    key = (kra_id or "").strip()
    return KRA_LABELS.get(key, key or "—")


def _criterion_label(criterion_id: str | None, indicator_id: str | None) -> str:
    cid = (criterion_id or "").strip()
    if cid in _CRITERION_LABELS:
        return _CRITERION_LABELS[cid]
    if (indicator_id or "").startswith("kra1-a"):
        return "Teaching Effectiveness"
    return cid.replace("-", " ").title() if cid else "—"


def _document_type_label(info: dict) -> str:
    for key in ("Document type", "Document evaluation composition", "Evaluation type"):
        raw = (info.get(key) or "").strip()
        if raw:
            return raw
    return "—"


def _ocr_status_label(doc: Document) -> str:
    status = normalize_ocr_status(doc.ocr_status)
    return _OCR_STATUS_LABELS.get(status, status.replace("_", " ").title())


def _review_status_label(doc: Document, *, review_display: str | None = None) -> str:
    display = (review_display or review_display_status(doc) or document_status_to_web(doc) or "").strip()
    mapping = {
        "approved": "Validated",
        "valid": "Validated",
        "pending-review": "Pending Review",
        "reviewer-required": "Pending Review",
        "revision": "Needs Revision",
        "needs_revision": "Needs Revision",
        "rejected": "Rejected",
        "draft": "Draft",
        "simulation-auto-accepted": "Pending Review",
    }
    return mapping.get(display.replace("_", "-"), display.replace("-", " ").title() or "Pending Review")


def build_document_information(
    doc: Document,
    profile: FacultyProfile | None = None,
    *,
    review_display: str | None = None,
) -> dict:
    """Unified document information block for web and mobile."""
    info = dict(doc.extracted_info or {})
    owner = account_owner_name(profile, doc)
    extracted_name = extracted_name_from_document(info)
    extraction_status = (info.get("Faculty name extraction status") or "").strip().lower()
    detected_on_doc = bool(extracted_name) and extraction_status != "not_detected"
    extraction_status = (info.get("Faculty name extraction status") or "").strip().lower()
    faculty_fields = resolve_faculty_name_fields(
        owner=owner,
        extracted_name=extracted_name,
        detected_on_doc=detected_on_doc,
        extraction_status=extraction_status,
    )
    from documents.document_ownership_verification import verify_document_ownership

    ownership = verify_document_ownership(doc, profile)

    uploaded = doc.submitted_at or doc.created_at
    return {
        **faculty_fields,
        "nameVerificationMessage": ownership.get("message"),
        "ownershipScoringEligible": ownership.get("scoringEligible"),
        "dateUploaded": uploaded.isoformat() if uploaded else None,
        "kraLabel": _kra_label(doc.kra_id),
        "criterionLabel": _criterion_label(doc.criterion_id, doc.indicator_id),
        "documentType": _document_type_label(info),
        "ocrStatus": _ocr_status_label(doc),
        "reviewStatus": _review_status_label(doc, review_display=review_display),
    }
