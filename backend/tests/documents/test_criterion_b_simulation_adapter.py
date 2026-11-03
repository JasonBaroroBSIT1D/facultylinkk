"""Phase 5A: Criterion B simulation adapter + validation/scoring gates (no PostgreSQL)."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from documents.criterion_b_evidence.bundle import (
    SLOT_STATUS_VERIFIED,
    apply_slot_link,
    build_initial_bundle,
)
from documents.criterion_b_evidence.checklist import (
    SLOT_IMDC_APPROVAL,
    SLOT_PRIMARY_MATERIAL,
    required_slots,
)
from documents.criterion_b_evidence.cross_kra import assess_cross_kra_warnings
from documents.criterion_b_evidence.program_checklist import (
    DEVELOPMENT_STUDY_SLOTS,
    MANDATORY_APPROVAL_SLOTS,
    PROGRAM_KIND_NEW,
    PROGRAM_KIND_REVISION,
    SLOT_PRIMARY_CONTRIBUTION,
    SLOT_REVISED_CURRICULUM,
)
from documents.criterion_b_evidence.program_validation import validate_academic_program_bundle
from documents.criterion_b_evidence.validation import (
    detect_duplicate_supporting_hash,
    validate_instructional_material_bundle,
)
from documents.scoring.criterion_b_simulation_adapter import (
    aggregate_criterion_b_simulation_from_documents,
    score_primary_document_for_simulation,
)
from documents.scoring.document_evidence_points import effective_document_points
from kra_configuration.criterion_b_scoring import compute_criterion_b_indicator_points

from tests.documents.test_criterion_b_program_evidence import _filled_bundle


def _settings() -> dict:
    return {
        "criteria": {"kra1-b": {"maxPoints": 30}},
        "indicators": {
            "kra1-b-textbook-sole": {"points": 30, "maxPoints": 30},
            "kra1-b-textbook-co": {"points": 30, "maxPoints": 30},
            "kra1-b-module-sole": {"points": 16, "maxPoints": 16},
            "kra1-b-module-co": {"points": 16, "maxPoints": 16},
            "kra1-b-program-lead": {"points": 10, "maxPoints": 10},
            "kra1-b-program-contributor": {"points": 5, "maxPoints": 5},
        },
    }


def _link_all_im_supporting_slots(bundle: dict) -> dict:
    material_type = bundle.get("materialType") or ""
    authorship = bundle.get("authorship") or "sole"
    for slot in required_slots(material_type, authorship=authorship):
        entry = (bundle.get("checklist") or {}).get(slot) or {}
        if not entry.get("documentId"):
            bundle = apply_slot_link(
                bundle,
                slot_id=slot,
                supporting_document_id=f"doc_{slot}",
                supporting_file_hash=f"hash_{slot}",
            )
    return bundle


def _verify_im_checklist(bundle: dict) -> dict:
    material_type = bundle.get("materialType") or ""
    authorship = bundle.get("authorship") or "sole"
    slots = list(required_slots(material_type, authorship=authorship)) + [SLOT_PRIMARY_MATERIAL]
    checklist = bundle.setdefault("checklist", {})
    for slot in slots:
        entry = checklist.get(slot)
        if not isinstance(entry, dict):
            continue
        if entry.get("documentId"):
            entry["status"] = SLOT_STATUS_VERIFIED
            entry["ocrHintOnly"] = False
    return bundle


def _scoring_ready_im_bundle(*, indicator_id: str = "kra1-b-module-sole") -> dict:
    bundle = build_initial_bundle(
        primary_document_id="doc_primary",
        primary_file_hash="hash_primary",
        indicator_id=indicator_id,
        material_title="Calculus Module Vol. 1",
    )
    bundle = _link_all_im_supporting_slots(bundle)
    if bundle.get("materialType") in ("module", "instructional_manual"):
        bundle["completeSetDeclared"] = True
    bundle["specializationAligned"] = True
    if bundle.get("authorship") == "co":
        bundle["contributionPercent"] = 40
    bundle = _verify_im_checklist(bundle)
    return bundle


def _verify_program_slots(bundle: dict) -> dict:
    from documents.criterion_b_evidence.program_applicability import (
        RRPA_APPLICABILITY_NOT_APPLICABLE,
        apply_rrpa_copc_applicability_decision,
    )

    apply_rrpa_copc_applicability_decision(
        bundle,
        status=RRPA_APPLICABILITY_NOT_APPLICABLE,
        note="Test fixture: RRPA/COPC not applicable.",
        decided_by_role="reviewer",
    )
    kind = bundle.get("programDevelopmentKind")
    slots = list(MANDATORY_APPROVAL_SLOTS) + [SLOT_PRIMARY_CONTRIBUTION]
    if kind == PROGRAM_KIND_NEW:
        for slot in DEVELOPMENT_STUDY_SLOTS:
            if (bundle.get("checklist") or {}).get(slot, {}).get("documentId"):
                slots.append(slot)
                break
    elif kind == PROGRAM_KIND_REVISION:
        slots.append(SLOT_REVISED_CURRICULUM)
    checklist = bundle.setdefault("checklist", {})
    for slot in slots:
        entry = checklist.get(slot)
        if isinstance(entry, dict) and entry.get("documentId"):
            entry["status"] = SLOT_STATUS_VERIFIED
            entry["ocrHintOnly"] = False
    return bundle


def _scoring_ready_program_bundle(*, kind: str = PROGRAM_KIND_NEW) -> dict:
    bundle = _filled_bundle(kind=kind)
    bundle = _verify_program_slots(bundle)
    return bundle


def _primary_doc(*, bundle: dict | None, indicator_id: str, public_id: str = "doc_primary"):
    info = {}
    if bundle is not None:
        info["criterionBEvidenceBundle"] = bundle
    return SimpleNamespace(
        public_id=public_id,
        criterion_id="kra1-b",
        indicator_id=indicator_id,
        extracted_info=info,
        deleted_at=None,
        status="approved",
        verified_points=99.0,
        reviewer_score=99.0,
        estimated_points=99.0,
        ocr_status="completed",
    )


# --- Happy path (validation + adapter) ---


def test_im_happy_path_ready_for_scoring_true():
    bundle = _scoring_ready_im_bundle(indicator_id="kra1-b-module-sole")
    validation = validate_instructional_material_bundle(bundle)
    assert validation["validationStatus"] == "valid"
    assert validation["readyForScoring"] is True

    doc = _primary_doc(bundle=bundle, indicator_id="kra1-b-module-sole")
    res = score_primary_document_for_simulation(doc, settings=_settings())
    assert res is not None
    assert res.eligible is True
    assert res.points == 16.0


def test_im_coauthor_happy_path_ready_for_scoring():
    bundle = _scoring_ready_im_bundle(indicator_id="kra1-b-module-co")
    validation = validate_instructional_material_bundle(bundle)
    assert validation["readyForScoring"] is True
    doc = _primary_doc(bundle=bundle, indicator_id="kra1-b-module-co")
    res = score_primary_document_for_simulation(doc, settings=_settings())
    assert res.points == pytest.approx(6.4)


def test_program_happy_path_ready_for_scoring_true():
    bundle = _scoring_ready_program_bundle(kind=PROGRAM_KIND_NEW)
    validation = validate_academic_program_bundle(bundle)
    assert validation["validationStatus"] == "valid"
    assert validation["readyForScoring"] is True

    doc = _primary_doc(bundle=bundle, indicator_id="kra1-b-program-lead", public_id="doc_prog")
    res = score_primary_document_for_simulation(doc, settings=_settings())
    assert res.eligible is True
    assert res.points == 10.0


def test_program_revision_happy_path_ready_for_scoring():
    bundle = _scoring_ready_program_bundle(kind=PROGRAM_KIND_REVISION)
    validation = validate_academic_program_bundle(bundle)
    assert validation["readyForScoring"] is True


def test_same_material_duplicate_claims_use_highest_points_only():
    bundle_low = _scoring_ready_im_bundle(indicator_id="kra1-b-module-co")
    bundle_low["contributionPercent"] = 25
    bundle_high = _scoring_ready_im_bundle(indicator_id="kra1-b-module-co")
    bundle_high["contributionPercent"] = 50
    bundle_high["checklist"]["primary_material"]["fileHash"] = bundle_low["checklist"][
        "primary_material"
    ]["fileHash"]
    docs = [
        _primary_doc(bundle=bundle_low, indicator_id="kra1-b-module-co", public_id="low"),
        _primary_doc(bundle=bundle_high, indicator_id="kra1-b-module-co", public_id="high"),
    ]
    out = aggregate_criterion_b_simulation_from_documents(docs, settings=_settings())
    assert out["cappedTotal"] == pytest.approx(8.0)
    assert out["rawSumBeforeCap"] == pytest.approx(8.0)


def test_aggregate_caps_at_30_and_best_per_indicator():
    doc_module = _primary_doc(
        bundle=_scoring_ready_im_bundle(indicator_id="kra1-b-module-sole"),
        indicator_id="kra1-b-module-sole",
        public_id="d1",
    )
    bundle_text = _scoring_ready_im_bundle(indicator_id="kra1-b-textbook-sole")
    doc_text = _primary_doc(bundle=bundle_text, indicator_id="kra1-b-textbook-sole", public_id="d2")
    out = aggregate_criterion_b_simulation_from_documents([doc_module, doc_text], settings=_settings())
    assert out["cappedTotal"] == 30.0
    assert out["rawSumBeforeCap"] == 46.0
    assert out["estimatedPoints"] == 30.0


# --- Negative: validation gates ---


def test_missing_evidence_not_ready_for_scoring():
    bundle = build_initial_bundle(
        primary_document_id="doc_p",
        primary_file_hash="h1",
        indicator_id="kra1-b-manual-sole",
        material_title="Lab Manual",
    )
    validation = validate_instructional_material_bundle(bundle)
    assert validation["validationStatus"] in ("incomplete", "reviewer_required")
    assert validation["readyForScoring"] is False


def test_uploaded_unverified_not_ready_for_scoring():
    bundle = _link_all_im_supporting_slots(
        build_initial_bundle(
            primary_document_id="doc_p",
            primary_file_hash="h1",
            indicator_id="kra1-b-module-sole",
            material_title="Module",
        )
    )
    bundle["completeSetDeclared"] = True
    bundle["specializationAligned"] = True
    validation = validate_instructional_material_bundle(bundle)
    assert validation["readyForScoring"] is False
    assert validation["validationStatus"] == "reviewer_required"


def test_invalid_contribution_percent_blocks_scoring():
    bundle = _scoring_ready_im_bundle(indicator_id="kra1-b-textbook-co")
    bundle["contributionPercent"] = 150
    validation = validate_instructional_material_bundle(bundle)
    assert validation["readyForScoring"] is False
    doc = _primary_doc(bundle=bundle, indicator_id="kra1-b-textbook-co")
    res = score_primary_document_for_simulation(doc, settings=_settings())
    assert res.eligible is False
    assert res.points is None


def test_specialization_mismatch_invalid_not_ready():
    bundle = _scoring_ready_im_bundle()
    bundle["specializationAligned"] = False
    validation = validate_instructional_material_bundle(bundle)
    assert validation["validationStatus"] == "invalid"
    assert validation["readyForScoring"] is False


def test_program_disqualification_invalid_not_ready():
    bundle = _scoring_ready_program_bundle()
    bundle["reviewerDisqualificationConfirmed"] = True
    validation = validate_academic_program_bundle(bundle)
    assert validation["validationStatus"] == "invalid"
    assert validation["readyForScoring"] is False


def test_duplicate_supporting_hash_detected():
    bundle = _link_all_im_supporting_slots(
        build_initial_bundle(
            primary_document_id="doc_p",
            primary_file_hash="h1",
            indicator_id="kra1-b-module-sole",
            material_title="Mod",
        )
    )
    slot_hash = bundle["checklist"][SLOT_IMDC_APPROVAL]["fileHash"]
    assert detect_duplicate_supporting_hash(
        bundle, slot_id=SLOT_IMDC_APPROVAL, file_hash=slot_hash
    )


def test_cross_kra_warnings_do_not_auto_block_scoring():
    bundle = _scoring_ready_program_bundle()
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
    assert warnings
    validation = validate_academic_program_bundle(bundle)
    assert validation["readyForScoring"] is True


def test_supporting_document_zero_points_and_not_scored_by_adapter():
    supporting = SimpleNamespace(
        public_id="doc_sup",
        criterion_id="kra1-b",
        indicator_id="kra1-b-module-sole",
        extracted_info={
            "criterionBEvidenceLink": {
                "role": "supporting",
                "primaryDocumentId": "doc_primary",
                "evidenceSlot": SLOT_IMDC_APPROVAL,
            }
        },
        deleted_at=None,
        status="approved",
        verified_points=50.0,
        estimated_points=50.0,
        ocr_status="completed",
    )
    assert effective_document_points(supporting) is None
    assert score_primary_document_for_simulation(supporting, settings=_settings()) is None


def test_legacy_document_points_bypass_blocked_when_not_ready():
    """High legacy points on doc row must not flow through adapter without readyForScoring."""
    bundle = _link_all_im_supporting_slots(
        build_initial_bundle(
            primary_document_id="doc_p",
            primary_file_hash="h1",
            indicator_id="kra1-b-textbook-sole",
            material_title="Book",
        )
    )
    doc = _primary_doc(bundle=bundle, indicator_id="kra1-b-textbook-sole")
    res = score_primary_document_for_simulation(doc, settings=_settings())
    assert res.points is None
    assert res.reasons and (
        "evidence_not_verified" in res.reasons or "evidence_not_ready_for_scoring" in res.reasons
    )


def test_unverified_compute_helper_matches_adapter_gate():
    res = compute_criterion_b_indicator_points(
        "kra1-b-textbook-sole",
        evidence_verified=False,
        settings=_settings(),
    )
    assert res.points is None
