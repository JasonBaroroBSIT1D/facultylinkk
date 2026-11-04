"""KRA II — Research, Innovation and Creative Work (JC 01 s. 2026 catalog IDs)."""

from __future__ import annotations

from typing import Any

KRA2_ID = "kra2"
KRA2_MAX_POINTS = 100.0

CRITERION_A_ID = "kra2-a"
CRITERION_B_ID = "kra2-b"
CRITERION_C_ID = "kra2-c"

CRITERION_MAX_POINTS = 100.0

_KRA2_CRITERIA = frozenset({CRITERION_A_ID, CRITERION_B_ID, CRITERION_C_ID})


def is_kra2_criterion(criterion_id: str | None) -> bool:
    return (criterion_id or "").strip() in _KRA2_CRITERIA


def is_kra2_indicator(indicator_id: str | None) -> bool:
    iid = (indicator_id or "").strip()
    return iid.startswith("kra2-")


def criterion_id_for_indicator(indicator_id: str | None) -> str | None:
    iid = (indicator_id or "").strip()
    if not is_kra2_indicator(iid):
        return None
    parts = iid.split("-")
    if len(parts) >= 2:
        return f"{parts[0]}-{parts[1]}"
    return None


def indicator_metadata(indicator_id: str | None) -> dict[str, str | None] | None:
    """Catalog-derived metadata (registry + ID pattern fallback)."""
    ind = (indicator_id or "").strip()
    if not is_kra2_indicator(ind):
        return None
    from kra_configuration.kra2_indicator_registry import (
        contribution_mode,
        indicator_row,
        workflow_family,
    )

    row = indicator_row(ind)
    crit = criterion_id_for_indicator(ind)
    parts = ind.split("-")
    family = parts[2] if len(parts) >= 3 else "output"
    contrib = contribution_mode(ind)
    return {
        "criterionId": crit,
        "outputFamily": family,
        "contribution": contrib,
        "workflowFamily": workflow_family(ind),
        "catalogName": (row or {}).get("name"),
    }


def published_kra2_indicator_points(
    indicator_id: str,
    settings: dict[str, Any] | None,
    *,
    allow_annex_fallback: bool = True,
) -> float | None:
    """Resolve per-accomplishment base points from published Admin configuration (Annex A ``points``)."""
    base = published_kra2_indicator_base_points(
        indicator_id,
        settings,
        allow_annex_fallback=allow_annex_fallback,
    )
    if base is not None:
        return base
    if not allow_annex_fallback:
        return None
    return None


def published_kra2_indicator_base_points(
    indicator_id: str,
    settings: dict[str, Any] | None,
    *,
    allow_annex_fallback: bool = True,
) -> float | None:
    """Official base points per qualifying output (never the criterion maximum)."""
    ind = (indicator_id or "").strip()
    if not is_kra2_indicator(ind):
        return None
    if settings and isinstance(settings.get("indicators"), dict):
        entry = settings["indicators"].get(ind)
        if isinstance(entry, dict):
            raw = entry.get("points")
            if raw is not None:
                try:
                    return float(raw)
                except (TypeError, ValueError):
                    pass
        if not allow_annex_fallback:
            return None
    if allow_annex_fallback:
        from kra_configuration.kra2_indicator_registry import indicator_row

        row = indicator_row(ind)
        if row and row.get("points") is not None:
            try:
                return float(row["points"])
            except (TypeError, ValueError):
                pass
    return None


def published_kra2_criterion_max_points(
    criterion_id: str,
    settings: dict[str, Any] | None = None,
    *,
    allow_annex_fallback: bool = True,
) -> float | None:
    from kra_configuration.published_limits import published_criterion_max_points

    val = published_criterion_max_points(criterion_id, settings)
    if val is not None:
        return val
    if allow_annex_fallback and (criterion_id or "").strip() in _KRA2_CRITERIA:
        return CRITERION_MAX_POINTS
    return None
