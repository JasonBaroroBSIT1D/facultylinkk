"""Canonical Criterion B current score → KRA aggregation (adapter flag on/off)."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from documents.criterion_b_evidence.bundle import build_initial_bundle
from documents.criterion_b_evidence.contribution_confirmation import apply_contribution_confirmation
from documents.criterion_b_evidence.reviewer_assessment import apply_reviewer_proposed_assessment
from documents.criterion_b_evidence.validation import validate_instructional_material_bundle
from documents.scoring.criterion_b_simulation_adapter import (
    CRITERION_B_SIMULATION_ADAPTER_ENABLED,
    aggregate_criterion_b_simulation_from_documents,
    score_primary_document_for_simulation,
)
from faculty.kra_document_aggregate import aggregate_criterion_documents_from_list
from kra_configuration.criterion_b_scoring import published_base_points_for_annex_row
from tests.documents.test_criterion_b_simulation_adapter import (
    _primary_doc,
    _scoring_ready_im_bundle,
    _settings,
)


@pytest.fixture(autouse=True)
def _published_config_without_db(monkeypatch):
    settings = _settings()

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
        "documents.criterion_b_evidence.scoring_context.published_base_points_for_annex_row",
        _base,
    )
    monkeypatch.setattr(
        "documents.criterion_b_evidence.current_score.published_base_points_for_annex_row",
        _base,
    )
    monkeypatch.setattr(
        "kra_configuration.criterion_b_scoring.published_settings_blob",
        lambda: settings,
    )


def _confirm_co_contribution(bundle: dict) -> None:
    apply_contribution_confirmation(
        bundle,
        reviewer_user_id=1,
        reviewer_display_name="Reviewer",
        confirmed_percent=bundle["contributionPercent"],
    )


def test_reviewer_assessment_becomes_simulation_points_when_ready(monkeypatch):
    bundle = _scoring_ready_im_bundle(indicator_id="kra1-b-textbook-co")
    bundle["contributionPercent"] = 50
    _confirm_co_contribution(bundle)
    apply_reviewer_proposed_assessment(
        bundle,
        points=14,
        justification="Co-author contribution and evidence quality support 14 points.",
        reviewer_user_id=1,
        reviewer_display_name="Reviewer",
        indicator_id="kra1-b-textbook-co",
    )
    validation = validate_instructional_material_bundle(bundle)
    assert validation["readyForScoring"] is True
    doc = _primary_doc(
        bundle=bundle,
        indicator_id="kra1-b-textbook-co",
        public_id="doc_textbook",
    )
    doc.status = "approved"
    res = score_primary_document_for_simulation(doc, settings=_settings())
    assert res is not None
    assert res.eligible is True
    assert res.points == pytest.approx(14.0)

    out = aggregate_criterion_b_simulation_from_documents([doc], settings=_settings())
    assert out["estimatedPoints"] == pytest.approx(14.0)


def test_adapter_disabled_exposes_preview_not_kra_total(monkeypatch):
    monkeypatch.setattr(
        "documents.scoring.criterion_b_simulation_adapter.CRITERION_B_SIMULATION_ADAPTER_ENABLED",
        False,
    )
    bundle = _scoring_ready_im_bundle(indicator_id="kra1-b-textbook-co")
    bundle["contributionPercent"] = 50
    _confirm_co_contribution(bundle)
    apply_reviewer_proposed_assessment(
        bundle,
        points=14,
        justification="Professional assessment after verified evidence.",
        reviewer_user_id=1,
        reviewer_display_name="Reviewer",
        indicator_id="kra1-b-textbook-co",
    )
    doc = _primary_doc(
        bundle=bundle,
        indicator_id="kra1-b-textbook-co",
        public_id="doc_textbook",
    )
    doc.status = "approved"
    doc.verified_points = 0
    block = aggregate_criterion_documents_from_list(
        [doc],
        kra_key="kra1",
        criterion_id="kra1-b",
        settings=_settings(),
    )
    assert block["simulationAdapterEnabled"] is False
    assert block["estimatedPoints"] is None
    assert block["accomplishmentPreviewPoints"] == pytest.approx(14.0)
    assert block["integrationState"] == "criterion_b_adapter_disabled"


def test_adapter_enabled_includes_reviewer_assessed_in_kra_block(monkeypatch):
    monkeypatch.setattr(
        "documents.scoring.criterion_b_simulation_adapter.CRITERION_B_SIMULATION_ADAPTER_ENABLED",
        True,
    )
    bundle = _scoring_ready_im_bundle(indicator_id="kra1-b-textbook-co")
    bundle["contributionPercent"] = 50
    _confirm_co_contribution(bundle)
    apply_reviewer_proposed_assessment(
        bundle,
        points=14,
        justification="Professional assessment after verified evidence.",
        reviewer_user_id=1,
        reviewer_display_name="Reviewer",
        indicator_id="kra1-b-textbook-co",
    )
    doc = _primary_doc(
        bundle=bundle,
        indicator_id="kra1-b-textbook-co",
        public_id="doc_textbook",
    )
    doc.status = "approved"
    block = aggregate_criterion_documents_from_list(
        [doc],
        kra_key="kra1",
        criterion_id="kra1-b",
        settings=_settings(),
    )
    assert block["simulationAdapterEnabled"] is True
    assert block["estimatedPoints"] == pytest.approx(14.0)
    assert block["scoringSource"] == "criterion_b_evidence_bundle"


def test_estimated_before_reviewer_when_ready_not_assessed():
    bundle = _scoring_ready_im_bundle(indicator_id="kra1-b-module-sole")
    doc = _primary_doc(
        bundle=bundle,
        indicator_id="kra1-b-module-sole",
        public_id="mod",
    )
    doc.status = "pending_review"
    res = score_primary_document_for_simulation(doc, settings=_settings())
    assert res.eligible is True
    assert res.points == pytest.approx(16.0)


def test_not_ready_estimate_does_not_aggregate():
    bundle = build_initial_bundle(
        primary_document_id="doc_p",
        primary_file_hash="h1",
        indicator_id="kra1-b-textbook-sole",
        material_title="Draft",
    )
    doc = SimpleNamespace(
        public_id="doc_p",
        criterion_id="kra1-b",
        kra_id="kra1",
        indicator_id="kra1-b-textbook-sole",
        extracted_info={"criterionBEvidenceBundle": bundle},
        deleted_at=None,
        status="pending_review",
        estimated_points=None,
        verified_points=0,
        reviewer_score=None,
        ocr_status="completed",
    )
    res = score_primary_document_for_simulation(doc, settings=_settings())
    assert res is not None
    assert res.eligible is False
    assert res.points is None
