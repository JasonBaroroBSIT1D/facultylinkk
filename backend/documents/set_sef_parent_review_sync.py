"""Complete parent SET/SEF PDF workflow when semester records are validated (rule-gated, audited)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from extensions import db
from models import AuditLog, Document, DocumentTeachingEvaluation, User

from documents.document_ownership_verification import verify_document_ownership
from documents.ocr.set_sef_metadata import is_set_sef_indicator
from documents.set_sef_auto_approval.assess import _ocr_completed
from documents.set_sef_parent_context import _iter_tev, child_validation_summary_for_document
from documents.storage import resolve_path


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class ParentReviewCompletionAssessment:
    ready: bool
    blockers: list[str] = field(default_factory=list)
    already_complete: bool = False
    child_summary: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ready": self.ready,
            "blockers": self.blockers,
            "alreadyComplete": self.already_complete,
            "childValidationSummary": self.child_summary,
        }


def _is_set_sef_parent(doc: Document) -> bool:
    if doc.criterion_id == "kra1-a":
        return True
    if is_set_sef_indicator(doc.indicator_id or ""):
        return True
    return len(_iter_tev(doc)) > 0


def _tev_period_key(tev: DocumentTeachingEvaluation) -> tuple[str, str, str] | None:
    et = (tev.evaluation_type or "").strip().upper()
    year = (tev.academic_year or "").strip()
    sem = (tev.semester or "").strip()
    if not et or not year or not sem:
        return None
    return (et, year, sem)


def _duplicate_tev_period_across_faculty(doc: Document, tev: DocumentTeachingEvaluation) -> str | None:
    key = _tev_period_key(tev)
    if not key or not doc.faculty_profile_id:
        return None
    from documents.service import _active_docs_query

    others = (
        _active_docs_query()
        .filter(
            Document.faculty_profile_id == doc.faculty_profile_id,
            Document.id != doc.id,
        )
        .all()
    )
    for other in others:
        for other_tev in _iter_tev(other):
            if other_tev.id == tev.id:
                continue
            if _tev_period_key(other_tev) != key:
                continue
            if other_tev.reviewer_validation_status in ("approved", "valid"):
                return (
                    f"Duplicate semester coverage: {key[0]} {key[1]} · {key[2]} "
                    f"is already validated on document {other.public_id}."
                )
            if other.status in ("approved", "valid", "pending_review", "reviewer_required"):
                return (
                    f"Another document ({other.public_id}) already covers "
                    f"{key[0]} {key[1]} · {key[2]} for this faculty."
                )
    return None


def _duplicate_file_hash(doc: Document) -> str | None:
    if not doc.file_hash:
        return None
    from documents.service import _active_docs_query

    twin = (
        _active_docs_query()
        .filter_by(
            faculty_profile_id=doc.faculty_profile_id,
            indicator_id=doc.indicator_id,
            file_hash=doc.file_hash,
        )
        .filter(Document.id != doc.id)
        .first()
    )
    if twin:
        return f"Duplicate file for the same faculty and indicator ({twin.public_id})."
    return None


def assess_parent_document_review_completion(doc: Document) -> ParentReviewCompletionAssessment:
    """Whether the source PDF may move to approved workflow after child validation."""
    counts = child_validation_summary_for_document(doc)
    blockers: list[str] = []

    if not _is_set_sef_parent(doc):
        return ParentReviewCompletionAssessment(
            ready=False,
            blockers=["Not a SET/SEF source document."],
            child_summary=counts,
        )

    if doc.status in ("approved", "valid"):
        return ParentReviewCompletionAssessment(
            ready=False,
            blockers=[],
            already_complete=True,
            child_summary=counts,
        )

    if counts["total"] <= 0:
        blockers.append("No SET/SEF semester records are linked to this PDF.")
        return ParentReviewCompletionAssessment(ready=False, blockers=blockers, child_summary=counts)

    if counts["rejected"] > 0:
        blockers.append(f"{counts['rejected']} semester evaluation record(s) were rejected.")
    unresolved = counts["pending"] + counts["incomplete"] + counts["needsRevision"]
    if unresolved > 0:
        blockers.append(f"{unresolved} semester evaluation record(s) still require review.")
    if counts["validated"] != counts["total"]:
        blockers.append("Not all semester evaluation records are validated.")

    if doc.status in ("rejected", "needs_revision"):
        blockers.append(f"Document workflow status is {doc.status.replace('_', ' ')}.")

    if not _ocr_completed(doc.ocr_status):
        blockers.append("OCR processing has not completed for this PDF.")

    if not doc.file_path or not resolve_path(doc.file_path):
        blockers.append("Original PDF file is missing or not accessible.")

    info = dict(doc.extracted_info or {})
    if info.get("Document classification status") == "needs_classification":
        blockers.append("SET/SEF document composition needs classification.")

    ownership = verify_document_ownership(doc, doc.faculty_profile)
    if not ownership.get("scoringEligible"):
        blockers.append(ownership.get("message") or "Document ownership requires manual review.")

    dup = _duplicate_file_hash(doc)
    if dup:
        blockers.append(dup)

    for tev in _iter_tev(doc):
        conflict = _duplicate_tev_period_across_faculty(doc, tev)
        if conflict:
            blockers.append(conflict)
            break

    if counts["validated"] < counts["total"]:
        extraction_status = (info.get("SET/SEF extraction status") or "").strip().lower()
        if extraction_status and extraction_status not in ("complete", "completed"):
            blockers.append("SET/SEF extraction is incomplete on the source PDF.")

    ready = len(blockers) == 0
    return ParentReviewCompletionAssessment(ready=ready, blockers=blockers, child_summary=counts)


def _resolve_reviewer_actor(doc: Document, reviewer: User | None) -> User | None:
    if reviewer:
        return reviewer
    for tev in _iter_tev(doc):
        for entry in reversed(list(tev.correction_history_json or [])):
            if not isinstance(entry, dict):
                continue
            pid = (entry.get("reviewerId") or "").strip()
            if not pid:
                continue
            user = User.query.filter_by(public_id=pid).first()
            if user:
                return user
    return None


def _append_completion_history(
    doc: Document,
    *,
    actor: User | None,
    remarks: str,
    trigger: str,
    child_total: int,
) -> None:
    info = dict(doc.extracted_info or {})
    history = list(info.get("reviewHistory") or [])
    history.append(
        {
            "at": _utcnow().isoformat(),
            "actorId": actor.public_id if actor else None,
            "actorName": actor.full_name if actor else "FacultyLink policy",
            "action": "approve",
            "remarks": remarks,
            "status": "approved",
            "decisionSource": "reviewer_semester_validation_completion",
            "trigger": trigger,
            "semesterRecordsValidated": child_total,
        }
    )
    info["reviewHistory"] = history[-50:]
    info["Approval decision source"] = "reviewer_semester_validation_completion"
    info["Parent review completion"] = {
        "trigger": trigger,
        "completedAt": _utcnow().isoformat(),
        "semesterRecordsValidated": child_total,
    }
    doc.extracted_info = info


def try_sync_parent_document_review(
    doc: Document,
    reviewer: User | None,
    *,
    trigger: str,
) -> bool:
    """
    Persist parent PDF approval when all child semester records are validated and
    document-level checks pass. Idempotent; returns True if status changed to approved.
    """
    if not _is_set_sef_parent(doc):
        return False
    if doc.status in ("approved", "valid"):
        return False

    assessment = assess_parent_document_review_completion(doc)
    if not assessment.ready:
        return False

    actor = _resolve_reviewer_actor(doc, reviewer)
    previous = doc.status
    total = assessment.child_summary.get("total") or 0
    remarks = (
        f"Source PDF review complete: all {total} linked semester evaluation record(s) "
        "are validated and document verification checks passed."
    )
    doc.status = "approved"
    doc.reviewed_at = _utcnow()
    doc.reviewer_remarks = remarks
    _append_completion_history(
        doc,
        actor=actor,
        remarks=remarks,
        trigger=trigger,
        child_total=total,
    )
    db.session.add(
        AuditLog(
            actor_user_id=actor.id if actor else None,
            action="SET/SEF parent review complete",
            target_id=doc.public_id,
            detail=json.dumps(
                {
                    "documentId": doc.public_id,
                    "previousStatus": previous,
                    "newStatus": doc.status,
                    "trigger": trigger,
                    "decisionSource": "reviewer_semester_validation_completion",
                    "childValidationSummary": assessment.child_summary,
                },
                ensure_ascii=False,
            )[:8000],
        )
    )
    db.session.commit()
    return True


def sync_set_sef_parent_reviews(
    docs: list[Document],
    reviewer: User | None,
    *,
    trigger: str,
) -> int:
    """Apply completion policy to each pending SET/SEF parent (rule-gated, not blind bulk)."""
    changed = 0
    for doc in docs:
        if doc.status in ("approved", "valid", "rejected"):
            continue
        if try_sync_parent_document_review(doc, reviewer, trigger=trigger):
            changed += 1
    return changed
