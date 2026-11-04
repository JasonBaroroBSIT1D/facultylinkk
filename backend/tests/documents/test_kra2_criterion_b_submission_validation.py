"""Criterion B bundle validation — multi-slot checklists."""

from __future__ import annotations

from documents.kra2_evidence.bundle import SLOT_STATUS_VERIFIED, build_initial_bundle
from documents.kra2_evidence.validation import validate_kra2_bundle


def test_comm_local_missing_slot_blocks_submission():
    bundle = build_initial_bundle(
        primary_document_id="doc1",
        primary_file_hash="h1",
        indicator_id="kra2-b-comm-local",
    )
    bundle["submittedForReviewAt"] = "2026-01-01T00:00:00+00:00"
    v = validate_kra2_bundle(bundle, indicator_id="kra2-b-comm-local")
    assert v["readyForSubmission"] is False
    blockers = " ".join(v.get("submissionBlockers") or [])
    assert "commercialization" in blockers.lower() or "patent_certificate" in blockers.lower()


def test_patent_grant_sole_ready_when_all_slots_verified():
    bundle = build_initial_bundle(
        primary_document_id="doc1",
        primary_file_hash="h1",
        indicator_id="kra2-b-patent-g-sole",
    )
    bundle["submittedForReviewAt"] = "2026-01-01T00:00:00+00:00"
    bundle["metadataConfirmed"] = {
        "outputTitle": True,
        "registrationNumber": True,
        "registrationDate": True,
        "authorsLine": True,
    }
    bundle["outputTitle"] = "Device"
    bundle["registrationNumber"] = "PH-1"
    bundle["registrationDate"] = "2025-01-01"
    bundle["authorsLine"] = "Inventor"
    for slot in ("primary_output", "invention_photo", "president_special_order"):
        bundle["checklist"][slot]["documentId"] = f"doc-{slot}"
        bundle["checklist"][slot]["status"] = SLOT_STATUS_VERIFIED
    v = validate_kra2_bundle(bundle, indicator_id="kra2-b-patent-g-sole")
    assert v["readyForApproval"] is True
