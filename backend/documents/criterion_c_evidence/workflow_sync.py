"""Align Document.status with Criterion C accomplishment reviewer decisions."""

from __future__ import annotations

from typing import Any

from models import Document

from documents.criterion_c_evidence.bundle import bundle_from_document, is_supporting_evidence_document


def linked_document_public_ids(bundle: dict[str, Any], primary_public_id: str) -> set[str]:
    ids: set[str] = set()
    pid = (primary_public_id or "").strip()
    if pid:
        ids.add(pid)
    checklist = bundle.get("checklist") if isinstance(bundle.get("checklist"), dict) else {}
    for entry in checklist.values():
        if not isinstance(entry, dict):
            continue
        did = (entry.get("documentId") or "").strip()
        if did:
            ids.add(did)
    for sid in bundle.get("supportingDocumentIds") or []:
        text = str(sid or "").strip()
        if text:
            ids.add(text)
    return ids


def sync_criterion_c_document_workflow_status(
    primary: Document,
    bundle: dict[str, Any],
    *,
    review_status: str | None = None,
) -> int:
    """
    When a reviewer saves an accomplishment decision, mirror it on linked source PDFs.

    Checklist slot verification is separate; this runs only after accomplishment
    approve/reject is persisted (document-level workflow for directory counts).
    """
    status = (review_status or bundle.get("reviewStatus") or "").strip().lower()
    if status not in ("approved", "rejected"):
        return 0
    target = "approved" if status == "approved" else "rejected"
    ids = linked_document_public_ids(bundle, primary.public_id)
    updated = 0
    for public_id in ids:
        doc = (
            Document.query.filter_by(
                public_id=public_id,
                faculty_profile_id=primary.faculty_profile_id,
            )
            .filter(Document.deleted_at.is_(None))
            .first()
        )
        if doc and doc.status != target:
            doc.status = target
            updated += 1
    return updated


def heal_criterion_c_workflow_status_mismatch(doc: Document) -> bool:
    """Fix legacy rows where bundle.reviewStatus is final but Document.status is still pending."""
    if is_supporting_evidence_document(doc):
        return False
    bundle = bundle_from_document(doc)
    if not isinstance(bundle, dict):
        return False
    return sync_criterion_c_document_workflow_status(doc, bundle) > 0


def heal_criterion_c_workflow_for_documents(docs: list[Document]) -> bool:
    """Batch heal for faculty directory / summary (approved accomplishment → approved PDFs)."""
    from kra_configuration.criterion_c_annex import CRITERION_C_ID

    changed = False
    for doc in docs:
        if (getattr(doc, "criterion_id", None) or "").strip() != CRITERION_C_ID:
            continue
        if heal_criterion_c_workflow_status_mismatch(doc):
            changed = True
    return changed
