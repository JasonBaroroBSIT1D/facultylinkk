"""Human-facing review status labels for SET/SEF simulation workflow.

Stored document status ``approved`` means accepted evidence within FacultyLink's
simulation workflow, not official CHED or institutional certification.
"""

from __future__ import annotations

from models import Document

from documents.status_map import document_status_to_web


def review_display_status(doc: Document) -> str:
    info = doc.extracted_info or {}
    web = document_status_to_web(doc)
    source = (info.get("Approval decision source") or "").strip()
    auto = info.get("autoValidation") if isinstance(info.get("autoValidation"), dict) else {}

    if doc.status in ("rejected",):
        return "rejected"
    if doc.status in ("needs_revision",):
        return "revision"
    if doc.status in ("approved", "valid"):
        if source == "system_auto_approval" or auto.get("decisionSource") == "system_auto_approval":
            return "simulation-auto-accepted"
        return "simulation-reviewer-validated"
    if web in ("pending-review", "reviewer-required", "draft"):
        return "pending-review"
    return web or "pending-review"
