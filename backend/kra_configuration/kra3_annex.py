"""KRA III — Extension Services (JC 01 s. 2026 catalog IDs)."""

from __future__ import annotations

from typing import Any

KRA3_ID = "kra3"
KRA3_MAX_POINTS = 100.0

CRITERION_A_ID = "kra3-a"
CRITERION_B_ID = "kra3-b"
CRITERION_C_ID = "kra3-c"
CRITERION_D_ID = "kra3-d"

CRITERION_A_MAX = 30.0
CRITERION_B_MAX = 50.0
CRITERION_C_MAX = 20.0
CRITERION_D_BONUS_MAX = 20.0

_KRA3_CRITERIA = frozenset({CRITERION_A_ID, CRITERION_B_ID, CRITERION_C_ID, CRITERION_D_ID})
_KRA3_REGULAR_CRITERIA = frozenset({CRITERION_A_ID, CRITERION_B_ID, CRITERION_C_ID})


def is_kra3_criterion(criterion_id: str | None) -> bool:
    return (criterion_id or "").strip() in _KRA3_CRITERIA


def is_kra3_regular_criterion(criterion_id: str | None) -> bool:
    return (criterion_id or "").strip() in _KRA3_REGULAR_CRITERIA


def is_kra3_bonus_criterion(criterion_id: str | None) -> bool:
    return (criterion_id or "").strip() == CRITERION_D_ID


def is_kra3_indicator(indicator_id: str | None) -> bool:
    iid = (indicator_id or "").strip()
    return iid.startswith("kra3-")


def criterion_id_for_indicator(indicator_id: str | None) -> str | None:
    iid = (indicator_id or "").strip()
    if not is_kra3_indicator(iid):
        return None
    parts = iid.split("-")
    if len(parts) >= 2:
        return f"{parts[0]}-{parts[1]}"
    return None


def indicator_metadata(indicator_id: str | None) -> dict[str, str | None] | None:
    ind = (indicator_id or "").strip()
    if not is_kra3_indicator(ind):
        return None
    from kra_configuration.kra3_indicator_registry import (
        contribution_mode,
        indicator_row,
        workflow_family,
    )

    row = indicator_row(ind)
    crit = criterion_id_for_indicator(ind)
    parts = ind.split("-")
    family = parts[2] if len(parts) >= 3 else "service"
    contrib = contribution_mode(ind)
    return {
        "criterionId": crit,
        "outputFamily": family,
        "contribution": contrib,
        "workflowFamily": workflow_family(ind),
        "catalogName": (row or {}).get("name"),
    }


def published_kra3_indicator_points(
    indicator_id: str,
    settings: dict[str, Any] | None,
    *,
    allow_annex_fallback: bool = True,
) -> float | None:
    return published_kra3_indicator_base_points(
        indicator_id,
        settings,
        allow_annex_fallback=allow_annex_fallback,
    )


def published_kra3_indicator_base_points(
    indicator_id: str,
    settings: dict[str, Any] | None,
    *,
    allow_annex_fallback: bool = True,
) -> float | None:
    ind = (indicator_id or "").strip()
    if not is_kra3_indicator(ind):
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
    from kra_configuration.kra3_indicator_registry import DESIGNATION_POINTS_UNVERIFIED, indicator_row

    row = indicator_row(ind)
    if not row:
        return None
    if ind.startswith("kra3-d-") and DESIGNATION_POINTS_UNVERIFIED:
        return None
    if row.get("formulaRating"):
        return None
    pts = row.get("points")
    try:
        return float(pts) if pts is not None else None
    except (TypeError, ValueError):
        return None


def published_kra3_criterion_max_points(
    criterion_id: str,
    settings: dict[str, Any] | None,
    *,
    allow_annex_fallback: bool = True,
) -> float | None:
    cid = (criterion_id or "").strip()
    if settings and isinstance(settings.get("criteria"), dict):
        entry = settings["criteria"].get(cid)
        if isinstance(entry, dict) and entry.get("maxPoints") is not None:
            try:
                return float(entry["maxPoints"])
            except (TypeError, ValueError):
                pass
    if not allow_annex_fallback:
        return None
    defaults = {
        CRITERION_A_ID: CRITERION_A_MAX,
        CRITERION_B_ID: CRITERION_B_MAX,
        CRITERION_C_ID: CRITERION_C_MAX,
        CRITERION_D_ID: CRITERION_D_BONUS_MAX,
    }
    return defaults.get(cid)
