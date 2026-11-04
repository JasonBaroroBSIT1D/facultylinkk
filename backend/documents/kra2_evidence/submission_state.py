"""KRA II accomplishment submission vs document upload state."""

from __future__ import annotations

from typing import Any

from models import Document

from documents.kra2_evidence.bundle import bundle_from_document, is_supporting_evidence_document
from kra_configuration.kra2_annex import is_kra2_criterion, is_kra2_indicator


def accomplishment_submitted(bundle: dict[str, Any] | None) -> bool:
    if not isinstance(bundle, dict):
        return False
    return bool((bundle.get("submittedForReviewAt") or "").strip())


def is_kra2_primary_accomplishment(doc: Document | None) -> bool:
    if doc is None or getattr(doc, "deleted_at", None):
        return False
    if not is_kra2_criterion(getattr(doc, "criterion_id", None)):
        return False
    if not is_kra2_indicator(getattr(doc, "indicator_id", None)):
        return False
    return not is_supporting_evidence_document(doc)


def is_kra2_unsubmitted_draft(doc: Document | None) -> bool:
    """Primary KRA II accomplishment uploaded but faculty has not sent for review."""
    if not is_kra2_primary_accomplishment(doc):
        return False
    bundle = bundle_from_document(doc)
    return not accomplishment_submitted(bundle)


def reviewer_may_act_on_accomplishment(doc: Document | None) -> bool:
    return is_kra2_primary_accomplishment(doc) and not is_kra2_unsubmitted_draft(doc)


def heal_unsubmitted_kra2_document_status(doc: Document) -> bool:
    """Move mistaken pending_review uploads back to draft (no bundle submit timestamp)."""
    if not is_kra2_unsubmitted_draft(doc):
        return False
    if doc.status in ("pending_review", "reviewer_required"):
        doc.status = "draft"
        return True
    return False
