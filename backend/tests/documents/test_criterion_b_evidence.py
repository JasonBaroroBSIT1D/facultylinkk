"""Instructional material evidence bundles (no PostgreSQL)."""

from __future__ import annotations

from types import SimpleNamespace

from documents.criterion_b_evidence.bundle import (
    apply_slot_link,
    build_initial_bundle,
    is_supporting_evidence_document,
    persist_bundle,
    persist_link,
)
from documents.criterion_b_evidence.checklist import (
    SLOT_ANNEX_C_CONTRIBUTION,
    SLOT_IMDC_APPROVAL,
    required_slots,
)
from documents.criterion_b_evidence.validation import (
    detect_duplicate_supporting_hash,
    detect_cross_claim_hash_conflict,
    validate_instructional_material_bundle,
)
from documents.scoring.document_evidence_points import effective_document_points


def _doc(**kwargs):
    return SimpleNamespace(
        deleted_at=None,
        status="pending_review",
        indicator_id=kwargs.get("indicator_id", "kra1-b-module-sole"),
        criterion_id="kra1-b",
        extracted_info=kwargs.get("extracted_info", {}),
        verified_points=None,
        reviewer_score=None,
        estimated_points=0,
        ocr_status="completed",
    )


def test_build_initial_bundle_module_sole():
    bundle = build_initial_bundle(
        primary_document_id="doc_primary",
        primary_file_hash="hash-a",
        indicator_id="kra1-b-module-sole",
        material_title="Calculus Module",
    )
    assert bundle["materialType"] == "module"
    assert bundle["authorship"] == "sole"
    assert SLOT_IMDC_APPROVAL in bundle["checklist"]
    assert bundle["checklist"]["primary_material"]["documentId"] == "doc_primary"
    assert SLOT_ANNEX_C_CONTRIBUTION not in bundle["checklist"]


def test_co_author_includes_annex_c_slot():
    bundle = build_initial_bundle(
        primary_document_id="doc_p",
        primary_file_hash="h1",
        indicator_id="kra1-b-textbook-co",
        material_title="Textbook",
    )
    assert bundle["authorship"] == "co"
    assert SLOT_ANNEX_C_CONTRIBUTION in bundle["checklist"]
    slots = required_slots("textbook", authorship="co")
    assert SLOT_ANNEX_C_CONTRIBUTION in slots


def test_multimedia_requires_originality_slots():
    slots = required_slots("multimedia", authorship="sole")
    assert "originality_proof" in slots
    assert "pedagogical_validity_proof" in slots


def test_validation_flags_missing_evidence():
    bundle = build_initial_bundle(
        primary_document_id="doc_p",
        primary_file_hash="h1",
        indicator_id="kra1-b-manual-sole",
        material_title="Lab Manual",
    )
    result = validate_instructional_material_bundle(bundle)
    assert result["validationStatus"] in ("incomplete", "reviewer_required")
    assert "complete_set_not_attested" in result["flags"]
    assert result["readyForScoring"] is False
    assert any(b["code"] == "complete_set_not_attested" for b in result["scoringBlockers"])


def test_scoring_blockers_list_unverified_uploads():
    bundle = build_initial_bundle(
        primary_document_id="doc_p",
        primary_file_hash="h1",
        indicator_id="kra1-b-textbook-sole",
        material_title="Foundations of Applied Mathematics",
    )
    checklist = bundle.setdefault("checklist", {})
    checklist["approved_syllabus"] = {
        "documentId": "doc_syl",
        "status": "present_unverified",
    }
    checklist["imdc_evaluation_approval"] = {
        "documentId": "doc_imdc",
        "status": "present_unverified",
    }
    checklist["library_certification"] = {
        "documentId": "doc_lib",
        "status": "present_unverified",
    }
    result = validate_instructional_material_bundle(bundle)
    assert result["readyForScoring"] is False
    messages = " ".join(b["message"] for b in result["scoringBlockers"])
    assert "syllabus" in messages.lower() or "Syllabus" in messages
    assert any(b.get("slotId") == "approved_syllabus" for b in result["scoringBlockers"])


def test_co_author_requires_contribution_percent():
    bundle = build_initial_bundle(
        primary_document_id="doc_p",
        primary_file_hash="h1",
        indicator_id="kra1-b-module-co",
        material_title="Shared Module",
    )
    result = validate_instructional_material_bundle(bundle)
    assert "contribution_percent_required" in result["flags"]


def test_apply_slot_link_does_not_verify():
    bundle = build_initial_bundle(
        primary_document_id="doc_p",
        primary_file_hash="h1",
        indicator_id="kra1-b-module-sole",
        material_title="Mod",
    )
    updated = apply_slot_link(
        bundle,
        slot_id=SLOT_IMDC_APPROVAL,
        supporting_document_id="doc_support",
        supporting_file_hash="hash-b",
    )
    entry = updated["checklist"][SLOT_IMDC_APPROVAL]
    assert entry["status"] == "present_unverified"
    assert entry["ocrHintOnly"] is True
    assert "doc_support" in updated["supportingDocumentIds"]


def test_duplicate_supporting_hash():
    bundle = build_initial_bundle(
        primary_document_id="doc_p",
        primary_file_hash="h1",
        indicator_id="kra1-b-module-sole",
        material_title="Mod",
    )
    bundle = apply_slot_link(
        bundle,
        slot_id=SLOT_IMDC_APPROVAL,
        supporting_document_id="doc_s1",
        supporting_file_hash="same-hash",
    )
    assert detect_duplicate_supporting_hash(bundle, slot_id=SLOT_IMDC_APPROVAL, file_hash="same-hash")


def test_cross_claim_hash_conflict():
    other = build_initial_bundle(
        primary_document_id="doc_other",
        primary_file_hash="shared",
        indicator_id="kra1-b-textbook-sole",
        material_title="Other",
    )
    assert detect_cross_claim_hash_conflict(
        primary_public_id="doc_p",
        primary_hash="h1",
        other_bundles=[other],
        candidate_hash="shared",
    )


def test_supporting_document_excluded_from_scoring():
    doc = _doc(
        extracted_info={
            "criterionBEvidenceLink": {
                "role": "supporting",
                "primaryDocumentId": "doc_p",
                "evidenceSlot": SLOT_IMDC_APPROVAL,
            }
        }
    )
    assert is_supporting_evidence_document(doc) is True
    assert effective_document_points(doc) is None


def test_persist_bundle_on_document():
    doc = _doc()
    bundle = build_initial_bundle(
        primary_document_id="doc_x",
        primary_file_hash="hx",
        indicator_id="kra1-b-multimedia-sole",
        material_title="Interactive Course",
    )
    persist_bundle(doc, bundle)
    assert "criterionBEvidenceBundle" in doc.extracted_info
    persist_link(
        doc,
        {"role": "supporting", "primaryDocumentId": "doc_x", "evidenceSlot": SLOT_IMDC_APPROVAL},
    )
    assert doc.extracted_info["criterionBEvidenceLink"]["role"] == "supporting"
