"""Applicable semester coverage and scoring eligibility (SET/SEF, read-only rules)."""

from __future__ import annotations

import re
from typing import Any

_SEM_ORDER = {
    "1st semester": 0,
    "first semester": 0,
    "2nd semester": 1,
    "second semester": 1,
}


def normalize_semester(semester: str | None) -> str:
    text = (semester or "").strip()
    if not text:
        return ""
    lower = text.lower()
    if lower in ("1st semester", "first semester", "1st sem", "1st sem."):
        return "1st Semester"
    if lower in ("2nd semester", "second semester", "2nd sem", "2nd sem."):
        return "2nd Semester"
    return text


def period_key(academic_year: str | None, semester: str | None) -> tuple[str, str] | None:
    year = (academic_year or "").strip()
    sem = normalize_semester(semester)
    if not year or not sem:
        return None
    return (year, sem)


def _year_start(academic_year: str) -> tuple[int, int]:
    """Sort key for academic year labels like 2023-2024."""
    match = re.match(r"(\d{4})\s*[-–]\s*(\d{4})", academic_year.strip())
    if match:
        return int(match.group(1)), int(match.group(2))
    match = re.search(r"(\d{4})", academic_year)
    if match:
        y = int(match.group(1))
        return y, y + 1
    return 0, 0


def period_sort_key(key: tuple[str, str]) -> tuple[int, int, int]:
    year, sem = key
    y0, y1 = _year_start(year)
    sem_i = _SEM_ORDER.get(sem.lower(), 99)
    return y0, y1, sem_i


def sort_period_keys(keys: list[tuple[str, str]]) -> list[tuple[str, str]]:
    return sorted(set(keys), key=period_sort_key)


def applicable_period_keys_from_coverage(
    coverage: dict | None,
    *,
    eligible_divisor: int,
    evidenced_keys: list[tuple[str, str]],
) -> frozenset[tuple[str, str]]:
    """Resolve which (year, semester) keys may count toward the circular divisor."""
    cov = coverage if isinstance(coverage, dict) else {}
    explicit = cov.get("applicablePeriods")
    if isinstance(explicit, list) and explicit:
        keys: list[tuple[str, str]] = []
        for item in explicit:
            if not isinstance(item, dict):
                continue
            pk = period_key(item.get("academicYear"), item.get("semester"))
            if pk:
                keys.append(pk)
        return frozenset(sort_period_keys(keys))

    unique = sort_period_keys(evidenced_keys)
    if eligible_divisor <= 0:
        return frozenset(unique)
    if len(unique) <= eligible_divisor:
        return frozenset(unique)

    policy = (cov.get("overflowPolicy") or "exclude_outside_published_window").strip()
    if policy == "exclude_oldest_chronological":
        return frozenset(unique[-eligible_divisor:])
    # Default: keep the chronologically latest N semesters (configurable policy documents this).
    return frozenset(unique[-eligible_divisor:])


def slot_status_label(
    *,
    has_record: bool,
    included_in_scoring: bool,
    exclusion_reason: str | None,
    review_bucket: str | None,
) -> str:
    if not has_record:
        return "Missing"
    reason = (exclusion_reason or "").lower()
    if "duplicate" in reason or "already recorded" in reason or "superseded" in reason:
        return "Duplicate"
    if "outside" in reason or "coverage" in reason:
        return "Outside coverage"
    if review_bucket == "incomplete" or "incomplete" in reason or "ambiguous" in reason:
        return "Needs correction"
    if review_bucket == "revision":
        return "Needs correction"
    if review_bucket == "rejected":
        return "Rejected"
    if review_bucket == "accepted" and included_in_scoring:
        return "Complete"
    if review_bucket == "accepted":
        return "Complete"
    if review_bucket == "pending":
        return "Pending review"
    return "Pending review"


DUPLICATE_MESSAGE = "This semester evaluation is already recorded"
OUTSIDE_COVERAGE_MESSAGE = "This evaluation is outside the required six-semester coverage"
