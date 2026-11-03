"""Phase C1: Criterion C scoring, evidence validation, dedupe, and KRA aggregation."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from documents.criterion_c_evidence.bundle import (
    REVIEW_APPROVED,
    REVIEW_REJECTED,
    SLOT_STATUS_VERIFIED,
    apply_slot_link,
    build_initial_bundle,
)
from documents.criterion_c_evidence.checklist import required_slots
from documents.criterion_c_evidence.deduplication import assess_peer_duplicates
from documents.criterion_c_evidence.reviewer_assessment import apply_reviewer_accomplishment_decision
from documents.criterion_c_evidence.scoring import (
    aggregate_criterion_c_from_documents,
    score_accomplishment_document,
)
from documents.criterion_c_evidence.validation import validate_criterion_c_bundle
from faculty.kra_document_aggregate import aggregate_criterion_documents_from_list
from kra_configuration.criterion_c_annex import ANNEX_A_DEFAULT_POINTS, published_points_for_indicator


def _settings() -> dict:
    return {"criteria": {"kra1-c": {"maxPoints": 10}}, "indicators": {}}


def _doc(
    *,
    public_id: str,
    indicator_id: str,
    bundle: dict | None = None,
    estimated_points: float | None = None,
    verified_points: float | None = None,
    status: str = "approved",
):
    info = {}
    if bundle is not None:
        info["criterionCEvidenceBundle"] = bundle
    return SimpleNamespace(
        public_id=public_id,
        criterion_id="kra1-c",
        indicator_id=indicator_id,
        extracted_info=info,
        deleted_at=None,
        status=status,
        estimated_points=estimated_points,
        verified_points=verified_points,
        reviewer_score=None,
        ocr_status="completed",
    )


def _filled_mentorship_bundle() -> dict:
    bundle = build_initial_bundle(
        primary_document_id="doc_primary",
        primary_file_hash="hash1",
        indicator_id="kra1-c-mentor",
        project_title="National Research Competition",
    )
    bundle["mentorship"]["competitionName"] = "National Research Competition"
    for slot in required_slots(service_category="mentorship"):
        bundle = apply_slot_link(
            bundle,
            slot_id=slot,
            supporting_document_id=f"sup_{slot}",
            supporting_file_hash=f"h_{slot}",
        )
        bundle["checklist"][slot]["status"] = SLOT_STATUS_VERIFIED
    apply_reviewer_accomplishment_decision(
        bundle,
        review_status=REVIEW_APPROVED,
        reviewer_user_id=1,
        reviewer_display_name="Reviewer",
        remarks="Mentorship evidence verified in full.",
        indicator_id="kra1-c-mentor",
    )
    return bundle


def _filled_research_bundle(indicator_id: str) -> dict:
    bundle = build_initial_bundle(
        primary_document_id="doc_primary",
        primary_file_hash="hash1",
        indicator_id=indicator_id,
        project_title="Sample Thesis",
    )
    bundle["studentNames"] = "Student A"
    bundle["completionDate"] = "2025-05-01"
    for slot in required_slots(service_category="research"):
        bundle = apply_slot_link(
            bundle,
            slot_id=slot,
            supporting_document_id=f"sup_{slot}",
            supporting_file_hash=f"h_{slot}",
        )
        bundle["checklist"][slot]["status"] = SLOT_STATUS_VERIFIED
    apply_reviewer_accomplishment_decision(
        bundle,
        review_status=REVIEW_APPROVED,
        reviewer_user_id=1,
        reviewer_display_name="Reviewer",
        remarks="Verified complete evidence set.",
        indicator_id=indicator_id,
    )
    return bundle


@pytest.mark.parametrize(
    "indicator_id,expected",
    list(ANNEX_A_DEFAULT_POINTS.items()),
)
def test_official_point_values(indicator_id, expected):
    assert published_points_for_indicator(indicator_id, _settings()) == expected


def test_three_capstone_adviser_services_sum_nine():
    docs = [
        _doc(
            public_id=f"d{i}",
            indicator_id="kra1-c-adviser-sp",
            bundle=_filled_research_bundle("kra1-c-adviser-sp"),
        )
        for i in range(3)
    ]
    out = aggregate_criterion_c_from_documents(docs, settings=_settings())
    assert out["rawServiceSum"] == 9.0
    assert out["estimatedPoints"] == 9.0


def test_four_capstone_adviser_services_cap_ten():
    docs = [
        _doc(
            public_id=f"d{i}",
            indicator_id="kra1-c-adviser-sp",
            bundle=_filled_research_bundle("kra1-c-adviser-sp"),
        )
        for i in range(4)
    ]
    out = aggregate_criterion_c_from_documents(docs, settings=_settings())
    assert out["rawServiceSum"] == 12.0
    assert out["estimatedPoints"] == 10.0


def test_rejected_service_excluded():
    bundle = _filled_research_bundle("kra1-c-adviser-sp")
    apply_reviewer_accomplishment_decision(
        bundle,
        review_status=REVIEW_REJECTED,
        reviewer_user_id=1,
        reviewer_display_name="Reviewer",
        remarks="Incomplete defense documentation.",
        indicator_id="kra1-c-adviser-sp",
    )
    doc = _doc(public_id="d1", indicator_id="kra1-c-adviser-sp", bundle=bundle)
    row = score_accomplishment_document(doc, settings=_settings())
    assert row is not None
    assert not row.included
    out = aggregate_criterion_c_from_documents([doc], settings=_settings())
    assert out.get("estimatedPoints") is None or out["estimatedPoints"] == 0.0


def test_missing_evidence_not_ready_for_scoring():
    bundle = build_initial_bundle(
        primary_document_id="doc_primary",
        primary_file_hash="hash1",
        indicator_id="kra1-c-adviser-sp",
        project_title="Title",
    )
    validation = validate_criterion_c_bundle(bundle)
    assert validation["readyForScoring"] is False
    assert "missing_approval_sheet" in validation["flags"]


def test_duplicate_service_flag():
    bundle = build_initial_bundle(
        primary_document_id="doc_a",
        primary_file_hash="h",
        indicator_id="kra1-c-adviser-ut",
        project_title="Same Thesis",
    )
    bundle["studentNames"] = "S1"
    bundle["completionDate"] = "2024-01-01"
    peer = build_initial_bundle(
        primary_document_id="doc_b",
        primary_file_hash="h2",
        indicator_id="kra1-c-adviser-ut",
        project_title="Same Thesis",
    )
    peer["studentNames"] = "S1"
    peer["completionDate"] = "2024-01-01"
    dup, policy = assess_peer_duplicates(
        bundle,
        faculty_profile_id=99,
        peer_bundles=[("doc_b", peer)],
        self_public_id="doc_a",
    )
    assert "duplicate_service_suspected" in dup


def test_adviser_panel_same_thesis_policy_flag():
    adv = build_initial_bundle(
        primary_document_id="doc_a",
        primary_file_hash="h",
        indicator_id="kra1-c-adviser-ut",
        project_title="Shared Title",
    )
    adv["studentNames"] = "S1"
    adv["completionDate"] = "2024-06-01"
    panel = build_initial_bundle(
        primary_document_id="doc_b",
        primary_file_hash="h2",
        indicator_id="kra1-c-panel-ut",
        project_title="Shared Title",
    )
    panel["studentNames"] = "S1"
    panel["completionDate"] = "2024-06-01"
    _dup, policy = assess_peer_duplicates(
        adv,
        faculty_profile_id=1,
        peer_bundles=[("doc_b", panel)],
        self_public_id="doc_a",
    )
    assert "adviser_panel_same_thesis_review" in policy


def test_estimated_vs_assessed_points():
    bundle = _filled_research_bundle("kra1-c-adviser-ut")
    apply_reviewer_accomplishment_decision(
        bundle,
        review_status=REVIEW_APPROVED,
        reviewer_user_id=1,
        reviewer_display_name="R",
        remarks="Approved with partial credit.",
        assessed_points=4.0,
        indicator_id="kra1-c-adviser-ut",
    )
    doc = _doc(public_id="d1", indicator_id="kra1-c-adviser-ut", bundle=bundle)
    row = score_accomplishment_document(doc, settings=_settings())
    assert row.included
    assert row.counted_points == 4.0
    assert row.eligible_points == 5.0


def test_legacy_documents_without_bundle_best_per_indicator():
    docs = [
        _doc(public_id="l1", indicator_id="kra1-c-adviser-ut", estimated_points=5.0, verified_points=5.0),
        _doc(public_id="l2", indicator_id="kra1-c-adviser-ut", estimated_points=3.0, verified_points=3.0),
    ]
    out = aggregate_criterion_c_from_documents(docs, settings=_settings())
    assert out["scoringSource"] == "legacy_document_points"
    assert out["estimatedPoints"] == 5.0


def test_mentorship_three_points():
    doc = _doc(
        public_id="m1",
        indicator_id="kra1-c-mentor",
        bundle=_filled_mentorship_bundle(),
    )
    row = score_accomplishment_document(doc, settings=_settings())
    assert row.included
    assert row.counted_points == 3.0


def _pending_mentorship_bundle() -> dict:
    bundle = build_initial_bundle(
        primary_document_id="doc_primary",
        primary_file_hash="hash1",
        indicator_id="kra1-c-mentor",
        project_title="National Research Competition",
    )
    bundle["mentorship"]["competitionName"] = "National Research Competition"
    for slot in required_slots(service_category="mentorship"):
        bundle = apply_slot_link(
            bundle,
            slot_id=slot,
            supporting_document_id=f"sup_{slot}",
            supporting_file_hash=f"h_{slot}",
        )
    return bundle


def test_pending_mentorship_counts_in_estimated_not_validated():
    docs = [
        _doc(
            public_id="d_pending",
            indicator_id="kra1-c-mentor",
            bundle=_pending_mentorship_bundle(),
            status="pending_review",
        )
    ]
    out = aggregate_criterion_c_from_documents(docs, settings=_settings())
    assert out.get("estimatedPoints") == 3.0
    assert out.get("validatedPoints") == 0.0


def test_kra_aggregate_criterion_c_adapter_enabled(monkeypatch):
    import documents.scoring.criterion_c_simulation_adapter as c_adapter

    monkeypatch.setattr(c_adapter, "CRITERION_C_SIMULATION_ADAPTER_ENABLED", True)

    docs = [
        _doc(
            public_id="d1",
            indicator_id="kra1-c-mentor",
            bundle=_filled_mentorship_bundle(),
        )
    ]
    block = aggregate_criterion_documents_from_list(
        docs,
        kra_key="kra1",
        criterion_id="kra1-c",
        settings=_settings(),
    )
    assert block.get("simulationAdapterEnabled") is True
    assert block.get("estimatedPoints") == 3.0


def test_criterion_b_regression_untouched(monkeypatch):
    import documents.scoring.criterion_c_simulation_adapter as c_adapter

    monkeypatch.setattr(c_adapter, "CRITERION_C_SIMULATION_ADAPTER_ENABLED", True)
    docs = [
        SimpleNamespace(
            public_id="b1",
            criterion_id="kra1-b",
            indicator_id="kra1-b-module-sole",
            extracted_info={},
            deleted_at=None,
            status="approved",
            estimated_points=16.0,
            verified_points=16.0,
            reviewer_score=None,
            ocr_status="completed",
        )
    ]
    block = aggregate_criterion_documents_from_list(
        docs,
        kra_key="kra1",
        criterion_id="kra1-b",
        settings={"criteria": {"kra1-b": {"maxPoints": 30}}},
    )
    assert block["criterionId"] == "kra1-b"
