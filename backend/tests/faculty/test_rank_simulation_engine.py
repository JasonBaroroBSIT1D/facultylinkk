"""Rank simulation engine (unit tests, isolated from live facultylink data)."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

from faculty.rank_simulation_engine import (
    ELIGIBILITY_CANNOT_DETERMINE,
    ELIGIBILITY_ELIGIBLE,
    ELIGIBILITY_PROVISIONAL,
    ELIGIBILITY_UNDER_ASSESSMENT,
    compute_rank_simulation,
    resolve_rank_band,
)


def test_resolve_rank_band():
    assert resolve_rank_band("Instructor I") == "Instructor"
    assert resolve_rank_band("Assistant Professor III") == "Asst. Professor"


@patch("faculty.rank_simulation_engine.get_published_row", return_value=None)
@patch("faculty.rank_simulation_engine.teaching_effectiveness_payload")
@patch("faculty.rank_simulation_engine._doc_counts", return_value={"kra1": 0, "kra2": 0, "kra3": 0, "kra4": 0})
def test_no_documents_under_assessment(mock_counts, mock_te, _pub):
    mock_te.return_value = {
        "configurationComplete": False,
        "combinedProvisionalPoints": None,
        "combinedValidatedPoints": None,
        "criterionMaxPoints": 60,
        "set": {"coverageSummary": {"totalUploads": 0}, "missingPeriods": []},
        "sef": {"coverageSummary": {"totalUploads": 0}, "missingPeriods": []},
    }
    profile = SimpleNamespace(
        current_rank="Instructor I",
        target_rank="",
        kra_scores=[],
        id=1,
    )
    result = compute_rank_simulation(profile)
    assert result["eligibilityStatus"] == ELIGIBILITY_CANNOT_DETERMINE
    assert result["kraScores"][0]["statusLabel"] == "Not yet assessed"


@patch("faculty.rank_simulation_engine.get_published_row")
@patch("faculty.rank_simulation_engine.teaching_effectiveness_payload")
@patch("faculty.rank_simulation_engine._doc_counts", return_value={"kra1": 1, "kra2": 0, "kra3": 0, "kra4": 0})
def test_set_only_provisional_not_eligible(mock_counts, mock_te, mock_pub):
    mock_pub.return_value = SimpleNamespace(
        settings_json={
            "version": 1,
            "setSefScoring": {"officialFormulaVerified": True},
            "rankWeights": {"Instructor": {"kra1": 60, "kra2": 10, "kra3": 20, "kra4": 10}},
        },
        published_at=None,
        guideline_label="JC 2026",
    )
    mock_te.return_value = {
        "configurationComplete": True,
        "combinedProvisionalPoints": 18.5,
        "combinedValidatedPoints": None,
        "criterionMaxPoints": 60,
        "set": {
            "coverageSummary": {"totalUploads": 1, "includedPeriods": 1, "requiredPeriods": 6},
            "provisionalPoints": 18.5,
            "missingPeriods": ["5 semester(s) missing for divisor 6"],
        },
        "sef": {"coverageSummary": {"totalUploads": 0}, "missingPeriods": []},
    }
    profile = SimpleNamespace(
        current_rank="Instructor I",
        target_rank="Instructor II",
        kra_scores=[],
        id=1,
    )
    result = compute_rank_simulation(profile)
    assert result["eligibilityStatus"] == ELIGIBILITY_PROVISIONAL
    assert result["eligibilityStatus"] != "eligible_validated"
    assert any("SEF" in item["text"] or "kra" in item["category"] for item in result["missingRequirements"])


@patch("faculty.rank_simulation_engine.get_published_row")
@patch("faculty.rank_simulation_engine.teaching_effectiveness_payload")
@patch("faculty.rank_simulation_engine._doc_counts", return_value={"kra1": 1, "kra2": 0, "kra3": 0, "kra4": 0})
def test_sef_only_provisional(mock_counts, mock_te, mock_pub):
    mock_pub.return_value = SimpleNamespace(
        settings_json={
            "version": 1,
            "setSefScoring": {"officialFormulaVerified": True},
            "rankWeights": {"Instructor": {"kra1": 60, "kra2": 10, "kra3": 20, "kra4": 10}},
        },
        published_at=None,
        guideline_label="JC 2026",
    )
    mock_te.return_value = {
        "configurationComplete": True,
        "combinedProvisionalPoints": 12.0,
        "combinedValidatedPoints": None,
        "criterionMaxPoints": 60,
        "set": {"coverageSummary": {"totalUploads": 0}, "missingPeriods": []},
        "sef": {
            "coverageSummary": {"totalUploads": 1, "includedPeriods": 1, "requiredPeriods": 6},
            "provisionalPoints": 12.0,
            "missingPeriods": ["5 semester(s) missing for divisor 6"],
        },
    }
    profile = SimpleNamespace(
        current_rank="Instructor I",
        target_rank="Instructor II",
        kra_scores=[],
        id=1,
    )
    result = compute_rank_simulation(profile)
    assert result["eligibilityStatus"] == ELIGIBILITY_PROVISIONAL
    assert result["kraScores"][0]["provisionalPoints"] == 12.0
    assert result["kraScores"][0]["validatedPoints"] is None


@patch("faculty.rank_simulation_engine.get_published_row")
@patch("faculty.rank_simulation_engine.teaching_effectiveness_payload")
@patch("faculty.rank_simulation_engine._doc_counts", return_value={"kra1": 0, "kra2": 0, "kra3": 0, "kra4": 0})
def test_upload_alone_never_eligible_validated(mock_counts, mock_te, mock_pub):
    """High provisional TE must not mark eligible_validated without validated weighted score."""
    mock_pub.return_value = SimpleNamespace(
        settings_json={
            "version": 1,
            "setSefScoring": {"officialFormulaVerified": True},
            "rankWeights": {"Instructor": {"kra1": 60, "kra2": 10, "kra3": 20, "kra4": 10}},
            "rankUpgradeThresholds": {"Instructor II": {"requiredWeightedScore": 50}},
        },
        published_at=None,
        guideline_label="JC 2026",
    )
    mock_te.return_value = {
        "configurationComplete": True,
        "combinedProvisionalPoints": 55.0,
        "combinedValidatedPoints": None,
        "criterionMaxPoints": 60,
        "set": {
            "coverageSummary": {"totalUploads": 6, "includedPeriods": 6, "requiredPeriods": 6},
            "provisionalPoints": 55.0,
            "missingPeriods": [],
        },
        "sef": {"coverageSummary": {"totalUploads": 0}, "missingPeriods": []},
    }
    profile = SimpleNamespace(
        current_rank="Instructor I",
        target_rank="Instructor II",
        kra_scores=[],
        id=1,
    )
    result = compute_rank_simulation(profile)
    assert result["eligibilityStatus"] != ELIGIBILITY_ELIGIBLE
    assert result["progressPercent"] is not None
    assert result["weightedValidatedScore"] is None


@patch("faculty.rank_simulation_engine.get_published_row")
@patch("faculty.rank_simulation_engine.teaching_effectiveness_payload")
@patch("faculty.rank_simulation_engine._doc_counts", return_value={"kra1": 12, "kra2": 0, "kra3": 0, "kra4": 0})
def test_eligible_when_validated_meets_threshold(mock_counts, mock_te, mock_pub):
    mock_pub.return_value = SimpleNamespace(
        settings_json={
            "version": 1,
            "setSefScoring": {"officialFormulaVerified": True},
            "rankWeights": {"Instructor": {"kra1": 60, "kra2": 10, "kra3": 20, "kra4": 10}},
            "rankUpgradeThresholds": {"Instructor II": {"requiredWeightedScore": 30}},
        },
        published_at=None,
        guideline_label="JC 2026",
    )
    mock_te.return_value = {
        "configurationComplete": True,
        "combinedProvisionalPoints": 50.0,
        "combinedValidatedPoints": 55.0,
        "criterionMaxPoints": 60,
        "set": {
            "coverageSummary": {
                "totalUploads": 6,
                "includedPeriods": 6,
                "requiredPeriods": 6,
                "acceptedPeriods": 6,
            },
            "validatedPoints": 30.0,
            "missingPeriods": [],
        },
        "sef": {
            "coverageSummary": {
                "totalUploads": 6,
                "includedPeriods": 6,
                "requiredPeriods": 6,
                "acceptedPeriods": 6,
            },
            "validatedPoints": 25.0,
            "missingPeriods": [],
        },
    }
    profile = SimpleNamespace(
        current_rank="Instructor I",
        target_rank="Instructor II",
        kra_scores=[],
        id=1,
    )
    result = compute_rank_simulation(profile)
    assert result["eligibilityStatus"] == ELIGIBILITY_ELIGIBLE
    assert result["weightedValidatedScore"] is not None
    assert result["weightedValidatedScore"] >= 30


@patch("faculty.rank_simulation_engine.get_published_row", return_value=None)
@patch("faculty.rank_simulation_engine.teaching_effectiveness_payload")
@patch("faculty.rank_simulation_engine._doc_counts", return_value={"kra1": 0, "kra2": 0, "kra3": 0, "kra4": 0})
def test_missing_thresholds_under_assessment_not_percent(mock_counts, mock_te, _pub):
    mock_te.return_value = {
        "configurationComplete": True,
        "combinedProvisionalPoints": 20.0,
        "combinedValidatedPoints": None,
        "criterionMaxPoints": 60,
        "set": {"coverageSummary": {"totalUploads": 1}, "missingPeriods": []},
        "sef": {"coverageSummary": {"totalUploads": 0}, "missingPeriods": []},
    }
    profile = SimpleNamespace(
        current_rank="Instructor I",
        target_rank="Instructor II",
        kra_scores=[],
        id=1,
    )
    result = compute_rank_simulation(profile)
    assert result["eligibilityStatus"] in (ELIGIBILITY_CANNOT_DETERMINE, ELIGIBILITY_UNDER_ASSESSMENT)
    assert result["progressPercent"] is None
