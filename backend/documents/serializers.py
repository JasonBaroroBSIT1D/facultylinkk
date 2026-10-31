"""Serialize Document rows for web and mobile clients."""

from __future__ import annotations

from models import Document, FacultyProfile, User

from documents.ocr.queue import normalize_ocr_status
from documents.teaching_evaluation_serializers import (
    apply_duplicate_period_flags,
    teaching_evaluation_to_web,
)
from documents.faculty_document_policy import (
    faculty_can_delete,
    faculty_can_replace,
    faculty_can_request_withdrawal,
)
from documents.document_info_display import build_document_information
from documents.review_display import review_display_status
from documents.set_sef_parent_context import set_sef_parent_context
from documents.status_map import document_status_to_web, is_legacy_uploaded_draft

_OCR_LIST_PREVIEW = 480


def _iso(dt) -> str | None:
    return dt.isoformat() if dt else None


def document_to_web(
    doc: Document,
    *,
    faculty: FacultyProfile | None = None,
    reviewer: User | None = None,
    api_base: str = "",
    ocr_detail: bool = False,
) -> dict:
    profile = faculty or doc.faculty_profile
    faculty_public = profile.public_id if profile else None
    faculty_name = profile.user.full_name if profile and profile.user else ""
    reviewer_user = reviewer or doc.reviewer
    extracted = dict(doc.extracted_info or {})
    history = extracted.get("reviewHistory") or []
    set_sef_ctx = set_sef_parent_context(doc)
    workflow_status = document_status_to_web(doc)
    review_display = review_display_status(doc)
    if set_sef_ctx and set_sef_ctx.get("listDisplayStatus"):
        review_display = set_sef_ctx["listDisplayStatus"]

    document_information = build_document_information(
        doc, profile, review_display=review_display
    )

    payload = {
        "id": doc.public_id,
        "name": doc.title,
        "title": doc.title,
        "fileName": doc.file_name,
        "facultyId": faculty_public,
        "facultyName": faculty_name,
        "reviewerId": reviewer_user.public_id if reviewer_user else None,
        "kraId": doc.kra_id or "",
        "criterionId": doc.criterion_id or "",
        "indicatorId": doc.indicator_id or "",
        "status": workflow_status,
        "documentWorkflowStatus": workflow_status,
        "reviewDisplayStatus": review_display,
        "setSefParentContext": set_sef_ctx,
        "approvalDecisionSource": (extracted.get("Approval decision source") or None),
        "autoValidation": extracted.get("autoValidation"),
        "submittedAt": _iso(doc.submitted_at),
        "reviewedAt": _iso(doc.reviewed_at),
        "uploadedAt": _iso(doc.created_at),
        "fileSize": doc.file_size,
        "mimeType": doc.mime_type or "",
        "hasFile": bool(doc.file_path),
        "extractedInfo": extracted,
        "documentInformation": document_information,
        "feedback": doc.reviewer_remarks or "",
        "remarks": doc.reviewer_remarks or "",
        "reviewerScore": doc.reviewer_score,
        "verifiedPoints": doc.verified_points,
        "estimatedPoints": doc.estimated_points,
        "versionNumber": getattr(doc, "version_number", None) or 1,
        "replacesDocumentId": (
            doc.replaces_document.public_id
            if getattr(doc, "replaces_document", None) is not None
            else None
        ),
        "reviewHistory": history,
        "ocr": _ocr_payload(doc, extracted, ocr_detail=ocr_detail),
        "canDelete": faculty_can_delete(doc),
        "canReplace": faculty_can_replace(doc),
        "canRequestWithdrawal": faculty_can_request_withdrawal(doc),
    }
    if doc.status == "approved" and doc.verified_points is not None:
        payload["review"] = {
            "finalScore": doc.verified_points,
            "assignedScore": doc.reviewer_score or doc.verified_points,
            "indicatorId": doc.indicator_id,
            "kraId": doc.kra_id,
            "criterionId": doc.criterion_id,
        }
    if doc.file_path and api_base:
        payload["fileApiPath"] = f"{api_base}/file"
        payload["fileUrl"] = f"{api_base}/file"
    evaluations = []
    if hasattr(doc, "teaching_evaluations"):
        try:
            evaluations = list(doc.teaching_evaluations.all())
        except Exception:
            evaluations = list(doc.teaching_evaluations or [])
    if evaluations:
        tev_web = [teaching_evaluation_to_web(row, doc, profile) for row in evaluations]
        apply_duplicate_period_flags(tev_web)
        child_count = len(tev_web)
        summary = {
            "count": child_count,
            "independentValidationRequired": True,
            "note": (
                "Each linked SET/SEF semester record requires its own reviewer "
                "validation. Document-level approval does not verify every record."
            ),
        }
        if set_sef_ctx:
            summary["childValidationSummary"] = set_sef_ctx.get("allChildValidationSummary")
            summary["summaryLine"] = set_sef_ctx.get("summaryLine")
            summary["composition"] = set_sef_ctx.get("composition")
            if set_sef_ctx.get("estimatedPointsExplanation"):
                summary["estimatedPointsExplanation"] = set_sef_ctx["estimatedPointsExplanation"]
        if ocr_detail:
            payload["teachingEvaluations"] = tev_web
        payload["teachingEvaluationSummary"] = summary
    elif ocr_detail:
        payload["teachingEvaluations"] = []
    return payload


def _ocr_payload(doc: Document, extracted: dict, *, ocr_detail: bool) -> dict:
    status = normalize_ocr_status(doc.ocr_status)
    text = (doc.extracted_text or "").strip()
    excerpt = (extracted.get("OCR excerpt") or "").strip()
    if not excerpt and text:
        excerpt = text[: _OCR_LIST_PREVIEW if not ocr_detail else 12000]
    payload = {
        "status": status,
        "confidence": doc.ocr_confidence,
        "error": extracted.get("OCR error"),
        "completedAt": extracted.get("OCR completed at") or extracted.get("OCR failed at"),
        "method": extracted.get("OCR method"),
    }
    if ocr_detail:
        payload["content"] = excerpt
        payload["extractedText"] = text or None
    elif excerpt:
        payload["contentPreview"] = excerpt[:_OCR_LIST_PREVIEW]
    if status == "completed" and not excerpt and not text:
        payload["empty"] = True
    return payload


def stats_from_documents(docs: list[Document]) -> dict:
    total = len(docs)
    pending = 0
    approved = 0
    revision = 0
    rejected = 0
    draft = 0
    for doc in docs:
        st = doc.status
        if is_legacy_uploaded_draft(doc) or st in ("pending_review", "reviewer_required"):
            pending += 1
        elif st == "draft":
            draft += 1
        elif st == "needs_revision":
            revision += 1
        elif st in ("approved", "valid"):
            approved += 1
        elif st == "rejected":
            rejected += 1
    return {
        "total": total,
        "draft": draft,
        "pendingReview": pending,
        "approved": approved,
        "needsRevision": revision,
        "rejected": rejected,
    }
