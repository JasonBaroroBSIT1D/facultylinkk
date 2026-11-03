"""Phase 5A.1 — Criterion B aggregation and program validation policy tests."""

from __future__ import annotations

from types import SimpleNamespace

from documents.criterion_b_evidence.bundle import (
    SLOT_STATUS_VERIFIED,
    apply_slot_link,
    build_initial_bundle,
)
from documents.criterion_b_evidence.checklist import SLOT_PRIMARY_MATERIAL, required_slots
from documents.criterion_b_evidence.program_checklist import (
    MANDATORY_APPROVAL_SLOTS,
    PROGRAM_KIND_NEW,
    SLOT_PRIMARY_CONTRIBUTION,
)
from documents.criterion_b_evidence.program_validation import validate_academic_program_bundle
from documents.scoring.criterion_b_simulation_adapter import (
    aggregate_criterion_b_simulation_from_documents,
    score_primary_document_for_simulation,
)
from documents.scoring.document_evidence_points import effective_document_points
from kra_configuration.criterion_b_aggregation import deduplication_key_for_bundle
from kra_configuration.criterion_b_scoring import (
    aggregate_criterion_b_from_results,
    compute_criterion_b_indicator_points,
)
from tests.documents.test_criterion_b_program_evidence import _filled_bundle
from tests.documents.test_criterion_b_simulation_adapter import (
    _primary_doc,
    _scoring_ready_im_bundle,
    _settings,
    _verify_program_slots,
)


def _verify_im_checklist(bundle: dict) -> dict:
    material_type = bundle.get("materialType") or ""
    authorship = bundle.get("authorship") or "sole"
    slots = list(required_slots(material_type, authorship=authorship)) + [SLOT_PRIMARY_MATERIAL]
    for slot in slots:
        entry = (bundle.get("checklist") or {}).get(slot)
        if isinstance(entry, dict) and entry.get("documentId"):
            entry["status"] = SLOT_STATUS_VERIFIED
            entry["ocrHintOnly"] = False
    return bundle


def _link_slots(bundle: dict) -> dict:
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


def _ready_module(*, title: str, primary_hash: str, public_id: str) -> dict:
    bundle = build_initial_bundle(
        primary_document_id=public_id,
        primary_file_hash=primary_hash,
        indicator_id="kra1-b-module-sole",
        material_title=title,
    )
    bundle = _link_slots(bundle)
    bundle["completeSetDeclared"] = True
    bundle["specializationAligned"] = True
    return _verify_im_checklist(bundle)


def test_distinct_materials_same_annex_row_and_indicator_both_count():
    b1 = _ready_module(title="Calculus Module A", primary_hash="hash_a", public_id="doc_a")
    b2 = _ready_module(title="Calculus Module B", primary_hash="hash_b", public_id="doc_b")
    docs = [
        _primary_doc(bundle=b1, indicator_id="kra1-b-module-sole", public_id="doc_a"),
        _primary_doc(bundle=b2, indicator_id="kra1-b-module-sole", public_id="doc_b"),
    ]
    out = aggregate_criterion_b_simulation_from_documents(docs, settings=_settings())
    assert out["rawSumBeforeCap"] == 32.0
    assert out["cappedTotal"] == 30.0


def test_same_material_sole_and_co_author_keep_highest_only():
    shared_hash = "shared_material_hash"
    sole_bundle = _ready_module(title="Shared Module", primary_hash=shared_hash, public_id="doc_sole")
    co_bundle = build_initial_bundle(
        primary_document_id="doc_co",
        primary_file_hash=shared_hash,
        indicator_id="kra1-b-module-co",
        material_title="Shared Module",
    )
    co_bundle = _link_slots(co_bundle)
    co_bundle["completeSetDeclared"] = True
    co_bundle["specializationAligned"] = True
    co_bundle["contributionPercent"] = 50
    co_bundle = _verify_im_checklist(co_bundle)

    assert deduplication_key_for_bundle(sole_bundle) == deduplication_key_for_bundle(co_bundle)

    settings = _settings()
    sole_res = compute_criterion_b_indicator_points(
        "kra1-b-module-sole", evidence_verified=True, settings=settings
    )
    co_res = compute_criterion_b_indicator_points(
        "kra1-b-module-co", contribution_percent=50, evidence_verified=True, settings=settings
    )
    key = deduplication_key_for_bundle(sole_bundle)
    capped, raw = aggregate_criterion_b_from_results(
        [sole_res, co_res],
        settings,
        dedupe_keys=[key, key],
    )
    assert sole_res.points == 16.0
    assert co_res.points == 8.0
    assert raw == 16.0
    assert capped == 16.0


def test_duplicate_resubmission_same_indicator_same_hash_one_credit():
    settings = _settings()
    low = compute_criterion_b_indicator_points(
        "kra1-b-textbook-co",
        contribution_percent=40,
        evidence_verified=True,
        settings=settings,
    )
    high = compute_criterion_b_indicator_points(
        "kra1-b-textbook-co",
        contribution_percent=60,
        evidence_verified=True,
        settings=settings,
    )
    capped, raw = aggregate_criterion_b_from_results(
        [low, high],
        settings,
        dedupe_keys=["im:hash:same-edition", "im:hash:same-edition"],
    )
    assert raw == 18.0
    assert capped == 18.0


def test_program_mandatory_verified_optional_absent_ready_for_scoring():
    bundle = _filled_bundle(kind=PROGRAM_KIND_NEW)
    bundle = _verify_program_slots(bundle)
    validation = validate_academic_program_bundle(bundle)
    assert validation["validationStatus"] == "valid"
    assert validation["readyForScoring"] is True
    for slot in ("approved_program_outcomes", "curriculum_obe_mapping"):
        assert f"optional_{slot}_reviewer_required" not in validation["flags"]
    assert "rrpa_copc_applicability_undetermined" not in validation["flags"]


def test_program_conditional_new_requires_development_study():
    bundle = _filled_bundle(kind=PROGRAM_KIND_NEW)
    checklist = bundle["checklist"]
    for slot in ("feasibility_study", "benchmarking_report"):
        entry = checklist.get(slot)
        if isinstance(entry, dict):
            entry["documentId"] = None
            entry["status"] = "missing"
    validation = validate_academic_program_bundle(bundle)
    assert validation["validationStatus"] == "incomplete"
    assert "development_study_required" in validation["flags"]
    assert validation["readyForScoring"] is False


def test_legacy_points_do_not_bypass_bundle_gate():
    bundle = _link_slots(
        build_initial_bundle(
            primary_document_id="doc_p",
            primary_file_hash="h1",
            indicator_id="kra1-b-textbook-sole",
            material_title="Legacy Book",
        )
    )
    doc = _primary_doc(bundle=bundle, indicator_id="kra1-b-textbook-sole")
    res = score_primary_document_for_simulation(doc, settings=_settings())
    assert res is not None
    assert res.points is None
    assert (
        "evidence_not_verified" in res.reasons or "evidence_not_ready_for_scoring" in res.reasons
    )


def test_criterion_b_max_thirty_with_mixed_annex_rows():
    docs = [
        _primary_doc(
            bundle=_scoring_ready_im_bundle(indicator_id="kra1-b-textbook-sole"),
            indicator_id="kra1-b-textbook-sole",
            public_id="t1",
        ),
        _primary_doc(
            bundle=_scoring_ready_im_bundle(indicator_id="kra1-b-module-sole"),
            indicator_id="kra1-b-module-sole",
            public_id="m1",
        ),
    ]
    b2 = _scoring_ready_im_bundle(indicator_id="kra1-b-module-sole")
    b2["checklist"]["primary_material"]["fileHash"] = "other_module_hash"
    b2["materialTitle"] = "Second Module"
    docs.append(
        _primary_doc(bundle=b2, indicator_id="kra1-b-module-sole", public_id="m2")
    )
    out = aggregate_criterion_b_simulation_from_documents(docs, settings=_settings())
    assert out["rawSumBeforeCap"] == 62.0
    assert out["cappedTotal"] == 30.0
