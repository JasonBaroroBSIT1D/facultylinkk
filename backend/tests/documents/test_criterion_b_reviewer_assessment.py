"""Reviewer-proposed Criterion B assessment (no PostgreSQL)."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from documents.criterion_b_evidence.bundle import BUNDLE_EXTRACTED_KEY, build_initial_bundle
from documents.criterion_b_evidence.extracted_info_merge import merge_criterion_b_evidence_bundles
from documents.criterion_b_evidence.reviewer_assessment import (
    MIN_JUSTIFICATION_LEN,
    apply_reviewer_proposed_assessment,
)
from documents.criterion_b_evidence.scoring_context import build_criterion_b_scoring_context
from documents.criterion_b_evidence.service import CriterionBEvidenceError, reviewer_update_checklist_slot
from kra_configuration.criterion_b_scoring import (
    compute_criterion_b_indicator_points,
    published_base_points_for_annex_row,
)


def _criterion_b_settings() -> dict:
    return {
        "kras": {"kra1": {"maxPoints": 100}},
        "criteria": {"kra1-b": {"maxPoints": 30}},
        "indicators": {
            "kra1-b-module-sole": {"points": 16, "maxPoints": 16},
        },
    }


@pytest.fixture(autouse=True)
def _published_config_without_db(monkeypatch):
    settings = _criterion_b_settings()

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
    monkeypatch.setattr(
        "documents.criterion_b_evidence.scoring_context.published_criterion_b_max",
        lambda: 30,
    )
    monkeypatch.setattr(
        "documents.criterion_b_evidence.scoring_context.effective_document_points",
        lambda _doc: None,
    )

    def _compute(indicator_id, *, contribution_percent=None, evidence_verified=False):
        return compute_criterion_b_indicator_points(
            indicator_id,
            contribution_percent=contribution_percent,
            evidence_verified=evidence_verified,
            settings=settings,
        )

    monkeypatch.setattr(
        "documents.criterion_b_evidence.scoring_context.compute_criterion_b_indicator_points",
        _compute,
    )


def test_apply_reviewer_assessment_requires_justification():
    bundle = build_initial_bundle(
        primary_document_id="doc_p",
        primary_file_hash="h1",
        indicator_id="kra1-b-module-sole",
        material_title="Mod",
    )
    with pytest.raises(ValueError, match="justification"):
        apply_reviewer_proposed_assessment(
            bundle,
            points=5,
            justification="short",
            reviewer_user_id=1,
            reviewer_display_name="R",
            indicator_id="kra1-b-module-sole",
        )
    assert len("x" * MIN_JUSTIFICATION_LEN) >= MIN_JUSTIFICATION_LEN


def test_apply_reviewer_assessment_keeps_history():
    bundle = build_initial_bundle(
        primary_document_id="doc_p",
        primary_file_hash="h1",
        indicator_id="kra1-b-module-sole",
        material_title="Mod",
    )
    just = "First professional judgment based on evidence."
    apply_reviewer_proposed_assessment(
        bundle,
        points=4,
        justification=just,
        reviewer_user_id=1,
        reviewer_display_name="A",
        indicator_id="kra1-b-module-sole",
    )
    apply_reviewer_proposed_assessment(
        bundle,
        points=5,
        justification="Updated after verifying IMDC approval document.",
        reviewer_user_id=1,
        reviewer_display_name="A",
        indicator_id="kra1-b-module-sole",
    )
    record = bundle["reviewerProposedAssessment"]
    assert record["points"] == 5
    assert len(record["history"]) == 1
    assert record["history"][0]["points"] == 4


def test_merge_preserves_reviewer_assessment():
    old = {"reviewerProposedAssessment": {"points": 3, "justification": "Kept"}}
    new = {"materialTitle": "Updated title"}
    merged = merge_criterion_b_evidence_bundles(old, new)
    assert merged["reviewerProposedAssessment"]["points"] == 3
    assert merged["materialTitle"] == "Updated title"


def test_scoring_context_separates_estimate_and_proposed():
    bundle = build_initial_bundle(
        primary_document_id="doc_p",
        primary_file_hash="h1",
        indicator_id="kra1-b-module-sole",
        material_title="Mod",
    )
    apply_reviewer_proposed_assessment(
        bundle,
        points=6,
        justification="Professional assessment differs from OCR estimate.",
        reviewer_user_id=2,
        reviewer_display_name="Reviewer",
        indicator_id="kra1-b-module-sole",
    )
    doc = SimpleNamespace(
        indicator_id="kra1-b-module-sole",
        estimated_points=4.5,
        verified_points=0,
        ocr_status="completed",
        extracted_info={},
    )
    validation = {"readyForScoring": False, "validationStatus": "incomplete"}
    ctx = build_criterion_b_scoring_context(doc, bundle, validation)
    assert ctx["systemEstimatePoints"] == 4.5
    assert ctx["reviewerProposedAssessment"]["points"] == 6
    assert ctx["guidelineCompliantVerifiedPoints"] is None
    assert ctx["displayScore"]["label"] == "Reviewer Assessed"
    assert ctx["displayScore"]["points"] == 6


def test_scoring_context_automated_estimate_when_document_has_no_estimate():
    bundle = build_initial_bundle(
        primary_document_id="doc_p",
        primary_file_hash="h1",
        indicator_id="kra1-b-textbook-sole",
        material_title="Foundations of Applied Mathematics",
    )
    doc = SimpleNamespace(
        indicator_id="kra1-b-textbook-sole",
        estimated_points=None,
        verified_points=0,
        ocr_status="completed",
        extracted_info={},
        status="pending_review",
        deleted_at=None,
    )
    validation = {"readyForScoring": False, "validationStatus": "incomplete"}
    settings = _criterion_b_settings()
    settings["indicators"]["kra1-b-textbook-sole"] = {"points": 30, "maxPoints": 30}
    with patch("kra_configuration.criterion_b_scoring.published_settings_blob", return_value=settings):
        ctx = build_criterion_b_scoring_context(doc, bundle, validation)
    assert ctx["systemEstimatePoints"] == 30
    assert ctx["displayScore"]["label"] == "Estimated"
    assert ctx["displayScore"]["points"] == 30


def test_service_persists_specialization_without_slot():
    bundle = build_initial_bundle(
        primary_document_id="doc_p",
        primary_file_hash="h1",
        indicator_id="kra1-b-textbook-sole",
        material_title="Textbook",
    )
    doc = MagicMock()
    doc.public_id = "doc_p"
    doc.indicator_id = "kra1-b-textbook-sole"
    doc.faculty_profile_id = 1
    doc.extracted_info = {BUNDLE_EXTRACTED_KEY: bundle}
    reviewer = MagicMock(id=99, full_name="Rev User")
    with patch("documents.criterion_b_evidence.service.get_document", return_value=doc), patch(
        "documents.service.reviewer_can_access", return_value=True
    ), patch("documents.criterion_b_evidence.service.peer_document_summaries", return_value=[]), patch(
        "documents.criterion_b_evidence.service.persist_bundle"
    ) as mock_persist, patch("documents.criterion_b_evidence.service.db.session.commit"):
        _, validation = reviewer_update_checklist_slot(
            reviewer,
            "doc_p",
            slot_id=None,
            status=None,
            specialization_aligned=True,
        )
    saved = mock_persist.call_args[0][1]
    assert saved["specializationAligned"] is True
    assert validation["readyForScoring"] is False


def test_service_persists_remarks_without_slot():
    bundle = build_initial_bundle(
        primary_document_id="doc_p",
        primary_file_hash="h1",
        indicator_id="kra1-b-textbook-sole",
        material_title="Textbook",
    )
    doc = MagicMock()
    doc.public_id = "doc_p"
    doc.indicator_id = "kra1-b-textbook-sole"
    doc.faculty_profile_id = 1
    doc.extracted_info = {BUNDLE_EXTRACTED_KEY: bundle}
    reviewer = MagicMock(id=99, full_name="Rev User")
    with patch("documents.criterion_b_evidence.service.get_document", return_value=doc), patch(
        "documents.service.reviewer_can_access", return_value=True
    ), patch("documents.criterion_b_evidence.service.peer_document_summaries", return_value=[]), patch(
        "documents.criterion_b_evidence.service.persist_bundle"
    ) as mock_persist, patch("documents.criterion_b_evidence.service.db.session.commit"):
        reviewer_update_checklist_slot(
            reviewer,
            "doc_p",
            slot_id=None,
            status=None,
            remarks="Please update the syllabus header.",
        )
    saved = mock_persist.call_args[0][1]
    assert saved["reviewerRemarks"] == "Please update the syllabus header."


def test_service_blocks_assessment_when_not_ready():
    bundle = build_initial_bundle(
        primary_document_id="doc_p",
        primary_file_hash="h1",
        indicator_id="kra1-b-module-sole",
        material_title="Mod",
    )
    doc = MagicMock()
    doc.public_id = "doc_p"
    doc.indicator_id = "kra1-b-module-sole"
    doc.faculty_profile_id = 1
    doc.extracted_info = {BUNDLE_EXTRACTED_KEY: bundle}
    reviewer = MagicMock(id=99, full_name="Rev User")
    with patch("documents.criterion_b_evidence.service.get_document", return_value=doc), patch(
        "documents.service.reviewer_can_access", return_value=True
    ), patch("documents.criterion_b_evidence.service.peer_document_summaries", return_value=[]):
        with pytest.raises(CriterionBEvidenceError) as err:
            reviewer_update_checklist_slot(
                reviewer,
                "doc_p",
                slot_id=None,
                status=None,
                reviewer_assessment_points=5,
                reviewer_assessment_justification="Complete evidence set and strong pedagogical alignment.",
            )
    assert err.value.code == "reviewer_assessment_not_ready"


def test_service_persists_assessment_without_touching_verified_points():
    from tests.documents.test_criterion_b_simulation_adapter import _scoring_ready_im_bundle

    bundle = _scoring_ready_im_bundle(indicator_id="kra1-b-module-sole")
    bundle["checklist"]["primary_material"] = bundle["checklist"].get("primary_material") or {
        "documentId": "doc_p",
        "status": "verified",
    }
    doc = MagicMock()
    doc.public_id = "doc_p"
    doc.indicator_id = "kra1-b-module-sole"
    doc.faculty_profile_id = 1
    doc.estimated_points = 10
    doc.verified_points = 7.5
    doc.extracted_info = {BUNDLE_EXTRACTED_KEY: bundle}

    reviewer = MagicMock(id=99, full_name="Rev User")

    with patch("documents.criterion_b_evidence.service.get_document", return_value=doc), patch(
        "documents.service.reviewer_can_access", return_value=True
    ), patch("documents.criterion_b_evidence.service.peer_document_summaries", return_value=[]), patch(
        "documents.criterion_b_evidence.service.persist_bundle"
    ) as mock_persist, patch(
        "documents.criterion_b_evidence.service.db.session.commit"
    ), patch(
        "documents.criterion_b_evidence.service.db.session.add"
    ):
        reviewer_update_checklist_slot(
            reviewer,
            "doc_p",
            slot_id=None,
            status=None,
            reviewer_assessment_points=5,
            reviewer_assessment_justification="Complete evidence set and strong pedagogical alignment.",
        )

    assert doc.verified_points == 7.5
    saved = mock_persist.call_args[0][1]
    assert saved["reviewerProposedAssessment"]["points"] == 5


def test_service_forbidden_when_not_assigned():
    with patch("documents.criterion_b_evidence.service.get_document", return_value=MagicMock()), patch(
        "documents.service.reviewer_can_access", return_value=False
    ):
        with pytest.raises(CriterionBEvidenceError) as err:
            reviewer_update_checklist_slot(
                MagicMock(id=1),
                "doc_x",
                slot_id=None,
                status=None,
                reviewer_assessment_points=1,
                reviewer_assessment_justification="Enough text for justification field.",
            )
    assert err.value.code == "forbidden"
