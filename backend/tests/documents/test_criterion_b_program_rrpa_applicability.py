"""Phase 6A.1 — RRPA/COPC applicability and implementation evidence (no PostgreSQL)."""

from __future__ import annotations

from documents.criterion_b_evidence.bundle import SLOT_STATUS_VERIFIED, apply_slot_link
from documents.criterion_b_evidence.program_applicability import (
    RRPA_APPLICABILITY_APPLICABLE,
    RRPA_APPLICABILITY_NOT_APPLICABLE,
    apply_rrpa_copc_applicability_decision,
)
from documents.criterion_b_evidence.program_checklist import (
    MANDATORY_APPROVAL_SLOTS,
    SLOT_FEASIBILITY_STUDY,
    SLOT_IMPLEMENTATION,
    SLOT_PRIMARY_CONTRIBUTION,
    SLOT_RRPA_COPC,
)
from documents.criterion_b_evidence.program_validation import validate_academic_program_bundle
from tests.documents.test_criterion_b_program_evidence import _filled_bundle


def _verify_all_mandatory(bundle: dict) -> dict:
    for slot in MANDATORY_APPROVAL_SLOTS + (SLOT_PRIMARY_CONTRIBUTION, SLOT_FEASIBILITY_STUDY):
        entry = bundle["checklist"].get(slot)
        if isinstance(entry, dict) and entry.get("documentId"):
            entry["status"] = SLOT_STATUS_VERIFIED
    return bundle


def test_rrpa_applicable_and_verified_ready_for_scoring():
    bundle = _filled_bundle()
    bundle = apply_slot_link(
        bundle,
        slot_id=SLOT_RRPA_COPC,
        supporting_document_id="doc_rrpa",
        supporting_file_hash="hash_rrpa",
    )
    apply_rrpa_copc_applicability_decision(bundle, status=RRPA_APPLICABILITY_APPLICABLE, note="")
    bundle["checklist"][SLOT_RRPA_COPC]["status"] = SLOT_STATUS_VERIFIED
    bundle = _verify_all_mandatory(bundle)
    result = validate_academic_program_bundle(bundle)
    assert result["rrpaCopcApplicability"] == "applicable"
    assert result["validationStatus"] == "valid"
    assert result["readyForScoring"] is True


def test_rrpa_applicable_but_missing_not_ready():
    bundle = _filled_bundle()
    apply_rrpa_copc_applicability_decision(bundle, status=RRPA_APPLICABILITY_APPLICABLE, note="")
    bundle = _verify_all_mandatory(bundle)
    result = validate_academic_program_bundle(bundle)
    assert "missing_rrpa_or_copc" in result["flags"]
    assert result["readyForScoring"] is False


def test_rrpa_confirmed_not_applicable_with_note_ready():
    bundle = _filled_bundle()
    apply_rrpa_copc_applicability_decision(
        bundle,
        status=RRPA_APPLICABILITY_NOT_APPLICABLE,
        note="Institutional memo: program track exempt from COPC per CHED regional office.",
        decided_by_role="reviewer",
    )
    bundle = _verify_all_mandatory(bundle)
    result = validate_academic_program_bundle(bundle)
    assert result["rrpaCopcApplicability"] == "not_applicable"
    assert result["checklistSummary"][SLOT_RRPA_COPC] == "not_applicable"
    assert result["validationStatus"] == "valid"
    assert result["readyForScoring"] is True


def test_rrpa_applicability_unknown_blocks_scoring():
    bundle = _filled_bundle()
    bundle = _verify_all_mandatory(bundle)
    result = validate_academic_program_bundle(bundle)
    assert "rrpa_copc_applicability_undetermined" in result["flags"]
    assert result["readyForScoring"] is False
    assert result["validationStatus"] in ("reviewer_required", "incomplete")


def test_implementation_evidence_missing_blocks_scoring():
    bundle = _filled_bundle()
    impl = bundle["checklist"].get(SLOT_IMPLEMENTATION)
    if isinstance(impl, dict):
        impl["documentId"] = None
        impl["status"] = "missing"
    apply_rrpa_copc_applicability_decision(
        bundle,
        status=RRPA_APPLICABILITY_NOT_APPLICABLE,
        note="Exemption documented.",
        decided_by_role="reviewer",
    )
    for slot in MANDATORY_APPROVAL_SLOTS:
        if slot == SLOT_IMPLEMENTATION:
            continue
        entry = bundle["checklist"].get(slot)
        if isinstance(entry, dict) and entry.get("documentId"):
            entry["status"] = SLOT_STATUS_VERIFIED
    bundle["checklist"][SLOT_PRIMARY_CONTRIBUTION]["status"] = SLOT_STATUS_VERIFIED
    bundle["checklist"][SLOT_FEASIBILITY_STUDY]["status"] = SLOT_STATUS_VERIFIED
    result = validate_academic_program_bundle(bundle)
    assert f"missing_{SLOT_IMPLEMENTATION}" in result["flags"]
    assert result["readyForScoring"] is False


def test_all_mandatory_and_rrpa_verified_ready():
    bundle = _filled_bundle()
    bundle = apply_slot_link(
        bundle,
        slot_id=SLOT_RRPA_COPC,
        supporting_document_id="doc_rrpa",
        supporting_file_hash="hash_rrpa",
    )
    apply_rrpa_copc_applicability_decision(bundle, status=RRPA_APPLICABILITY_APPLICABLE, note="")
    bundle["checklist"][SLOT_RRPA_COPC]["status"] = SLOT_STATUS_VERIFIED
    bundle = _verify_all_mandatory(bundle)
    result = validate_academic_program_bundle(bundle)
    assert result["readyForScoring"] is True
