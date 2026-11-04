"""Criterion A checklist sync — legacy slots and bundle indicator identity."""

from __future__ import annotations

from documents.kra2_evidence.bundle import (
    SLOT_STATUS_PRESENT_UNVERIFIED,
    SLOT_STATUS_VERIFIED,
    build_initial_bundle,
    ensure_checklist_slots,
)
from documents.kra2_evidence.kra2_a_evidence_slots import (
    SLOT_PEER_REVIEW,
    migrate_legacy_criterion_a_checklist_slots,
)
from documents.kra2_evidence.validation import validate_kra2_bundle


def test_legacy_peer_review_slot_migrates_to_canonical():
    bundle = build_initial_bundle(
        primary_document_id="doc-primary",
        primary_file_hash="h1",
        indicator_id="kra2-a-book-sole",
    )
    checklist = bundle.setdefault("checklist", {})
    checklist["peer_review"] = {
        "status": SLOT_STATUS_PRESENT_UNVERIFIED,
        "documentId": "doc-peer-legacy",
        "fileHash": "h2",
    }
    del checklist[SLOT_PEER_REVIEW]
    changed = migrate_legacy_criterion_a_checklist_slots(checklist, indicator_id="kra2-a-book-sole")
    assert changed is True
    assert "peer_review" not in checklist
    peer = checklist[SLOT_PEER_REVIEW]
    assert peer["documentId"] == "doc-peer-legacy"
    assert ensure_checklist_slots(bundle, indicator_id="kra2-a-book-sole") is False


def test_book_sole_validation_requires_canonical_peer_slot_only():
    bundle = build_initial_bundle(
        primary_document_id="doc-primary",
        primary_file_hash="h1",
        indicator_id="kra2-a-book-sole",
    )
    bundle["submittedForReviewAt"] = "2026-01-01T00:00:00+00:00"
    bundle["metadataConfirmed"] = {
        "outputTitle": True,
        "authorsLine": True,
        "outputVenue": True,
        "publicationDate": True,
    }
    bundle["outputTitle"] = "Test Book"
    bundle["authorsLine"] = "Author"
    bundle["outputVenue"] = "University Press"
    bundle["publicationDate"] = "2025-01-01"
    cl = bundle["checklist"]
    cl["primary_output"]["status"] = SLOT_STATUS_VERIFIED
    cl[SLOT_PEER_REVIEW]["documentId"] = "doc-peer"
    cl[SLOT_PEER_REVIEW]["status"] = SLOT_STATUS_VERIFIED
    v = validate_kra2_bundle(bundle, indicator_id="kra2-a-book-sole")
    assert v["readyForApproval"] is True
    assert v["approvalBlockers"] == []
