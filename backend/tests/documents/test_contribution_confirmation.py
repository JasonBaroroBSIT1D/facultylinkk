"""Annex C contribution confirmation (co-author Criterion B)."""

from __future__ import annotations

import pytest

from documents.criterion_b_evidence.contribution_confirmation import (
    STATUS_CONFIRMED,
    STATUS_LEGACY_GRANDFATHERED,
    STATUS_MISMATCH,
    STATUS_NOT_CONFIRMED,
    apply_contribution_confirmation,
    assert_can_save_reviewer_assessment,
    build_contribution_verification_view,
    effective_confirmation_status,
    suggest_contribution_percent_from_ocr,
)
from documents.criterion_b_evidence.reviewer_assessment import apply_reviewer_proposed_assessment
from kra_configuration.criterion_b_scoring import (
    compute_criterion_b_indicator_automated_estimate,
    published_base_points_for_annex_row,
    published_criterion_b_max,
)


@pytest.fixture(autouse=True)
def _published_config(monkeypatch):
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


def _settings() -> dict:
    return {
        "kras": {"kra1": {"maxPoints": 100}},
        "criteria": {"kra1-b": {"maxPoints": 30}},
        "indicators": {"kra1-b-textbook-sole": {"points": 30}},
    }


def _co_bundle(**overrides) -> dict:
    base = {
        "authorship": "co",
        "contributionPercent": 60,
        "checklist": {
            "annex_c_contribution": {"documentId": "doc_annex", "status": "verified"},
        },
    }
    base.update(overrides)
    return base


def test_matching_recorded_and_confirmed_allows_assessment():
    bundle = _co_bundle(contributionPercent=60)
    apply_contribution_confirmation(
        bundle,
        reviewer_user_id=1,
        reviewer_display_name="Reviewer",
        confirmed_percent=60,
    )
    assert bundle["contributionConfirmation"]["status"] == STATUS_CONFIRMED
    assert_can_save_reviewer_assessment(
        bundle,
        indicator_id="kra1-b-textbook-co",
        points=17.0,
        justification="Valid justification text here.",
    )
    est = compute_criterion_b_indicator_automated_estimate(
        "kra1-b-textbook-co",
        contribution_percent=60,
        settings=_settings(),
    )
    assert est == 18.0


def test_assessment_exceeding_cap_rejected():
    bundle = _co_bundle(contributionPercent=60)
    apply_contribution_confirmation(
        bundle,
        reviewer_user_id=1,
        reviewer_display_name="Reviewer",
        confirmed_percent=60,
    )
    with pytest.raises(ValueError) as exc:
        apply_reviewer_proposed_assessment(
            bundle,
            points=19,
            justification="Too high for 60 percent share.",
            reviewer_user_id=1,
            reviewer_display_name="R",
            indicator_id="kra1-b-textbook-co",
        )
    assert exc.value.args[0] == "reviewer_assessment_points_exceeds_published_max"


def test_missing_confirmation_blocks_new_assessment():
    bundle = _co_bundle()
    assert effective_confirmation_status(bundle, indicator_id="kra1-b-textbook-co") == STATUS_NOT_CONFIRMED
    with pytest.raises(ValueError) as exc:
        assert_can_save_reviewer_assessment(
            bundle,
            indicator_id="kra1-b-textbook-co",
            points=14,
            justification="Needs confirmation first.",
        )
    assert exc.value.args[0] == "contribution_confirmation_required"


def test_legacy_grandfather_allows_unchanged_assessment():
    bundle = _co_bundle()
    bundle["reviewerProposedAssessment"] = {
        "points": 14.0,
        "justification": "Historical assessment preserved.",
    }
    assert effective_confirmation_status(bundle, indicator_id="kra1-b-textbook-co") == STATUS_LEGACY_GRANDFATHERED
    assert_can_save_reviewer_assessment(
        bundle,
        indicator_id="kra1-b-textbook-co",
        points=14,
        justification="Historical assessment preserved.",
    )


def test_legacy_blocks_assessment_change_without_confirmation():
    bundle = _co_bundle()
    bundle["reviewerProposedAssessment"] = {
        "points": 14.0,
        "justification": "Historical assessment preserved.",
    }
    with pytest.raises(ValueError) as exc:
        assert_can_save_reviewer_assessment(
            bundle,
            indicator_id="kra1-b-textbook-co",
            points=15,
            justification="Trying to change without confirm.",
        )
    assert exc.value.args[0] == "contribution_confirmation_required_for_assessment_change"


def test_mismatch_on_confirm():
    bundle = _co_bundle(contributionPercent=50)
    with pytest.raises(ValueError):
        apply_contribution_confirmation(
            bundle,
            reviewer_user_id=1,
            reviewer_display_name="R",
            confirmed_percent=40,
            clarification_reason="",
        )


def test_ocr_suggestion_single_percent():
    ocr = suggest_contribution_percent_from_ocr(
        {"OCR excerpt": "Jason Baroro: 50% (sample)"},
        faculty_name="Jason Baroro",
    )
    assert ocr["ocrSuggestedPercent"] == 50.0
    assert ocr["ocrAmbiguous"] is False


def test_ocr_ambiguous_multiple_percentages():
    ocr = suggest_contribution_percent_from_ocr(
        {"OCR excerpt": "A: 40% and B: 60% on the same line"},
    )
    assert ocr["ocrSuggestedPercent"] is None
    assert ocr["ocrAmbiguous"] is True


def test_verified_annex_without_confirmation_flagged_in_view():
    view = build_contribution_verification_view(
        _co_bundle(),
        indicator_id="kra1-b-textbook-co",
    )
    assert view is not None
    assert view["confirmationStatus"] == STATUS_NOT_CONFIRMED
    assert view["requiresConfirmationBeforeNewAssessment"] is True


def test_criterion_b_cap_unchanged():
    assert published_criterion_b_max(_settings()) == 30.0
