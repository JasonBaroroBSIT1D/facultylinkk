"""Criterion B bundle preservation across OCR merges (no PostgreSQL)."""

from __future__ import annotations

from types import SimpleNamespace

from documents.criterion_b_evidence.bundle import (
    CLAIM_TYPE_INSTRUCTIONAL_MATERIAL,
    build_initial_bundle,
    persist_bundle,
)
from documents.criterion_b_evidence.extracted_info_merge import (
    merge_criterion_b_evidence_bundles,
    preserve_criterion_b_extracted_info,
)
from documents.criterion_b_evidence.service import attach_supporting_upload_link
from documents.scoring.document_evidence_points import effective_document_points
def test_initial_instructional_bundle_has_claim_type():
    bundle = build_initial_bundle(
        primary_document_id="doc_p",
        primary_file_hash="hash_p",
        indicator_id="kra1-b-module-sole",
        material_title="Sample Module",
    )
    assert bundle["claimType"] == CLAIM_TYPE_INSTRUCTIONAL_MATERIAL


def test_preserve_extracted_info_keeps_checklist_links_when_ocr_strips_slots():
    before = {
        "criterionBEvidenceBundle": {
            "claimType": CLAIM_TYPE_INSTRUCTIONAL_MATERIAL,
            "materialType": "module",
            "checklist": {
                "imdc_evaluation_approval": {
                    "status": "present_unverified",
                    "documentId": "doc_s1",
                    "fileHash": "hash_s1",
                }
            },
        }
    }
    after = {
        "OCR excerpt": "noise",
        "criterionBEvidenceBundle": {
            "claimType": None,
            "materialType": "module",
            "checklist": {
                "imdc_evaluation_approval": {
                    "status": "missing",
                    "documentId": None,
                }
            },
        },
    }
    merged = preserve_criterion_b_extracted_info(before=before, after=after)
    bundle = merged["criterionBEvidenceBundle"]
    assert bundle["claimType"] == CLAIM_TYPE_INSTRUCTIONAL_MATERIAL
    entry = bundle["checklist"]["imdc_evaluation_approval"]
    assert entry["documentId"] == "doc_s1"
    assert merged["OCR excerpt"] == "noise"


def test_merge_bundles_keeps_verified_slot_over_incoming_unverified():
    preserved = {
        "checklist": {
            "dean_contribution_certification": {
                "status": "verified",
                "documentId": "doc_d",
                "reviewerNote": "confirmed",
            }
        }
    }
    incoming = {
        "checklist": {
            "dean_contribution_certification": {
                "status": "present_unverified",
                "documentId": "doc_d",
            }
        }
    }
    merged = merge_criterion_b_evidence_bundles(preserved, incoming)
    assert merged["checklist"]["dean_contribution_certification"]["status"] == "verified"


def test_simulated_stale_ocr_write_vs_refresh_pattern():
    """Stale session write drops checklist; refresh-then-merge pattern keeps links."""
    live = {
        "criterionBEvidenceBundle": {
            "claimType": CLAIM_TYPE_INSTRUCTIONAL_MATERIAL,
            "checklist": {
                "library_certification": {
                    "documentId": "doc_lib",
                    "status": "present_unverified",
                }
            },
        }
    }
    stale_snapshot = {
        "criterionBEvidenceBundle": {
            "claimType": CLAIM_TYPE_INSTRUCTIONAL_MATERIAL,
            "checklist": {},
        }
    }
    stale_write = dict(stale_snapshot)
    stale_write["OCR excerpt"] = "text"
    stale_write["criterionBEvidenceBundle"] = stale_snapshot["criterionBEvidenceBundle"]

    refreshed_write = preserve_criterion_b_extracted_info(before=live, after=stale_write)
    assert refreshed_write["criterionBEvidenceBundle"]["checklist"]["library_certification"]["documentId"] == "doc_lib"

    assert stale_write["criterionBEvidenceBundle"]["checklist"] == {}


def test_attach_supporting_idempotent_same_document():
    primary = SimpleNamespace(
        public_id="doc_primary",
        faculty_profile_id=1,
        file_hash="hash_primary",
        criterion_id="kra1-b",
        kra_id="kra1",
        indicator_id="kra1-b-module-sole",
        extracted_info={},
    )
    supporting = SimpleNamespace(
        public_id="doc_support",
        faculty_profile_id=1,
        file_hash="hash_support",
        criterion_id="kra1-b",
        kra_id="kra1",
        indicator_id="kra1-b-module-sole",
        extracted_info={},
    )
    bundle = build_initial_bundle(
        primary_document_id="doc_primary",
        primary_file_hash="hash_primary",
        indicator_id="kra1-b-module-sole",
        material_title="Module",
    )
    persist_bundle(primary, bundle)

    from documents.criterion_b_evidence import service as service_module

    original_get = service_module.get_document

    def fake_get(public_id: str):
        return primary if public_id == "doc_primary" else None

    class FakeSession:
        @staticmethod
        def refresh(_obj):
            return None

    original_peers = service_module.peer_document_summaries

    service_module.get_document = fake_get
    service_module.db.session.refresh = FakeSession.refresh
    service_module.peer_document_summaries = lambda *args, **kwargs: []
    try:
        attach_supporting_upload_link(
            supporting,
            primary_public_id="doc_primary",
            evidence_slot="imdc_evaluation_approval",
        )
        attach_supporting_upload_link(
            supporting,
            primary_public_id="doc_primary",
            evidence_slot="imdc_evaluation_approval",
        )
    finally:
        service_module.get_document = original_get
        service_module.peer_document_summaries = original_peers

    link = supporting.extracted_info.get("criterionBEvidenceLink", {})
    assert link.get("evidenceSlot") == "imdc_evaluation_approval"
    slot = primary.extracted_info["criterionBEvidenceBundle"]["checklist"]["imdc_evaluation_approval"]
    assert slot.get("documentId") == "doc_support"


def test_supporting_document_no_independent_points_unchanged():
    doc = SimpleNamespace(
        deleted_at=None,
        status="pending_review",
        indicator_id="kra1-b-module-sole",
        criterion_id="kra1-b",
        extracted_info={
            "criterionBEvidenceLink": {
                "role": "supporting",
                "primaryDocumentId": "doc_primary",
                "evidenceSlot": "imdc_evaluation_approval",
            }
        },
        verified_points=None,
        reviewer_score=None,
        estimated_points=0,
        ocr_status="completed",
    )
    assert effective_document_points(doc) is None


def test_set_sef_pipeline_not_applied_to_criterion_b_indicator():
    from documents.criterion_a_upload import should_run_set_sef_pipeline

    assert should_run_set_sef_pipeline(indicator_id="kra1-b-module-sole", criterion_id="kra1-b") is False
