"""DBM–CHED JC 01 s. 2026 SET/SEF point formulas (config-driven maxima)."""

from __future__ import annotations

from documents.scoring.section10 import CIRCULAR_AGGREGATION_METHOD


def apply_rounding(value: float, rule: str | None) -> float:
    if rule in (None, "", "two_decimals", "round_half_up_2"):
        return round(value + 1e-9, 2)
    if rule == "four_decimals":
        return round(value + 1e-9, 4)
    return round(value + 1e-9, 2)


def overall_rating_from_semesters(
    semester_ratings: list[float],
    *,
    divisor: int,
) -> float | None:
    """OSETR/OSEFR = sum of semester ratings ÷ applicable divisor (circular sample uses six)."""
    if divisor <= 0 or not semester_ratings:
        return None
    if len(semester_ratings) < divisor:
        return None
    total = sum(semester_ratings[:divisor])
    return round(total / divisor, 4)


def provisional_average(semester_ratings: list[float]) -> float | None:
    if not semester_ratings:
        return None
    return round(sum(semester_ratings) / len(semester_ratings), 4)


def indicator_points_from_overall_rating(
    overall_rating: float,
    *,
    multiplier: float,
    max_points: float,
    rounding_rule: str | None,
) -> float:
    raw = (overall_rating / 100.0) * multiplier
    capped = min(raw, max_points)
    return apply_rounding(capped, rounding_rule)


def is_supported_aggregation(method: str | None) -> bool:
    if not method:
        return False
    return method == CIRCULAR_AGGREGATION_METHOD
