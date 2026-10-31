"""In-app notifications for document ownership verification (faculty-facing)."""

from __future__ import annotations

from models import Document, Notification, new_public_id, User

from documents.document_ownership_verification import (
    STATUS_MISMATCH,
    STATUS_NEEDS_REVIEW,
    STATUS_NOT_DETECTED,
    verify_document_ownership
)


def notify_ownership_issue_if_needed(doc: Document) -> None:
    if not doc.faculty_profile or not doc.faculty_profile.user:
        return
    result = verify_document_ownership(doc, doc.faculty_profile)
    status = result.get("status")
    if status not in (STATUS_MISMATCH, STATUS_NOT_DETECTED, STATUS_NEEDS_REVIEW):
        return
    user: User = doc.faculty_profile.user
    kind = f"ownership_{status}"
    existing = Notification.query.filter_by(
        user_id=user.id,
        kind=kind,
        related_document_id=doc.public_id,
    ).first()
    if existing:
        return
    title = result.get("statusLabel") or "Document ownership review"
    body = result.get("message") or "Your uploaded document needs ownership review."
    note = Notification(
        public_id=new_public_id("ntf_"),
        user_id=user.id,
        title=title,
        body=body,
        kind=kind,
        related_document_id=doc.public_id,
        related_faculty_id=doc.faculty_profile.public_id,
    )
    from extensions import db

    db.session.add(note)
