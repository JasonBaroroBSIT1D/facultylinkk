"""KRA I Criterion C — Annex A point mapping (JC 01 s. 2026 §15, Annex A p. 77–78)."""

from __future__ import annotations

from typing import Any

CRITERION_C_ID = "kra1-c"
CRITERION_C_MAX_POINTS = 10.0

SERVICE_RESEARCH = "research"
SERVICE_MENTORSHIP = "mentorship"

ROLE_ADVISER = "adviser"
ROLE_PANEL = "panel"

RESEARCH_SP_CP = "sp_cp"
RESEARCH_UT = "ut"
RESEARCH_MT = "mt"
RESEARCH_DD = "dd"

# Official Annex A defaults (overridden by published Admin indicator config when present).
ANNEX_A_DEFAULT_POINTS: dict[str, float] = {
    "kra1-c-adviser-sp": 3.0,
    "kra1-c-panel-sp": 1.0,
    "kra1-c-adviser-ut": 5.0,
    "kra1-c-panel-ut": 1.0,
    "kra1-c-adviser-mt": 8.0,
    "kra1-c-panel-mt": 2.0,
    "kra1-c-adviser-dd": 10.0,
    "kra1-c-panel-dd": 2.0,
    "kra1-c-mentor": 3.0,
}

_INDICATOR_META: dict[str, dict[str, str | None]] = {
    "kra1-c-adviser-sp": {
        "serviceCategory": SERVICE_RESEARCH,
        "researchType": RESEARCH_SP_CP,
        "role": ROLE_ADVISER,
    },
    "kra1-c-panel-sp": {
        "serviceCategory": SERVICE_RESEARCH,
        "researchType": RESEARCH_SP_CP,
        "role": ROLE_PANEL,
    },
    "kra1-c-adviser-ut": {
        "serviceCategory": SERVICE_RESEARCH,
        "researchType": RESEARCH_UT,
        "role": ROLE_ADVISER,
    },
    "kra1-c-panel-ut": {
        "serviceCategory": SERVICE_RESEARCH,
        "researchType": RESEARCH_UT,
        "role": ROLE_PANEL,
    },
    "kra1-c-adviser-mt": {
        "serviceCategory": SERVICE_RESEARCH,
        "researchType": RESEARCH_MT,
        "role": ROLE_ADVISER,
    },
    "kra1-c-panel-mt": {
        "serviceCategory": SERVICE_RESEARCH,
        "researchType": RESEARCH_MT,
        "role": ROLE_PANEL,
    },
    "kra1-c-adviser-dd": {
        "serviceCategory": SERVICE_RESEARCH,
        "researchType": RESEARCH_DD,
        "role": ROLE_ADVISER,
    },
    "kra1-c-panel-dd": {
        "serviceCategory": SERVICE_RESEARCH,
        "researchType": RESEARCH_DD,
        "role": ROLE_PANEL,
    },
    "kra1-c-mentor": {
        "serviceCategory": SERVICE_MENTORSHIP,
        "researchType": None,
        "role": None,
    },
}


def is_criterion_c_indicator(indicator_id: str | None) -> bool:
    ind = (indicator_id or "").strip()
    return ind.startswith("kra1-c-")


def indicator_metadata(indicator_id: str) -> dict[str, str | None] | None:
    return _INDICATOR_META.get((indicator_id or "").strip())


def published_points_for_indicator(
    indicator_id: str,
    settings: dict[str, Any] | None = None,
    *,
    allow_annex_fallback: bool = True,
) -> float | None:
    ind = (indicator_id or "").strip()
    if not ind:
        return None
    if settings and isinstance(settings.get("indicators"), dict):
        entry = settings["indicators"].get(ind)
        if isinstance(entry, dict):
            for key in ("points", "maxPoints"):
                raw = entry.get(key)
                if raw is not None:
                    try:
                        return float(raw)
                    except (TypeError, ValueError):
                        pass
        if not allow_annex_fallback:
            return None
    if not allow_annex_fallback:
        return None
    default = ANNEX_A_DEFAULT_POINTS.get(ind)
    return float(default) if default is not None else None


def published_criterion_c_max_points(
    settings: dict[str, Any] | None = None,
    *,
    allow_annex_fallback: bool = True,
) -> float | None:
    """Criterion C maximum from published Admin criteria config."""
    from kra_configuration.published_limits import published_criterion_max_points

    val = published_criterion_max_points(CRITERION_C_ID, settings)
    if val is not None:
        return val
    if allow_annex_fallback:
        return CRITERION_C_MAX_POINTS
    return None
