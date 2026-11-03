"""KRA I Criterion B scoring helpers (JC 01 s. 2026 Annex A) — simulation foundation only."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from kra_configuration.criterion_b_annex import (
    CRITERION_B_ID,
    KRA1_ID,
    annex_row_for_indicator,
    indicator_requires_contribution_percent,
    is_criterion_b_indicator,
)
from kra_configuration.published_limits import (
    published_criterion_max_points,
    published_kra_max_points,
    published_settings_blob,
)

ROUNDING_PLACES = 2


@dataclass(frozen=True)
class CriterionBScoreResult:
    """Outcome of a single indicator scoring attempt (not persisted)."""

    indicator_id: str
    annex_row_id: str | None
    base_points: float | None
    contribution_percent: float | None
    raw_points: float | None
    points: float | None
    eligible: bool
    reasons: tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict[str, Any]:
        return {
            "indicatorId": self.indicator_id,
            "annexRowId": self.annex_row_id,
            "basePoints": self.base_points,
            "contributionPercent": self.contribution_percent,
            "rawPoints": self.raw_points,
            "points": self.points,
            "eligible": self.eligible,
            "reasons": list(self.reasons),
        }


def _round_score(value: float) -> float:
    return round(value + 1e-9, ROUNDING_PLACES)


def _indicator_entry(settings: dict[str, Any], indicator_id: str) -> dict[str, Any] | None:
    indicators = settings.get("indicators")
    if not isinstance(indicators, dict):
        return None
    entry = indicators.get(indicator_id)
    return entry if isinstance(entry, dict) else None


def published_base_points_for_annex_row(
    indicator_id: str,
    settings: dict[str, Any] | None = None,
) -> float | None:
    """
    Official base points for an indicator from published Admin config.

    Co-author indicator IDs resolve through the annex row's ``base_indicator_id``
    so the same official allocation is not duplicated in config.
    """
    row = annex_row_for_indicator(indicator_id)
    if not row:
        return None
    blob = settings if settings is not None else published_settings_blob()
    entry = _indicator_entry(blob, row.base_indicator_id)
    if not entry:
        return None
    for key in ("points", "maxPoints"):
        raw = entry.get(key)
        if raw is None:
            continue
        try:
            val = float(raw)
        except (TypeError, ValueError):
            continue
        if val >= 0:
            return val
    return None


def published_criterion_b_max(settings: dict[str, Any] | None = None) -> float:
    blob = settings if settings is not None else published_settings_blob()
    crit = published_criterion_max_points(CRITERION_B_ID, blob)
    if crit is not None and crit >= 0:
        return crit
    return 30.0


def published_kra1_max(settings: dict[str, Any] | None = None) -> float:
    blob = settings if settings is not None else published_settings_blob()
    return published_kra_max_points(KRA1_ID, blob)


def validate_contribution_percent(value: float | int | str | None) -> tuple[float | None, str | None]:
    """Return (percent, error_message). Rejects values outside 0–100."""
    if value is None:
        return None, "contribution_percent_required"
    try:
        pct = float(value)
    except (TypeError, ValueError):
        return None, "contribution_percent_invalid"
    if pct < 0 or pct > 100:
        return None, "contribution_percent_out_of_range"
    return pct, None


def compute_criterion_b_indicator_points(
    indicator_id: str,
    *,
    contribution_percent: float | int | str | None = None,
    evidence_verified: bool = False,
    settings: dict[str, Any] | None = None,
) -> CriterionBScoreResult:
    """
    Compute provisional points for one Criterion B indicator claim.

    Does not assume OCR or upload completeness equals verification.
    Returns ``points=None`` when evidence is not verified or required inputs are missing.
    """
    ind = (indicator_id or "").strip()
    if not is_criterion_b_indicator(ind):
        return CriterionBScoreResult(
            indicator_id=ind,
            annex_row_id=None,
            base_points=None,
            contribution_percent=None,
            raw_points=None,
            points=None,
            eligible=False,
            reasons=("unknown_criterion_b_indicator",),
        )

    row = annex_row_for_indicator(ind)
    annex_id = row.row_id if row else None
    base = published_base_points_for_annex_row(ind, settings)
    if base is None:
        return CriterionBScoreResult(
            indicator_id=ind,
            annex_row_id=annex_id,
            base_points=None,
            contribution_percent=None,
            raw_points=None,
            points=None,
            eligible=False,
            reasons=("published_base_points_unavailable",),
        )

    if not evidence_verified:
        return CriterionBScoreResult(
            indicator_id=ind,
            annex_row_id=annex_id,
            base_points=base,
            contribution_percent=None,
            raw_points=None,
            points=None,
            eligible=False,
            reasons=("evidence_not_verified",),
        )

    if indicator_requires_contribution_percent(ind):
        pct, err = validate_contribution_percent(contribution_percent)
        if err:
            return CriterionBScoreResult(
                indicator_id=ind,
                annex_row_id=annex_id,
                base_points=base,
                contribution_percent=None,
                raw_points=None,
                points=None,
                eligible=False,
                reasons=(err,),
            )
        raw = _round_score(base * (pct / 100.0))
        return CriterionBScoreResult(
            indicator_id=ind,
            annex_row_id=annex_id,
            base_points=base,
            contribution_percent=pct,
            raw_points=raw,
            points=raw,
            eligible=True,
            reasons=(),
        )

    raw = _round_score(base)
    return CriterionBScoreResult(
        indicator_id=ind,
        annex_row_id=annex_id,
        base_points=base,
        contribution_percent=100.0 if base > 0 else 0.0,
        raw_points=raw,
        points=raw,
        eligible=True,
        reasons=(),
    )


def compute_criterion_b_indicator_automated_estimate(
    indicator_id: str,
    *,
    contribution_percent: float | int | str | None = None,
    settings: dict[str, Any] | None = None,
) -> float | None:
    """
    Pre-verification estimate from published Admin config (same base/co math as official scoring).

    Does not imply evidence is verified or eligible for guideline-compliant points.
    """
    ind = (indicator_id or "").strip()
    if not is_criterion_b_indicator(ind):
        return None
    base = published_base_points_for_annex_row(ind, settings)
    if base is None:
        return None
    if indicator_requires_contribution_percent(ind):
        pct, err = validate_contribution_percent(contribution_percent)
        if err:
            return None
        return _round_score(base * (pct / 100.0))
    return _round_score(base)


def cap_criterion_b_total(
    component_points: list[float] | tuple[float, ...],
    settings: dict[str, Any] | None = None,
) -> tuple[float, float]:
    """
    Sum eligible criterion B points and apply the published criterion maximum (30).

    Returns ``(capped_total, raw_sum)``.
    """
    raw = _round_score(sum(float(p) for p in component_points if p is not None and p > 0))
    ceiling = published_criterion_b_max(settings)
    return min(raw, ceiling), raw


def cap_kra1_instruction_total(
    *,
    criterion_a_points: float | None = None,
    criterion_b_points: float | None = None,
    criterion_c_points: float | None = None,
    settings: dict[str, Any] | None = None,
) -> tuple[float, dict[str, float]]:
    """
    Apply per-criterion ceilings then cap combined KRA I at the published KRA maximum (100).

    Criterion A is passed through unchanged (SET/SEF engine owns A); this helper only
    enforces B/C caps and the overall KRA I ceiling for future integration.
    """
    blob = settings if settings is not None else published_settings_blob()
    crit_max = {
        "kra1-a": published_criterion_max_points("kra1-a", blob),
        "kra1-b": published_criterion_b_max(blob),
        "kra1-c": published_criterion_max_points("kra1-c", blob),
    }

    def _cap(value: float | None, cid: str) -> float:
        if value is None or value <= 0:
            return 0.0
        mx = crit_max.get(cid)
        if mx is not None and mx >= 0:
            return min(float(value), mx)
        return float(value)

    a = _cap(criterion_a_points, "kra1-a")
    b = _cap(criterion_b_points, "kra1-b")
    c = _cap(criterion_c_points, "kra1-c")
    raw = _round_score(a + b + c)
    kra_ceiling = published_kra1_max(blob)
    total = min(raw, kra_ceiling)
    return total, {"kra1-a": a, "kra1-b": b, "kra1-c": c, "rawSum": raw}


def best_points_per_indicator(
    results: list[CriterionBScoreResult],
) -> dict[str, float]:
    """Highest eligible score per indicator ID (for future bundle aggregation)."""
    best: dict[str, float] = {}
    for res in results:
        if not res.eligible or res.points is None:
            continue
        prev = best.get(res.indicator_id)
        if prev is None or res.points > prev:
            best[res.indicator_id] = res.points
    return best


def aggregate_criterion_b_from_results(
    results: list[CriterionBScoreResult],
    settings: dict[str, Any] | None = None,
    *,
    dedupe_keys: list[str] | None = None,
) -> tuple[float, float]:
    """
    Sum eligible Criterion B points and apply the published criterion maximum.

    When ``dedupe_keys`` is provided (one key per result), uses
    ``aggregate_eligible_points_by_output`` — distinct outputs may each earn credit;
    duplicate keys on the same Annex row keep the highest score only.

    When ``dedupe_keys`` is omitted, falls back to legacy **best-per-indicator-id**
    (deprecated for simulation; retained for older unit tests).
    """
    if dedupe_keys is not None:
        from kra_configuration.criterion_b_aggregation import aggregate_eligible_points_by_output

        return aggregate_eligible_points_by_output(
            results,
            dedupe_keys=dedupe_keys,
            settings=settings,
        )
    best = best_points_per_indicator(results)
    return cap_criterion_b_total(list(best.values()), settings)
