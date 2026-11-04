"""KRA II reviewer scoring controls — all 54 indicators."""

from __future__ import annotations

import pytest

from documents.kra2_evidence.reviewer_assessment import (
    SCORING_METHOD_CONTRIBUTION,
    SCORING_METHOD_FIXED,
    SCORING_METHOD_VARIABLE,
    allows_reviewer_point_adjustment,
    apply_reviewer_accomplishment_decision,
    reviewer_scoring_controls,
    reviewer_scoring_method,
)
from documents.kra2_evidence.bundle import REVIEW_APPROVED, build_initial_bundle
from kra_configuration.kra2_indicator_registry import all_indicators, reviewer_adjustment_governing_rule

_CATALOG_IDS = [row["id"] for row in all_indicators()]


def _settings() -> dict:
    ind = {row["id"]: {"points": row.get("points"), "maxPoints": row.get("maxPoints")} for row in all_indicators()}
    return {
        "kras": {"kra2": {"maxPoints": 100}},
        "criteria": {"kra2-a": {"maxPoints": 100}, "kra2-b": {"maxPoints": 100}, "kra2-c": {"maxPoints": 100}},
        "indicators": ind,
    }


@pytest.mark.parametrize("indicator_id", _CATALOG_IDS)
def test_scoring_controls_payload(indicator_id: str):
    controls = reviewer_scoring_controls(indicator_id, settings=_settings())
    assert controls["scoringMethod"] in ("fixed", "contribution_based", "variable")
    assert controls["scoringMethodLabel"]
    assert controls["adjustmentGoverningRule"]
    assert controls["allowsPointAdjustment"] == allows_reviewer_point_adjustment(indicator_id=indicator_id)
    if reviewer_scoring_method(indicator_id) == SCORING_METHOD_CONTRIBUTION:
        assert controls["allowsContributionEdit"] is True


def test_fixed_indicator_rejects_partial_assessment():
    bundle = build_initial_bundle(
        primary_document_id="doc_x",
        primary_file_hash="h",
        indicator_id="kra2-a-book-sole",
    )
    bundle["submittedForReviewAt"] = "2025-01-01T00:00:00+00:00"
    with pytest.raises(ValueError, match="assessed_points_not_adjustable"):
        apply_reviewer_accomplishment_decision(
            bundle,
            review_status=REVIEW_APPROVED,
            reviewer_user_id=1,
            reviewer_display_name="R",
            remarks="Approved after verifying book evidence.",
            assessed_points=50.0,
            score_adjustment_reason="Trying partial on fixed indicator.",
            indicator_id="kra2-a-book-sole",
            settings=_settings(),
        )


def test_journal_allows_partial_with_reason():
    bundle = build_initial_bundle(
        primary_document_id="doc_j",
        primary_file_hash="h",
        indicator_id="kra2-a-journal-sole",
    )
    bundle["submittedForReviewAt"] = "2025-01-01T00:00:00+00:00"
    apply_reviewer_accomplishment_decision(
        bundle,
        review_status=REVIEW_APPROVED,
        reviewer_user_id=1,
        reviewer_display_name="R",
        remarks="Approved with reduced indexing tier.",
        assessed_points=30.0,
        score_adjustment_reason="Journal not in the indexed list per official matrix.",
        indicator_id="kra2-a-journal-sole",
        settings=_settings(),
    )
    assert bundle["reviewerAssessment"]["assessedPoints"] == 30.0
    assert bundle["reviewerAssessment"]["approvedPoints"] == 30.0


def test_translation_indicator_allows_partial_adjustment():
    assert allows_reviewer_point_adjustment(indicator_id="kra2-a-translation-sole") is True
    assert reviewer_scoring_method("kra2-a-translation-sole") == SCORING_METHOD_VARIABLE


def test_adjustment_rules_non_empty():
    for row in all_indicators():
        assert len(reviewer_adjustment_governing_rule(row["id"])) >= 20


def test_partial_adjustment_indicator_ids():
    partial = {iid for iid in _CATALOG_IDS if allows_reviewer_point_adjustment(indicator_id=iid)}
    assert "kra2-a-journal-sole" in partial
    assert "kra2-a-cite" in partial
    assert "kra2-b-comm-local" in partial
    assert "kra2-a-translation-sole" in partial
    assert "kra2-a-book-sole" not in partial


def test_contribution_co_authored_uses_contribution_method():
    assert reviewer_scoring_method("kra2-a-book-co") == SCORING_METHOD_CONTRIBUTION
    assert reviewer_scoring_method("kra2-a-journal-co") == SCORING_METHOD_CONTRIBUTION
