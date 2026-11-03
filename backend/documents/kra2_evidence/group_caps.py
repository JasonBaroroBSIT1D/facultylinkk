"""Apply catalog group maximums (translation, citations, commercialization)."""

from __future__ import annotations

from typing import Any

from kra_configuration.kra2_indicator_registry import scoring_group, scoring_group_max


def apply_group_caps(
    points_by_accomplishment: dict[str, float],
    *,
    indicator_by_accomplishment: dict[str, str],
) -> dict[str, float]:
    """Reduce counted points when a scoring group total exceeds groupMax."""
    if not points_by_accomplishment:
        return points_by_accomplishment
    group_totals: dict[str, float] = {}
    group_max: dict[str, float] = {}
    for key, pts in points_by_accomplishment.items():
        ind = indicator_by_accomplishment.get(key, "")
        grp = scoring_group(ind)
        if not grp:
            continue
        gmax = scoring_group_max(ind)
        if gmax is None:
            continue
        group_totals[grp] = group_totals.get(grp, 0.0) + float(pts)
        group_max[grp] = float(gmax)

    adjusted = dict(points_by_accomplishment)
    for grp, total in group_totals.items():
        cap = group_max.get(grp)
        if cap is None or total <= cap:
            continue
        scale = cap / total if total > 0 else 0.0
        for key, pts in list(adjusted.items()):
            ind = indicator_by_accomplishment.get(key, "")
            if scoring_group(ind) == grp:
                adjusted[key] = round(float(pts) * scale, 2)
    return adjusted
