"""DBM–CHED JC 01 s. 2026 SET/SEF circular sample and Section 10 (no database)."""

from __future__ import annotations

from types import SimpleNamespace

from documents.scoring.circular_formula import (
    indicator_points_from_overall_rating,
    overall_rating_from_semesters,
)
from documents.scoring.section10 import resolve_divisor
from documents.scoring.set_sef_aggregate import aggregate_indicator


def _verified_config(multiplier: float, max_points: float | None = None):
    max_points = max_points if max_points is not None else multiplier
    return {
        "complete": True,
        "maxPoints": max_points,
        "multiplier": multiplier,
        "ratingScale": 100.0,
        "aggregationMethod": "circular_jc_2026_semester_average",
        "roundingRule": "two_decimals",
        "evaluationCoverage": {"standardRequiredSemesters": 6},
    }


def _set_doc(public_id: str, ay: str, sem: str, rating: str, status: str = "approved"):
    return SimpleNamespace(
        public_id=public_id,
        file_name=f"{public_id}.pdf",
        indicator_id="kra1-a-student",
        status=status,
        ocr_status="completed",
        submitted_at=None,
        extracted_info={
            "Academic year": ay,
            "Semester": f"{sem} Semester" if sem.isdigit() else sem,
            "Extracted rating": rating,
            "Rating scale": "100",
        },
    )


def test_circular_set_sample_oetr_and_points():
    ratings = [95.0, 89.0, 88.0, 92.0, 94.0, 85.0]
    oetr = overall_rating_from_semesters(ratings, divisor=6)
    assert oetr == 90.5
    points = indicator_points_from_overall_rating(
        oetr, multiplier=36.0, max_points=36.0, rounding_rule="two_decimals"
    )
    assert points == 32.58


def test_circular_sef_sample_parallel():
    ratings = [96.0, 94.0, 91.0, 93.0, 95.0, 92.0]
    oefr = overall_rating_from_semesters(ratings, divisor=6)
    assert oefr == 93.5
    points = indicator_points_from_overall_rating(
        oefr, multiplier=24.0, max_points=24.0, rounding_rule="two_decimals"
    )
    assert points == 22.44


def test_set_six_semesters_aggregate(monkeypatch):
    monkeypatch.setattr(
        "documents.scoring.set_sef_aggregate.indicator_scoring_config",
        lambda _ind: _verified_config(36.0),
    )
    monkeypatch.setattr("documents.scoring.set_sef_aggregate.published_settings_root", lambda: {})
    docs = [
        _set_doc("d1", "2023-2024", "1", "95"),
        _set_doc("d2", "2023-2024", "2", "89"),
        _set_doc("d3", "2024-2025", "1", "88"),
        _set_doc("d4", "2024-2025", "2", "92"),
        _set_doc("d5", "2025-2026", "1", "94"),
        _set_doc("d6", "2025-2026", "2", "85"),
    ]
    block = aggregate_indicator(docs, "kra1-a-student")
    assert block["provisionalPoints"] == 32.58
    assert block["validatedPoints"] == 32.58
    assert block["averageRatingPercent"] == 90.5


def test_incomplete_five_semesters_no_official_points(monkeypatch):
    monkeypatch.setattr(
        "documents.scoring.set_sef_aggregate.indicator_scoring_config",
        lambda _ind: _verified_config(36.0),
    )
    monkeypatch.setattr("documents.scoring.set_sef_aggregate.published_settings_root", lambda: {})
    docs = [
        _set_doc("d1", "2023-2024", "1", "95"),
        _set_doc("d2", "2023-2024", "2", "89"),
        _set_doc("d3", "2024-2025", "1", "88"),
        _set_doc("d4", "2024-2025", "2", "92"),
        _set_doc("d5", "2025-2026", "1", "94"),
    ]
    block = aggregate_indicator(docs, "kra1-a-student")
    assert block["provisionalPoints"] is None
    assert block["scoringStatus"] == "incomplete"
    assert block["missingPeriods"]


def test_section10_study_leave_requires_eligible_count():
    coverage = {"standardRequiredSemesters": 6}
    elig = {"section10Code": "study_leave", "reviewerVerified": True}
    res = resolve_divisor(coverage, elig)
    assert res.eligible_divisor is None
    assert res.incomplete_reason


def test_section10_verified_reduced_divisor():
    coverage = {"standardRequiredSemesters": 6}
    elig = {
        "section10Code": "study_leave",
        "reviewerVerified": True,
        "eligibleSemesterCount": 4,
    }
    res = resolve_divisor(coverage, elig)
    assert res.eligible_divisor == 4
    ratings = [90.0, 88.0, 92.0, 91.0]
    oetr = overall_rating_from_semesters(ratings, divisor=4)
    assert oetr == 90.25
