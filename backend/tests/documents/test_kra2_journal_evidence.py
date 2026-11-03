"""KRA II Phase 2 — journal article bundle, validation, scoring, workflow."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from documents.kra2_evidence.bundle import (
    REVIEW_APPROVED,
    SLOT_STATUS_VERIFIED,
    build_initial_bundle,
)
from documents.kra2_evidence.reviewer_assessment import apply_reviewer_accomplishment_decision
from documents.kra2_evidence.scoring import aggregate_kra2_a_from_documents, estimated_points_for_bundle
from documents.kra2_evidence.slots import required_slots
from documents.kra2_evidence.validation import validate_kra2_bundle
from documents.kra2_evidence.workflow_sync import linked_document_public_ids
from faculty.kra_document_aggregate import aggregate_criterion_documents_from_list


def _settings() -> dict:
    return {
        "criteria": {"kra2-a": {"maxPoints": 100}},
        "indicators": {
            "kra2-a-journal-sole": {"points": 50, "maxPoints": 50},
            "kra2-a-journal-co": {"points": 50, "maxPoints": 50},
            "kra2-a-book-sole": {"points": 100, "maxPoints": 100},
        },
    }


def _submit_bundle(bundle: dict, *, co: bool = False) -> dict:
    bundle["outputTitle"] = "Sample Article Title"
    bundle["outputVenue"] = "Journal of Examples"
    bundle["journalTitle"] = "Journal of Examples"
    bundle["authorsLine"] = "Faculty A; Student B"
    bundle["publicationDate"] = "2025-06-01"
    bundle["metadataConfirmed"] = {
        "outputTitle": True,
        "outputVenue": True,
        "journalTitle": True,
        "authorsLine": True,
        "publicationDate": True,
    }
    bundle["submittedForReviewAt"] = "2025-06-02T00:00:00+00:00"
    if co:
        bundle["declaredContributionPercent"] = 40.0
        bundle["metadataConfirmed"]["declaredContributionPercent"] = True
    return bundle


def test_journal_sole_required_slots():
    assert required_slots(indicator_id="kra2-a-journal-sole") == ("primary_output",)


def test_journal_co_requires_annex_d_slot():
    assert required_slots(indicator_id="kra2-a-journal-co") == (
        "primary_output",
        "contribution_certificate",
    )


def test_estimated_points_co_author_percent():
    bundle = build_initial_bundle(
        primary_document_id="doc1",
        primary_file_hash="h1",
        indicator_id="kra2-a-journal-co",
    )
    bundle["declaredContributionPercent"] = 50.0
    est = estimated_points_for_bundle(bundle, indicator_id="kra2-a-journal-co", settings=_settings())
    assert est == 25.0


def test_co_author_assessed_cannot_exceed_system_calculated():
    bundle = build_initial_bundle(
        primary_document_id="doc-co",
        primary_file_hash="h2",
        indicator_id="kra2-a-journal-co",
    )
    _submit_bundle(bundle, co=True)
    bundle["checklist"]["primary_output"]["status"] = SLOT_STATUS_VERIFIED
    with pytest.raises(ValueError, match="assessed_points_exceeds_eligible"):
        apply_reviewer_accomplishment_decision(
            bundle,
            review_status=REVIEW_APPROVED,
            reviewer_user_id=9,
            reviewer_display_name="Reviewer",
            remarks="Attempted to assign full sole-author points.",
            assessed_points=50.0,
            indicator_id="kra2-a-journal-co",
            settings=_settings(),
        )


def test_co_journal_rejects_assessed_above_system_calculated():
    bundle = build_initial_bundle(
        primary_document_id="doc-co2",
        primary_file_hash="h3",
        indicator_id="kra2-a-journal-co",
    )
    _submit_bundle(bundle, co=True)
    bundle["checklist"]["primary_output"]["status"] = SLOT_STATUS_VERIFIED
    with pytest.raises(ValueError, match="assessed_points_exceeds_eligible"):
        apply_reviewer_accomplishment_decision(
            bundle,
            review_status=REVIEW_APPROVED,
            reviewer_user_id=9,
            reviewer_display_name="Reviewer",
            remarks="Attempted to exceed contribution-based eligible points.",
            assessed_points=50.0,
            indicator_id="kra2-a-journal-co",
            settings=_settings(),
        )


def test_journal_sole_allows_partial_assessment_with_reason():
    bundle = build_initial_bundle(
        primary_document_id="doc-partial",
        primary_file_hash="h4",
        indicator_id="kra2-a-journal-sole",
    )
    _submit_bundle(bundle)
    bundle["checklist"]["primary_output"]["status"] = SLOT_STATUS_VERIFIED
    apply_reviewer_accomplishment_decision(
        bundle,
        review_status=REVIEW_APPROVED,
        reviewer_user_id=9,
        reviewer_display_name="Reviewer",
        remarks="Indexed source verified at reduced eligibility tier.",
        assessed_points=30.0,
        score_adjustment_reason="Publication meets criteria for partial credit under indexing rules.",
        indicator_id="kra2-a-journal-sole",
        settings=_settings(),
    )
    assert bundle["reviewerAssessment"]["assessedPoints"] == 30.0
    assert bundle["reviewerAssessment"]["systemCalculatedPoints"] == 50.0


def test_journal_sole_partial_requires_adjustment_reason():
    bundle = build_initial_bundle(
        primary_document_id="doc-partial2",
        primary_file_hash="h5",
        indicator_id="kra2-a-journal-sole",
    )
    _submit_bundle(bundle)
    bundle["checklist"]["primary_output"]["status"] = SLOT_STATUS_VERIFIED
    with pytest.raises(ValueError, match="score_adjustment_reason_required"):
        apply_reviewer_accomplishment_decision(
            bundle,
            review_status=REVIEW_APPROVED,
            reviewer_user_id=9,
            reviewer_display_name="Reviewer",
            remarks="Approved with reduced points but no adjustment reason.",
            assessed_points=30.0,
            indicator_id="kra2-a-journal-sole",
            settings=_settings(),
        )


def test_book_sole_disallows_partial_override():
    bundle = build_initial_bundle(
        primary_document_id="doc-book",
        primary_file_hash="h6",
        indicator_id="kra2-a-book-sole",
    )
    _submit_bundle(bundle)
    bundle["checklist"]["primary_output"]["status"] = SLOT_STATUS_VERIFIED
    with pytest.raises(ValueError, match="assessed_points_not_adjustable"):
        apply_reviewer_accomplishment_decision(
            bundle,
            review_status=REVIEW_APPROVED,
            reviewer_user_id=9,
            reviewer_display_name="Reviewer",
            remarks="Attempted unsupported partial score on fixed book indicator.",
            assessed_points=30.0,
            score_adjustment_reason="Should not apply to fixed book sole indicator.",
            indicator_id="kra2-a-book-sole",
            settings=_settings(),
        )


def test_assessed_cannot_exceed_indicator_max():
    bundle = build_initial_bundle(
        primary_document_id="doc-high",
        primary_file_hash="h7",
        indicator_id="kra2-a-journal-sole",
    )
    _submit_bundle(bundle)
    bundle["checklist"]["primary_output"]["status"] = SLOT_STATUS_VERIFIED
    with pytest.raises(ValueError, match="assessed_points_exceeds_indicator_max"):
        apply_reviewer_accomplishment_decision(
            bundle,
            review_status=REVIEW_APPROVED,
            reviewer_user_id=9,
            reviewer_display_name="Reviewer",
            remarks="Attempted score above official indicator maximum.",
            assessed_points=60.0,
            score_adjustment_reason="Invalid attempt to exceed published maximum.",
            indicator_id="kra2-a-journal-sole",
            settings=_settings(),
        )


def test_reviewer_scoring_method_labels():
    from documents.kra2_evidence.reviewer_assessment import (
        reviewer_scoring_method,
        reviewer_scoring_method_label,
    )
    from kra_configuration.kra2_indicator_registry import allows_reviewer_partial_points

    assert reviewer_scoring_method("kra2-a-journal-sole") == "variable"
    assert allows_reviewer_partial_points("kra2-a-journal-sole") is True
    assert reviewer_scoring_method_label("variable") == "Variable"
    assert reviewer_scoring_method("kra2-a-journal-co") == "contribution_based"
    assert reviewer_scoring_method_label("contribution_based") == "Contribution-Based"
    assert allows_reviewer_partial_points("kra2-a-book-sole") is False


def test_approval_sets_assessed_points_sole():
    bundle = build_initial_bundle(
        primary_document_id="doc1",
        primary_file_hash="h1",
        indicator_id="kra2-a-journal-sole",
    )
    _submit_bundle(bundle)
    bundle["checklist"]["primary_output"]["status"] = SLOT_STATUS_VERIFIED
    apply_reviewer_accomplishment_decision(
        bundle,
        review_status=REVIEW_APPROVED,
        reviewer_user_id=9,
        reviewer_display_name="Reviewer",
        remarks="Journal article verified against indexing policy.",
        indicator_id="kra2-a-journal-sole",
        settings=_settings(),
    )
    assert bundle["reviewerAssessment"]["assessedPoints"] == 50.0


def test_aggregate_caps_criterion_a():
    bundle = build_initial_bundle(
        primary_document_id="doc1",
        primary_file_hash="h1",
        indicator_id="kra2-a-journal-sole",
    )
    _submit_bundle(bundle)
    bundle["checklist"]["primary_output"]["status"] = SLOT_STATUS_VERIFIED
    apply_reviewer_accomplishment_decision(
        bundle,
        review_status=REVIEW_APPROVED,
        reviewer_user_id=9,
        reviewer_display_name="Reviewer",
        remarks="Verified sole-author journal article evidence.",
        indicator_id="kra2-a-journal-sole",
        settings=_settings(),
    )
    doc = SimpleNamespace(
        public_id="doc1",
        criterion_id="kra2-a",
        indicator_id="kra2-a-journal-sole",
        extracted_info={"kra2EvidenceBundle": bundle},
        deleted_at=None,
        status="approved",
    )
    block = aggregate_kra2_a_from_documents([doc], settings=_settings(), applicable_config_present=True)
    assert block["validatedPoints"] == 50.0
    assert block["maxPoints"] == 100.0


def test_rank_simulation_integration_kra2_a():
    bundle = build_initial_bundle(
        primary_document_id="doc1",
        primary_file_hash="h1",
        indicator_id="kra2-a-journal-sole",
    )
    _submit_bundle(bundle)
    bundle["checklist"]["primary_output"]["status"] = SLOT_STATUS_VERIFIED
    apply_reviewer_accomplishment_decision(
        bundle,
        review_status=REVIEW_APPROVED,
        reviewer_user_id=9,
        reviewer_display_name="Reviewer",
        remarks="Verified sole-author journal article evidence.",
        indicator_id="kra2-a-journal-sole",
        settings=_settings(),
    )
    doc = SimpleNamespace(
        public_id="doc1",
        criterion_id="kra2-a",
        indicator_id="kra2-a-journal-sole",
        extracted_info={"kra2EvidenceBundle": bundle},
        deleted_at=None,
        status="approved",
    )
    block = aggregate_criterion_documents_from_list(
        [doc],
        kra_key="kra2",
        criterion_id="kra2-a",
        settings=_settings(),
    )
    assert block.get("simulationAdapterEnabled") is True
    assert block.get("validatedPoints") == 50.0


def test_linked_document_ids_includes_primary_and_supporting():
    bundle = build_initial_bundle(
        primary_document_id="doc_primary",
        primary_file_hash="h1",
        indicator_id="kra2-a-journal-co",
    )
    bundle["checklist"]["contribution_certificate"] = {
        "status": "present_unverified",
        "documentId": "doc_annex_d",
        "fileHash": "h2",
    }
    ids = linked_document_public_ids(bundle, "doc_primary")
    assert ids == {"doc_primary", "doc_annex_d"}


def test_validation_blocks_approval_without_submission():
    bundle = build_initial_bundle(
        primary_document_id="doc1",
        primary_file_hash="h1",
        indicator_id="kra2-a-journal-sole",
    )
    bundle["checklist"]["primary_output"]["status"] = SLOT_STATUS_VERIFIED
    v = validate_kra2_bundle(bundle, indicator_id="kra2-a-journal-sole")
    assert v["readyForReviewer"] is False
    assert "not_submitted" in v["flags"]
