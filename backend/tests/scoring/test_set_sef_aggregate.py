"""Unit tests for SET/SEF aggregation (no database writes)."""

from __future__ import annotations

from types import SimpleNamespace

from documents.scoring.set_sef_aggregate import (
    _dedupe_periods,
    aggregate_indicator,
    parse_rating_percent,
)


def test_parse_rating_percent_fraction_and_percent():
    pct, scale = parse_rating_percent("95.00/100")
    assert pct == 95.0
    assert scale == 100.0
    pct2, _ = parse_rating_percent("88%")
    assert pct2 == 88.0


def test_dedupe_periods_prefers_accepted_over_pending():
    rows = [
        {
            "academicYear": "2024-2025",
            "semester": "1st Semester",
            "reviewBucket": "pending",
            "ratingPercent": 90.0,
            "fileName": "a.pdf",
        },
        {
            "academicYear": "2024-2025",
            "semester": "1st Semester",
            "reviewBucket": "accepted",
            "ratingPercent": 92.0,
            "fileName": "b.pdf",
        },
    ]
    chosen, excluded = _dedupe_periods(rows)
    assert len(chosen) == 1
    assert chosen[0]["ratingPercent"] == 92.0
    assert len(excluded) == 1


def test_aggregate_indicator_without_db(monkeypatch):
    monkeypatch.setattr(
        "documents.scoring.set_sef_aggregate.indicator_scoring_config",
        lambda _ind: {
            "complete": True,
            "maxPoints": 36.0,
            "multiplier": 36.0,
            "ratingScale": 100.0,
            "aggregationMethod": "circular_jc_2026_semester_average",
            "roundingRule": "two_decimals",
            "evaluationCoverage": {"standardRequiredSemesters": 1},
        },
    )
    monkeypatch.setattr(
        "documents.scoring.set_sef_aggregate.published_settings_root",
        lambda: {},
    )

    def doc(**kwargs):
        defaults = {
            "public_id": "doc_x",
            "file_name": "set.pdf",
            "indicator_id": "kra1-a-student",
            "status": "approved",
            "ocr_status": "completed",
            "submitted_at": None,
            "extracted_info": {
                "Academic year": "2024-2025",
                "Semester": "1st Semester",
                "Extracted rating": "90/100",
            },
        }
        defaults.update(kwargs)
        return SimpleNamespace(**defaults)

    docs = [
        doc(public_id="d1"),
        doc(
            public_id="d2",
            extracted_info={
                "Academic year": "2024-2025",
                "Semester": "1st Semester",
                "Extracted rating": "80/100",
            },
            status="pending_review",
        ),
    ]
    block = aggregate_indicator(docs, "kra1-a-student")
    assert block["provisionalPoints"] == 32.4
    assert block["validatedPoints"] == 32.4
    assert block["coverageSummary"]["includedPeriods"] == 1
    assert block["coverageSummary"]["requiredPeriods"] == 1
