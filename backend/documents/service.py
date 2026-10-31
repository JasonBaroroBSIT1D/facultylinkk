"""Document business logic and authorization."""

from __future__ import annotations

from datetime import datetime, timezone

from flask import current_app

from extensions import db
from models import AuditLog, Document, FacultyProfile, User

from documents.faculty_document_policy import faculty_can_delete, faculty_can_replace
from documents.serializers import document_to_web, stats_from_documents
from documents.status_map import QUEUE_DB, is_legacy_uploaded_draft, status_from_web
from documents.storage import resolve_path, save_upload
from documents.criterion_a_upload import (
    CRITERION_A_AUTO_INDICATOR_ID,
    CRITERION_A_ID,
    normalize_upload_classification,
)
from documents.ocr.dispatch import maybe_dispatch_inline_worker
from documents.ocr import queue as ocr_queue


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _active_docs_query():
    return Document.query.filter(Document.deleted_at.is_(None))


def faculty_profile_for_user(user: User) -> FacultyProfile | None:
    return user.faculty_profile if user else None


def get_document(public_id: str) -> Document | None:
    return _active_docs_query().filter_by(public_id=public_id).first()


def get_owned_document(public_id: str, faculty_user: User) -> Document | None:
    profile = faculty_profile_for_user(faculty_user)
    if not profile:
        return None
    return Document.query.filter_by(public_id=public_id, faculty_profile_id=profile.id).first()


def append_review_history(doc: Document, *, actor: User, action: str, remarks: str, status_after: str) -> None:
    info = dict(doc.extracted_info or {})
    history = list(info.get("reviewHistory") or [])
    history.append(
        {
            "at": utcnow().isoformat(),
            "actorId": actor.public_id,
            "actorName": actor.full_name,
            "action": action,
            "remarks": remarks,
            "status": status_after,
            "decisionSource": "reviewer_manual",
        }
    )
    info["reviewHistory"] = history[-50:]
    info["Approval decision source"] = "reviewer_manual"
    prior_source = (info.get("autoValidation") or {}).get("decisionSource")
    if prior_source == "system_auto_approval" and action in ("reject", "revision", "approve"):
        import json

        db.session.add(
            AuditLog(
                actor_user_id=actor.id,
                action="Reviewer override of SET/SEF automatic approval",
                target_id=doc.public_id,
                detail=json.dumps(
                    {
                        "documentId": doc.public_id,
                        "reviewAction": action,
                        "previousAutoApproval": True,
                        "remarks": remarks,
                    },
                    ensure_ascii=False,
                )[:4000],
            )
        )
    doc.extracted_info = info


def list_faculty_documents(profile: FacultyProfile, *, kra_id: str | None = None) -> list[Document]:
    q = _active_docs_query().filter_by(faculty_profile_id=profile.id)
    if kra_id:
        q = q.filter_by(kra_id=kra_id)
    return q.order_by(Document.created_at.desc()).all()


def list_reviewer_documents(reviewer: User) -> list[Document]:
    assigned_ids = [
        row.id
        for row in FacultyProfile.query.filter_by(reviewer_user_id=reviewer.id).all()
    ]
    if not assigned_ids:
        return []
    return (
        _active_docs_query()
        .filter(Document.faculty_profile_id.in_(assigned_ids))
        .order_by(Document.submitted_at.desc())
        .all()
    )


def list_admin_documents(*, faculty_public_id: str | None = None) -> list[Document]:
    q = _active_docs_query()
    if faculty_public_id:
        profile = FacultyProfile.query.filter_by(public_id=faculty_public_id).first()
        if not profile:
            return []
        q = q.filter_by(faculty_profile_id=profile.id)
    return q.order_by(Document.submitted_at.desc()).all()


def list_reviewer_documents_for_faculty(reviewer: User, faculty_public_id: str) -> list[Document]:
    profile = FacultyProfile.query.filter_by(public_id=faculty_public_id).first()
    if not profile or profile.reviewer_user_id != reviewer.id:
        return []
    return (
        _active_docs_query()
        .filter_by(faculty_profile_id=profile.id)
        .order_by(Document.submitted_at.desc())
        .all()
    )


def reviewer_can_access(reviewer: User, doc: Document) -> bool:
    profile = doc.faculty_profile
    return bool(profile and profile.reviewer_user_id == reviewer.id)


def faculty_owns(faculty_user: User, doc: Document) -> bool:
    profile = faculty_profile_for_user(faculty_user)
    return bool(profile and doc.faculty_profile_id == profile.id)


def create_upload(
    faculty_user: User,
    *,
    file,
    title: str,
    kra_id: str,
    criterion_id: str,
    indicator_id: str = "",
    replaces_public_id: str | None = None,
) -> Document:
    profile = faculty_profile_for_user(faculty_user)
    if not profile:
        raise ValueError("no_profile")
    try:
        kra_id, criterion_id, indicator_id = normalize_upload_classification(
            kra_id=kra_id,
            criterion_id=criterion_id,
            indicator_id=indicator_id,
        )
    except ValueError:
        raise
    title = (title or "").strip() or (file.filename if file else "Document")
    relative, digest, size, mime = save_upload(file, profile.id)
    if not replaces_public_id:
        dup_q = _active_docs_query().filter_by(
            faculty_profile_id=profile.id,
            file_hash=digest,
        )
        if criterion_id == CRITERION_A_ID and indicator_id == CRITERION_A_AUTO_INDICATOR_ID:
            duplicate = dup_q.filter_by(criterion_id=CRITERION_A_ID).first()
        else:
            duplicate = dup_q.filter_by(indicator_id=indicator_id).first()
    else:
        duplicate = None
    if duplicate:
        stored = resolve_path(relative)
        if stored and stored.is_file():
            stored.unlink()
        raise ValueError("duplicate_upload")
    replaces_id = None
    version = 1
    prev: Document | None = None
    if replaces_public_id:
        prev = get_document(replaces_public_id)
        if not prev or prev.faculty_profile_id != profile.id:
            raise ValueError("invalid_replace_target")
        if not faculty_can_replace(prev):
            raise ValueError("not_replaceable")
        replaces_id = prev.id
        version = (getattr(prev, "version_number", None) or 1) + 1
    doc = Document(
        faculty_profile_id=profile.id,
        reviewer_user_id=profile.reviewer_user_id,
        title=title,
        file_name=file.filename or title,
        file_path=relative,
        mime_type=mime,
        file_size=size,
        file_hash=digest,
        kra_id=kra_id,
        criterion_id=criterion_id,
        indicator_id=indicator_id,
        status="pending_review",
        extracted_info={},
        ocr_status="pending",
        submitted_at=utcnow(),
    )
    if hasattr(doc, "version_number"):
        doc.version_number = version
    if hasattr(doc, "replaces_document_id"):
        doc.replaces_document_id = replaces_id
    db.session.add(doc)
    if prev is not None:
        _soft_delete_document_internal(
            prev,
            actor_user=faculty_user,
            reason="replaced_by_upload",
            replacement_public_id=doc.public_id,
            via_replacement=True,
            recalculate=False,
        )
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        stored = resolve_path(relative)
        if stored and stored.is_file():
            stored.unlink()
        raise
    if prev is not None and profile:
        from faculty.estimated_score_service import recalculate_faculty_estimated_scores

        recalculate_faculty_estimated_scores(
            profile,
            actor=faculty_user,
            reason="document_replaced",
            document_id=doc.public_id,
            criterion=doc.criterion_id,
        )
    ocr_queue.enqueue_document_ocr(doc)
    try:
        maybe_dispatch_inline_worker(current_app._get_current_object())
    except RuntimeError:
        pass
    return doc


def submit_for_review(faculty_user: User, doc: Document) -> Document:
    if not faculty_owns(faculty_user, doc):
        raise ValueError("forbidden")
    if doc.status not in ("draft", "needs_revision"):
        raise ValueError("not_submittable")
    profile = doc.faculty_profile
    doc.status = "pending_review"
    doc.reviewer_user_id = profile.reviewer_user_id if profile else None
    doc.submitted_at = utcnow()
    db.session.commit()
    return doc


def apply_review_decision(
    reviewer: User,
    doc: Document,
    *,
    decision: str,
    remarks: str,
) -> Document:
    if not reviewer_can_access(reviewer, doc):
        raise ValueError("forbidden")
    remarks = (remarks or "").strip()
    decision = (decision or "").strip().lower()
    if decision == "approve":
        doc.status = "approved"
        doc.reviewer_remarks = remarks or "Approved."
        doc.reviewed_at = utcnow()
        append_review_history(doc, actor=reviewer, action="approve", remarks=doc.reviewer_remarks, status_after="approved")
    elif decision == "reject":
        if not remarks:
            raise ValueError("remarks_required")
        doc.status = "rejected"
        doc.reviewer_remarks = remarks
        doc.reviewed_at = utcnow()
        append_review_history(doc, actor=reviewer, action="reject", remarks=remarks, status_after="rejected")
    elif decision in ("revision", "revise", "needs_revision"):
        if not remarks:
            raise ValueError("remarks_required")
        doc.status = "needs_revision"
        doc.reviewer_remarks = remarks
        doc.reviewed_at = utcnow()
        append_review_history(doc, actor=reviewer, action="revision", remarks=remarks, status_after="needs_revision")
    else:
        raise ValueError("invalid_decision")
    db.session.commit()
    _recalculate_faculty_score_for_document(doc, actor=reviewer, reason="reviewer_document_decision")
    return doc


def _cancel_active_ocr_jobs(doc: Document) -> None:
    from models import DocumentOcrJob

    jobs = (
        DocumentOcrJob.query.filter_by(document_id=doc.id)
        .filter(DocumentOcrJob.status.in_(("pending", "running")))
        .all()
    )
    for job in jobs:
        job.status = "cancelled"
        job.locked_at = None
        job.locked_by = None
        job.last_error = "Cancelled — document removed by faculty."


def _soft_delete_document_internal(
    doc: Document,
    *,
    actor_user: User,
    reason: str,
    replacement_public_id: str | None = None,
    via_replacement: bool = False,
    recalculate: bool = True,
) -> None:
    if doc.deleted_at is not None:
        return
    if not via_replacement and not faculty_can_delete(doc):
        raise ValueError("not_deletable")
    _cancel_active_ocr_jobs(doc)
    tev_count = 0
    if hasattr(doc, "teaching_evaluations"):
        try:
            tev_count = doc.teaching_evaluations.count()
        except Exception:
            tev_count = len(list(doc.teaching_evaluations or []))
    info = dict(doc.extracted_info or {})
    info["Faculty soft deletion"] = utcnow().isoformat()
    info["Deletion reason"] = reason
    if replacement_public_id:
        info["Replaced by document"] = replacement_public_id
    doc.extracted_info = info
    doc.deleted_at = utcnow()
    import json

    db.session.add(
        AuditLog(
            actor_user_id=actor_user.id,
            action="Faculty document soft-deleted",
            target_id=doc.public_id,
            detail=json.dumps(
                {
                    "documentId": doc.public_id,
                    "reason": reason,
                    "status": doc.status,
                    "ocrStatus": doc.ocr_status,
                    "replacementDocumentId": replacement_public_id,
                    "teachingEvaluationRecords": tev_count,
                    "viaReplacement": via_replacement,
                },
                ensure_ascii=False,
            )[:8000],
        )
    )
    db.session.flush()
    if not recalculate:
        return
    profile = doc.faculty_profile
    if profile:
        from faculty.estimated_score_service import recalculate_faculty_estimated_scores

        recalculate_faculty_estimated_scores(
            profile,
            actor=actor_user,
            reason=f"document_soft_delete:{reason}",
            document_id=doc.public_id,
            criterion=doc.criterion_id,
        )


def soft_delete_faculty_document(faculty_user: User, doc: Document) -> None:
    if not faculty_owns(faculty_user, doc):
        raise ValueError("forbidden")
    if doc.deleted_at is not None:
        return
    _soft_delete_document_internal(
        doc,
        actor_user=faculty_user,
        reason="faculty_delete",
    )
    db.session.commit()


def patch_from_web_payload(doc: Document, body: dict) -> Document:
    """Merge reviewer mock-style updates when using PUT from web (legacy fields)."""
    web_status = body.get("status")
    if web_status:
        doc.status = status_from_web(web_status)
    if "feedback" in body or "remarks" in body:
        doc.reviewer_remarks = (body.get("feedback") or body.get("remarks") or doc.reviewer_remarks or "").strip()
    if body.get("indicatorId"):
        doc.indicator_id = body["indicatorId"]
    if body.get("kraId"):
        doc.kra_id = body["kraId"]
    if body.get("criterionId"):
        doc.criterion_id = body["criterionId"]
    review = body.get("review")
    if isinstance(review, dict) and review.get("finalScore") is not None:
        doc.verified_points = float(review["finalScore"])
        doc.reviewer_score = float(review.get("assignedScore") or review["finalScore"])
    if body.get("reviewerScore") is not None:
        doc.reviewer_score = float(body["reviewerScore"])
    extracted = dict(doc.extracted_info or {})
    if isinstance(body.get("extractedInfo"), dict):
        extracted.update(body["extractedInfo"])
        doc.extracted_info = extracted
    score_changed = isinstance(review, dict) and review.get("finalScore") is not None
    db.session.commit()
    if score_changed or web_status or isinstance(review, dict):
        _recalculate_faculty_score_for_document(doc, actor=None, reason="reviewer_document_update")
    return doc


def _recalculate_faculty_score_for_document(doc: Document, *, actor, reason: str) -> None:
    profile = doc.faculty_profile
    if not profile:
        return
    try:
        from faculty.estimated_score_service import recalculate_faculty_estimated_scores

        recalculate_faculty_estimated_scores(
            profile,
            actor=actor,
            reason=reason,
            document_id=doc.public_id,
            criterion=doc.criterion_id,
        )
    except Exception:
        db.session.rollback()


def queue_for_reviewer(reviewer: User) -> list[Document]:
    docs = list_reviewer_documents(reviewer)
    return [d for d in docs if d.status in QUEUE_DB or is_legacy_uploaded_draft(d)]


def serialize_many(docs: list[Document], *, api_base: str = "") -> list[dict]:
    return [document_to_web(d, api_base=api_base) for d in docs]


def aggregate_stats(docs: list[Document]) -> dict:
    return stats_from_documents(docs)


def retry_document_ocr(doc: Document):
    return ocr_queue.retry_document_ocr(doc)
