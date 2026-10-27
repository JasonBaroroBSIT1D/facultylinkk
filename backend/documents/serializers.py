"""Serialize Document rows for web and mobile clients."""

from __future__ import annotations

from models import Document, FacultyProfile, User

from documents.status_map import status_to_web


def _iso(dt) -> str | None:
    return dt.isoformat() if dt else None


def document_to_web(
    doc: Document,
    *,
    faculty: FacultyProfile | None = None,
    reviewer: User | None = None,
    api_base: str = "",
) -> dict:
    profile = faculty or doc.faculty_profile
    faculty_public = profile.public_id if profile else None
    faculty_name = profile.user.full_name if profile and profile.user else ""
    reviewer_user = reviewer or doc.reviewer
    extracted = dict(doc.extracted_info or {})
    history = extracted.get("reviewHistory") or []
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
        "status": status_to_web(doc.status),
        "submittedAt": _iso(doc.submitted_at),
        "reviewedAt": _iso(doc.reviewed_at),
        "uploadedAt": _iso(doc.created_at),
        "fileSize": doc.file_size,
        "mimeType": doc.mime_type or "",
        "hasFile": bool(doc.file_path),
        "extractedInfo": extracted,
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
        "ocr": {
            "status": doc.ocr_status or "pending",
            "confidence": doc.ocr_confidence,
        },
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
        if st == "draft":
            draft += 1
        elif st in ("pending_review", "reviewer_required"):
            pending += 1
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
