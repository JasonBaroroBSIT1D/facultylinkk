"""Reviewer corrections to OCR-extracted metadata (audit-preserving)."""

from __future__ import annotations

from datetime import datetime, timezone

from extensions import db
from models import Document, User

from documents.service import append_review_history
from documents.ocr.set_sef_metadata import apply_set_sef_to_extracted_info

_ORIGINAL_PREFIX = "OCR original "


def _stamp_original(info: dict, field_key: str, current_value: str) -> None:
    backup_key = _ORIGINAL_PREFIX + field_key
    if backup_key not in info and current_value:
        info[backup_key] = current_value


def apply_metadata_correction(reviewer: User, doc: Document, body: dict) -> Document:
    reason = (body.get("reason") or "").strip()
    if len(reason) < 8:
        raise ValueError("reason_required")

    info = dict(doc.extracted_info or {})
    changes: list[dict] = []

    def _set(field_label: str, info_key: str, value: str | None, aliases: list[str] | None = None):
        if value is None:
            return
        value = value.strip()
        if not value:
            return
        current = (info.get(info_key) or "").strip()
        _stamp_original(info, info_key, current)
        if value == current:
            return
        info[info_key] = value
        if aliases:
            for alias in aliases:
                _stamp_original(info, alias, (info.get(alias) or "").strip())
                info[alias] = value
        changes.append({"field": field_label, "previous": current or None, "corrected": value})

    _set("Faculty name", "Faculty name", body.get("facultyName"), ["Extracted names"])
    _set("Document title", "Extracted title", body.get("extractedTitle"))
    _set("Academic year", "Academic year", body.get("academicYear"))
    _set("Semester", "Semester", body.get("academicTerm"))
    if body.get("academicYear") or body.get("academicTerm"):
        year = (info.get("Academic year") or "").strip()
        sem = (info.get("Semester") or "").strip()
        info["Extracted date"] = f"{year} · {sem}" if year and sem else year or sem or info.get("Extracted date")
    _set("Evaluation type", "Evaluation type", body.get("evaluationType"))
    _set("Overall rating", "Extracted rating", body.get("evaluationRating"))
    _set("Rating scale", "Rating scale", body.get("ratingScale"))

    if body.get("attestSupportingEvidence"):
        info["Supporting evidence verified"] = "yes"

    if not changes and not body.get("attestSupportingEvidence"):
        raise ValueError("no_changes")

    log = list(info.get("Reviewer correction log") or [])
    entry = {
        "at": datetime.now(timezone.utc).isoformat(),
        "reviewerId": reviewer.public_id,
        "reviewerName": reviewer.full_name,
        "reason": reason,
        "changes": changes,
    }
    log.append(entry)
    info["Reviewer correction log"] = log[-25:]
    info["Reviewer verified extraction"] = "yes"
    info["Validation status"] = "needs verification"

    text = (doc.extracted_text or "").strip()
    method = info.get("OCR method") or info.get("Extraction method")
    if doc.indicator_id in ("kra1-a-student", "kra1-a-supervisor") and text:
        info = apply_set_sef_to_extracted_info(
            info,
            text=text,
            indicator_id=doc.indicator_id,
            extraction_method=method,
        )
        for change in changes:
            field = change["field"]
            if field == "Faculty name":
                info["Faculty name"] = change["corrected"]
                info["Extracted names"] = change["corrected"]
            elif field == "Document title":
                info["Extracted title"] = change["corrected"]
            elif field == "Academic year":
                info["Academic year"] = change["corrected"]
            elif field == "Semester":
                info["Semester"] = change["corrected"]
            elif field == "Overall rating":
                info["Extracted rating"] = change["corrected"]
            elif field == "Rating scale":
                info["Rating scale"] = change["corrected"]
            elif field == "Evaluation type":
                info["Evaluation type"] = change["corrected"]

    doc.extracted_info = info
    append_review_history(
        doc,
        actor=reviewer,
        action="correct_metadata",
        remarks=reason,
        status_after=doc.status,
    )
    db.session.commit()
    return doc
