"""Academic program evidence bundles (Phase 2c, no PostgreSQL)."""

from __future__ import annotations

from types import SimpleNamespace

from kra_configuration.criterion_b_annex import (
    faculty_role_for_program_indicator,
    is_academic_program_indicator,
)
from kra_configuration.criterion_b_scoring import compute_criterion_b_indicator_points
from documents.criterion_b_evidence.bundle import apply_slot_link, persist_link
from documents.criterion_b_evidence.cross_kra import (
    WARNING_EXTENSION_COMMITTEE_OVERLAP,
    WARNING_SHARED_EVIDENCE_HASH,
    assess_cross_kra_warnings,
)
from documents.criterion_b_evidence.program_bundle import build_initial_program_bundle
from documents.criterion_b_evidence.program_checklist import (
    MANDATORY_APPROVAL_SLOTS,
    PROGRAM_KIND_NEW,
    PROGRAM_KIND_REVISION,
    SLOT_ACADEMIC_COUNCIL,
    SLOT_BENCHMARKING,
    SLOT_DEAN_CERTIFICATION,
    SLOT_FEASIBILITY_STUDY,
    SLOT_GOVERNING_BOARD,
    SLOT_IMPLEMENTATION,
    SLOT_PRIMARY_CONTRIBUTION,
    SLOT_REVISED_CURRICULUM,
)
from documents.criterion_b_evidence.program_validation import validate_academic_program_bundle
from documents.criterion_b_evidence.validation import detect_duplicate_supporting_hash
from documents.scoring.document_evidence_points import effective_document_points


def _filled_bundle(*, indicator_id: str = "kra1-b-program-lead", kind: str = PROGRAM_KIND_NEW):
    bundle = build_initial_program_bundle(
        primary_document_id="doc_prog",
        primary_file_hash="hash-primary",
        indicator_id=indicator_id,
        program_name="BS Data Science",
    )
    bundle["programDevelopmentKind"] = kind
    bundle["contributionDescription"] = "Led curriculum mapping and stakeholder sessions."
    for slot in (
        SLOT_DEAN_CERTIFICATION,
        SLOT_ACADEMIC_COUNCIL,
        SLOT_GOVERNING_BOARD,
        SLOT_IMPLEMENTATION,
    ):
        bundle = apply_slot_link(
            bundle,
            slot_id=slot,
            supporting_document_id=f"doc_{slot}",
            supporting_file_hash=f"hash_{slot}",
        )
    if kind == PROGRAM_KIND_NEW:
        bundle = apply_slot_link(
            bundle,
            slot_id=SLOT_FEASIBILITY_STUDY,
            supporting_document_id="doc_feas",
            supporting_file_hash="hash_feas",
        )
    else:
        bundle = apply_slot_link(
            bundle,
            slot_id=SLOT_REVISED_CURRICULUM,
            supporting_document_id="doc_rev",
            supporting_file_hash="hash_rev",
        )
    return bundle


def test_program_indicator_role_mapping():
    assert is_academic_program_indicator("kra1-b-program-lead") is True
    assert faculty_role_for_program_indicator("kra1-b-program-lead") == "lead"
    assert faculty_role_for_program_indicator("kra1-b-program-contributor") == "contributor"


def test_build_initial_program_bundle_lead():
    bundle = build_initial_program_bundle(
        primary_document_id="doc1",
        primary_file_hash="h1",
        indicator_id="kra1-b-program-lead",
        program_name="BS Nursing",
    )
    assert bundle["claimType"] == "academic_program"
    assert bundle["facultyRole"] == "lead"
    assert bundle["checklist"]["primary_contribution_document"]["documentId"] == "doc1"
    assert SLOT_DEAN_CERTIFICATION in bundle["checklist"]


def test_new_program_requires_feasibility_or_benchmarking():
    bundle = build_initial_program_bundle(
        primary_document_id="doc1",
        primary_file_hash="h1",
        indicator_id="kra1-b-program-contributor",
        program_name="BS IT",
    )
    bundle["programDevelopmentKind"] = PROGRAM_KIND_NEW
    bundle["contributionDescription"] = "Drafted OBE matrix."
    result = validate_academic_program_bundle(bundle)
    assert result["validationStatus"] == "incomplete"
    assert "development_study_required" in result["flags"]


def test_revision_requires_stakeholder_consultation():
    bundle = build_initial_program_bundle(
        primary_document_id="doc1",
        primary_file_hash="h1",
        indicator_id="kra1-b-program-lead",
        program_name="BS Education",
    )
    bundle["programDevelopmentKind"] = PROGRAM_KIND_REVISION
    bundle["contributionDescription"] = "Facilitated consultation."
    result = validate_academic_program_bundle(bundle)
    assert "revised_curriculum_consultation_required" in result["flags"]


def test_missing_mandatory_approval_is_incomplete_not_invalid():
    bundle = build_initial_program_bundle(
        primary_document_id="doc1",
        primary_file_hash="h1",
        indicator_id="kra1-b-program-lead",
        program_name="BS Math",
    )
    result = validate_academic_program_bundle(bundle)
    assert result["validationStatus"] in ("incomplete", "reviewer_required")
    assert result["validationStatus"] != "invalid"


def test_role_indicator_mismatch_is_invalid():
    bundle = build_initial_program_bundle(
        primary_document_id="doc1",
        primary_file_hash="h1",
        indicator_id="kra1-b-program-lead",
        program_name="BS Chemistry",
    )
    bundle["facultyRole"] = "contributor"
    result = validate_academic_program_bundle(bundle)
    assert result["validationStatus"] == "invalid"
    assert "role_indicator_mismatch" in result["flags"]


def test_approval_slots_present_moves_to_reviewer_required():
    bundle = _filled_bundle()
    result = validate_academic_program_bundle(bundle)
    assert result["validationStatus"] in ("reviewer_required", "incomplete")
    assert result["readyForScoring"] is False


def test_mandatory_verified_optional_missing_can_be_ready_for_scoring():
    from documents.criterion_b_evidence.bundle import SLOT_STATUS_VERIFIED
    from documents.criterion_b_evidence.program_applicability import (
        RRPA_APPLICABILITY_NOT_APPLICABLE,
        apply_rrpa_copc_applicability_decision,
    )

    bundle = _filled_bundle()
    apply_rrpa_copc_applicability_decision(
        bundle,
        status=RRPA_APPLICABILITY_NOT_APPLICABLE,
        note="Reviewer confirmed RRPA/COPC not applicable for this program.",
        decided_by_role="reviewer",
    )
    for slot in MANDATORY_APPROVAL_SLOTS + (SLOT_PRIMARY_CONTRIBUTION, SLOT_FEASIBILITY_STUDY):
        entry = bundle["checklist"].get(slot)
        if isinstance(entry, dict) and entry.get("documentId"):
            entry["status"] = SLOT_STATUS_VERIFIED
    result = validate_academic_program_bundle(bundle)
    assert result["validationStatus"] == "valid"
    assert result["readyForScoring"] is True


def test_duplicate_supporting_hash_program_slot():
    bundle = _filled_bundle()
    assert detect_duplicate_supporting_hash(
        bundle,
        slot_id=SLOT_DEAN_CERTIFICATION,
        file_hash="hash_dean_contribution_certification",
    )


def test_supporting_document_no_independent_points():
    doc = SimpleNamespace(
        deleted_at=None,
        status="pending_review",
        indicator_id="kra1-b-program-lead",
        criterion_id="kra1-b",
        extracted_info={
            "criterionBEvidenceLink": {
                "role": "supporting",
                "primaryDocumentId": "doc_prog",
                "evidenceSlot": SLOT_GOVERNING_BOARD,
            }
        },
        verified_points=None,
        reviewer_score=None,
        estimated_points=0,
        ocr_status="completed",
    )
    assert effective_document_points(doc) is None


def test_cross_kra_extension_committee_warning():
    bundle = _filled_bundle()
    bundle["committeeName"] = "Program Development Committee BS Data Science"
    peers = [
        {
            "publicId": "ext1",
            "indicatorId": "kra3-d-inst-chair",
            "title": "Institution committee — Program Development Committee BS Data Science",
            "criterionId": "kra3-d",
        }
    ]
    warnings = assess_cross_kra_warnings(bundle, peers)
    assert any(w["code"] == WARNING_EXTENSION_COMMITTEE_OVERLAP for w in warnings)


def test_cross_kra_shared_hash_warning_only():
    bundle = _filled_bundle()
    peers = [
        {
            "publicId": "kra2doc",
            "indicatorId": "kra2-a-journal-sole",
            "criterionId": "kra2-a",
            "fileHash": "hash-primary",
        }
    ]
    warnings = assess_cross_kra_warnings(bundle, peers)
    assert any(w["code"] == WARNING_SHARED_EVIDENCE_HASH for w in warnings)
    assert all(w["confidence"] == "uncertain" for w in warnings if w["code"] == WARNING_SHARED_EVIDENCE_HASH)


def test_scoring_uses_published_config_not_hardcoded():
    settings = {
        "indicators": {
            "kra1-b-program-lead": {"points": 10},
            "kra1-b-program-contributor": {"points": 5},
        }
    }
    lead = compute_criterion_b_indicator_points(
        "kra1-b-program-lead",
        evidence_verified=True,
        settings=settings,
    )
    contrib = compute_criterion_b_indicator_points(
        "kra1-b-program-contributor",
        evidence_verified=True,
        settings=settings,
    )
    assert lead.points == 10.0
    assert contrib.points == 5.0


def test_benchmarking_satisfies_new_program_study_group():
    bundle = build_initial_program_bundle(
        primary_document_id="doc1",
        primary_file_hash="h1",
        indicator_id="kra1-b-program-lead",
        program_name="BS Agriculture",
    )
    bundle["programDevelopmentKind"] = PROGRAM_KIND_NEW
    bundle["contributionDescription"] = "Benchmarking lead."
    bundle = apply_slot_link(
        bundle,
        slot_id=SLOT_BENCHMARKING,
        supporting_document_id="doc_bench",
        supporting_file_hash="hash_bench",
    )
    result = validate_academic_program_bundle(bundle)
    assert "development_study_required" not in result["flags"]
