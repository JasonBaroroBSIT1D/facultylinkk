"""
Isolated Criterion B adapter activation scenarios (no PostgreSQL writes).

Run with adapter ON via monkeypatch only:
  cd backend && python -m pytest tests/staging/test_criterion_b_activation_scenarios.py -q
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from documents.criterion_b_evidence.bundle import build_initial_bundle
from documents.criterion_b_evidence.reviewer_assessment import apply_reviewer_proposed_assessment
from documents.criterion_b_evidence.scoring_context import build_criterion_b_scoring_context
from documents.criterion_b_evidence.validation import validate_instructional_material_bundle
from documents.scoring.criterion_b_simulation_adapter import aggregate_criterion_b_simulation_from_documents
from faculty.kra_document_aggregate import aggregate_criterion_documents_from_list
from kra_configuration.criterion_b_scoring import published_base_points_for_annex_row
from tests.documents.test_criterion_b_simulation_adapter import (
    _link_all_im_supporting_slots,
    _primary_doc,
    _scoring_ready_im_bundle,
    _settings,
    _verify_im_checklist,
)


@pytest.fixture(autouse=True)
def _adapter_on(monkeypatch):
    monkeypatch.setattr(
        "documents.scoring.criterion_b_simulation_adapter.CRITERION_B_SIMULATION_ADAPTER_ENABLED",
        True,
    )


@pytest.fixture(autouse=True)
def _published_config(monkeypatch):
    settings = _settings()
    settings["indicators"].setdefault("kra1-b-textbook-sole", {"points": 30, "maxPoints": 30})

    def _base(indicator_id: str, settings_arg=None):
        return published_base_points_for_annex_row(
            indicator_id,
            settings if settings_arg is None else settings_arg,
        )

    monkeypatch.setattr(
        "documents.criterion_b_evidence.reviewer_assessment.published_base_points_for_annex_row",
        _base,
    )
    monkeypatch.setattr(
        "kra_configuration.criterion_b_scoring.published_settings_blob",
        lambda: settings,
    )


def test_jason_like_reviewer_14_not_guideline_15():
    bundle = _scoring_ready_im_bundle(indicator_id="kra1-b-textbook-co")
    bundle["contributionPercent"] = 50
    bundle["reviewerProposedAssessment"] = {
        "points": 14.0,
        "justification": "Verified co-author evidence supports fourteen points.",
    }
    doc = _primary_doc(bundle=bundle, indicator_id="kra1-b-textbook-co", public_id="jason_tb")
    doc.status = "approved"
    doc.estimated_points = None
    doc.verified_points = 0
    doc.reviewer_score = None
    validation = validate_instructional_material_bundle(bundle)
    ctx = build_criterion_b_scoring_context(doc, bundle, validation)
    assert ctx["displayScore"]["points"] == pytest.approx(14.0)
    assert ctx["displayScore"]["label"] == "Reviewer Assessed"
    assert ctx["guidelineCompliantVerifiedPoints"] == pytest.approx(15.0)
    assert ctx["systemEstimatePoints"] is not None
    assert ctx["reviewerProposedAssessment"]["points"] == pytest.approx(14.0)

    block = aggregate_criterion_documents_from_list(
        [doc],
        kra_key="kra1",
        criterion_id="kra1-b",
        settings=_settings(),
    )
    assert block["estimatedPoints"] == pytest.approx(14.0)
    assert block["scoringSource"] == "criterion_b_evidence_bundle"


def test_criterion_b_cap_30_two_textbooks():
    d1 = _primary_doc(
        bundle=_scoring_ready_im_bundle(indicator_id="kra1-b-textbook-sole"),
        indicator_id="kra1-b-textbook-sole",
        public_id="t1",
    )
    d2 = _primary_doc(
        bundle=_scoring_ready_im_bundle(indicator_id="kra1-b-textbook-sole"),
        indicator_id="kra1-b-textbook-sole",
        public_id="t2",
    )
    out = aggregate_criterion_b_simulation_from_documents([d1, d2], settings=_settings())
    assert out["cappedTotal"] == pytest.approx(30.0)


def test_supporting_not_counted_as_claim():
    primary = _primary_doc(
        bundle=_scoring_ready_im_bundle(indicator_id="kra1-b-module-sole"),
        indicator_id="kra1-b-module-sole",
        public_id="p1",
    )
    from documents.criterion_b_evidence.bundle import LINK_EXTRACTED_KEY

    supporting = SimpleNamespace(
        public_id="sup1",
        criterion_id="kra1-b",
        indicator_id="kra1-b-module-sole",
        extracted_info={
            LINK_EXTRACTED_KEY: {
                "role": "supporting",
                "primaryDocumentId": "p1",
                "evidenceSlot": "imdc_evaluation_approval",
            }
        },
        deleted_at=None,
        status="approved",
        verified_points=99.0,
        estimated_points=99.0,
        ocr_status="completed",
    )
    block = aggregate_criterion_documents_from_list(
        [primary, supporting],
        kra_key="kra1",
        criterion_id="kra1-b",
        settings=_settings(),
    )
    assert block["documentCount"] == 1
    assert block["estimatedPoints"] == pytest.approx(16.0)


def test_legacy_fallback_when_no_bundle_points():
    legacy = SimpleNamespace(
        public_id="legacy_b",
        criterion_id="kra1-b",
        kra_id="kra1",
        indicator_id="kra1-b-textbook-sole",
        extracted_info={},
        deleted_at=None,
        status="approved",
        verified_points=25.0,
        reviewer_score=None,
        estimated_points=25.0,
        ocr_status="completed",
    )
    block = aggregate_criterion_documents_from_list(
        [legacy],
        kra_key="kra1",
        criterion_id="kra1-b",
        settings=_settings(),
    )
    assert block["estimatedPoints"] == pytest.approx(25.0)
    assert block["scoringSource"] == "legacy_document_points"


def test_incomplete_no_aggregate_points():
    bundle = build_initial_bundle(
        primary_document_id="doc_p",
        primary_file_hash="h1",
        indicator_id="kra1-b-textbook-sole",
        material_title="Incomplete",
    )
    doc = _primary_doc(bundle=bundle, indicator_id="kra1-b-textbook-sole", public_id="inc")
    doc.verified_points = 0
    doc.estimated_points = None
    doc.reviewer_score = None
    block = aggregate_criterion_documents_from_list(
        [doc],
        kra_key="kra1",
        criterion_id="kra1-b",
        settings=_settings(),
    )
    assert block.get("estimatedPoints") is None


def test_ready_estimate_before_reviewer():
    bundle = _scoring_ready_im_bundle(indicator_id="kra1-b-module-sole")
    doc = _primary_doc(bundle=bundle, indicator_id="kra1-b-module-sole", public_id="est")
    doc.status = "pending_review"
    block = aggregate_criterion_documents_from_list(
        [doc],
        kra_key="kra1",
        criterion_id="kra1-b",
        settings=_settings(),
    )
    assert block["estimatedPoints"] == pytest.approx(16.0)


def test_unverified_slots_not_ready():
    bundle = _link_all_im_supporting_slots(
        build_initial_bundle(
            primary_document_id="doc_p",
            primary_file_hash="h1",
            indicator_id="kra1-b-module-sole",
            material_title="Unverified slots",
        )
    )
    bundle["specializationAligned"] = True
    doc = _primary_doc(bundle=bundle, indicator_id="kra1-b-module-sole", public_id="unv")
    doc.verified_points = 0
    doc.estimated_points = None
    doc.reviewer_score = None
    validation = validate_instructional_material_bundle(bundle)
    assert validation["readyForScoring"] is False
    block = aggregate_criterion_documents_from_list(
        [doc],
        kra_key="kra1",
        criterion_id="kra1-b",
        settings=_settings(),
    )
    assert block.get("estimatedPoints") is None
