"""Teaching evaluation serializer helpers (no database)."""

from __future__ import annotations

from documents.teaching_evaluation_serializers import apply_duplicate_period_flags


def test_duplicate_period_flags_mark_both_rows():
    rows = [
        {
            "evaluationType": "SET",
            "academicYear": "2024-2025",
            "semester": "1st Semester",
            "duplicatePeriodWarning": False,
        },
        {
            "evaluationType": "SET",
            "academicYear": "2024-2025",
            "semester": "1st Semester",
            "duplicatePeriodWarning": False,
        },
    ]
    apply_duplicate_period_flags(rows)
    assert rows[0]["duplicatePeriodWarning"] is True
    assert rows[1]["duplicatePeriodWarning"] is True


def test_duplicate_flags_ignore_incomplete_period():
    rows = [
        {"evaluationType": "SET", "academicYear": None, "semester": "1st Semester"},
        {"evaluationType": "SET", "academicYear": None, "semester": "1st Semester"},
    ]
    apply_duplicate_period_flags(rows)
    assert not rows[0].get("duplicatePeriodWarning")
    assert not rows[1].get("duplicatePeriodWarning")
