"""Reviewer actions on linked DocumentTeachingEvaluation rows."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from extensions import db
from models import AuditLog, Document, DocumentTeachingEvaluation, User

from documents.scoring.set_sef_aggregate import parse_rating_percent
_VALID_DECISIONS = frozenset({"approve", "reject", "revision", "needs_revision"})


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_decision(raw: str) -> str:
    value = (raw or "").strip().lower()
    if value in ("needs_revision", "revision", "revise"):
        return "needs_revision"
    if value in ("approve", "approved", "accept", "valid"):
        return "approved"
    if value in ("reject", "rejected", "deny"):
        return "rejected"
    raise ValueError("invalid_decision")


def _apply_field_corrections(
    tev: DocumentTeachingEvaluation,
    body: dict,
    *,
    changes: list[dict],
) -> None:
    def track(field_label: str, attr: str, info_key: str | None, new_val: str | None):
        if new_val is None:
            return
        new_val = new_val.strip()
        if not new_val:
            return
        old = getattr(tev, attr)
        old_str = "" if old is None else str(old).strip()
        if new_val == old_str:
            return
        setattr(tev, attr, new_val if attr != "rating_scale" else float(new_val))
        changes.append({"field": field_label, "previous": old_str or None, "corrected": new_val})
        if info_key and isinstance(tev.extracted_metadata, dict):
            meta = dict(tev.extracted_metadata)
            meta[info_key] = new_val
            tev.extracted_metadata = meta

    if body.get("evaluationType") is not None:
        et = body.get("evaluationType", "").strip().upper()
        if et in ("SET", "SEF"):
            old = tev.evaluation_type
            if et != old:
                tev.evaluation_type = et
                tev.indicator_id = DocumentTeachingEvaluation.INDICATOR_BY_TYPE[et]
                changes.append({"field": "evaluation type", "previous": old, "corrected": et})

    track("academic year", "academic_year", None, body.get("academicYear"))
    track("semester", "semester", None, body.get("semester") or body.get("academicTerm"))

    if body.get("ratingRaw") is not None or body.get("evaluationRating") is not None:
        rating = (body.get("ratingRaw") or body.get("evaluationRating") or "").strip()
        if rating:
            old = tev.rating_raw or ""
            if rating != old:
                tev.rating_raw = rating
                pct, scale = parse_rating_percent(rating)
                tev.rating_percent = pct
                if scale is not None:
                    tev.rating_scale = scale
                changes.append({"field": "overall rating", "previous": old or None, "corrected": rating})

    if body.get("ratingScale") is not None:
        scale_raw = str(body.get("ratingScale")).strip()
        if scale_raw:
            try:
                scale_f = float(scale_raw)
            except ValueError as exc:
                raise ValueError("invalid_rating_scale") from exc
            old = tev.rating_scale
            if old != scale_f:
                tev.rating_scale = scale_f
                changes.append(
                    {
                        "field": "rating scale",
                        "previous": None if old is None else str(old),
                        "corrected": scale_raw,
                    }
                )


def apply_teaching_evaluation_review(
    reviewer: User,
    doc: Document,
    tev: DocumentTeachingEvaluation,
    body: dict,
) -> DocumentTeachingEvaluation:
    if tev.document_id != doc.id:
        raise ValueError("not_found")

    decision_raw = body.get("decision") or body.get("action") or ""
    remarks = (body.get("remarks") or body.get("feedback") or "").strip()
    reason = (body.get("reason") or remarks or "").strip()

    changes: list[dict] = []
    _apply_field_corrections(tev, body, changes=changes)

    if decision_raw:
        try:
            decision = _normalize_decision(decision_raw)
        except ValueError as exc:
            raise ValueError("invalid_decision") from exc
        if decision in ("rejected", "needs_revision") and len(remarks) < 8:
            raise ValueError("remarks_required")
        if changes and len(reason) < 8:
            raise ValueError("reason_required")
        tev.reviewer_validation_status = decision
        if remarks:
            tev.reviewer_remarks = remarks
    elif changes:
        if len(reason) < 8:
            raise ValueError("reason_required")
    else:
        raise ValueError("no_changes")

    history = list(tev.correction_history_json or [])
    history.append(
        {
            "at": _utcnow_iso(),
            "reviewerId": reviewer.public_id,
            "reviewerName": reviewer.full_name,
            "decision": tev.reviewer_validation_status,
            "reason": reason or remarks or None,
            "remarks": remarks or None,
            "changes": changes,
        }
    )
    tev.correction_history_json = history[-25:]

    db.session.add(
        AuditLog(
            actor_user_id=reviewer.id,
            action="Teaching evaluation review",
            target_id=tev.public_id,
            detail=json.dumps(
                {
                    "documentId": doc.public_id,
                    "teachingEvaluationId": tev.public_id,
                    "decision": tev.reviewer_validation_status,
                    "evaluationType": tev.evaluation_type,
                    "academicYear": tev.academic_year,
                    "semester": tev.semester,
                    "changes": changes,
                },
                ensure_ascii=False,
            )[:8000],
        )
    )
    db.session.commit()
    return tev
