"""Publish-time validation extensions (Phase C5)."""

from __future__ import annotations

from typing import Any

from kra_configuration.criterion_c_annex import CRITERION_C_ID, is_criterion_c_indicator

CRITERION_C_INDICATOR_IDS = tuple(
    k for k in (
        "kra1-c-adviser-sp",
        "kra1-c-panel-sp",
        "kra1-c-adviser-ut",
        "kra1-c-panel-ut",
        "kra1-c-adviser-mt",
        "kra1-c-panel-mt",
        "kra1-c-adviser-dd",
        "kra1-c-panel-dd",
        "kra1-c-mentor",
    )
)


def _nonnegative_number(raw: Any) -> float | None:
    if raw is None:
        return None
    try:
        val = float(raw)
    except (TypeError, ValueError):
        return None
    if val < 0:
        return None
    return val


def _criterion_c_in_scope(settings: dict[str, Any]) -> bool:
    criteria = settings.get("criteria") if isinstance(settings.get("criteria"), dict) else {}
    if isinstance(criteria.get(CRITERION_C_ID), dict):
        return True
    indicators = settings.get("indicators") if isinstance(settings.get("indicators"), dict) else {}
    return any(str(k).startswith("kra1-c-") for k in indicators)


def validate_scoring_integrity(settings: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    """
    Additional publish checks beyond SET/SEF verification.

    Returns (checks, error_codes).
    """
    checks: list[dict[str, Any]] = []
    errors: list[str] = []

    indicators = settings.get("indicators") if isinstance(settings.get("indicators"), dict) else {}
    criteria = settings.get("criteria") if isinstance(settings.get("criteria"), dict) else {}

    for ind_id, entry in indicators.items():
        if not isinstance(entry, dict):
            continue
        for key in ("points", "maxPoints", "multiplier"):
            raw = entry.get(key)
            if raw is None:
                continue
            val = _nonnegative_number(raw)
            if val is None:
                checks.append(
                    {
                        "id": f"indicator_{ind_id}_{key}",
                        "ok": False,
                        "message": f"Indicator {ind_id}: {key} must be a non-negative number.",
                    }
                )
                if "indicator_values_invalid" not in errors:
                    errors.append("indicator_values_invalid")

    if _criterion_c_in_scope(settings):
        crit_c = criteria.get(CRITERION_C_ID) if isinstance(criteria.get(CRITERION_C_ID), dict) else {}
        cmax = _nonnegative_number(crit_c.get("maxPoints"))
        if cmax is None:
            checks.append(
                {
                    "id": "criterion_c_max",
                    "ok": False,
                    "message": "Criterion C maximum points must be configured before publishing.",
                }
            )
            errors.append("criterion_c_max_missing")
        else:
            checks.append(
                {
                    "id": "criterion_c_max",
                    "ok": True,
                    "message": f"Criterion C maximum configured ({cmax:g} points).",
                }
            )

        missing_c = []
        for ind_id in CRITERION_C_INDICATOR_IDS:
            entry = indicators.get(ind_id)
            if not isinstance(entry, dict):
                missing_c.append(ind_id)
                continue
            pts = _nonnegative_number(entry.get("points"))
            if pts is None and _nonnegative_number(entry.get("maxPoints")) is None:
                missing_c.append(ind_id)

        if missing_c:
            checks.append(
                {
                    "id": "criterion_c_indicators",
                    "ok": False,
                    "message": "Criterion C indicators missing point values: " + ", ".join(missing_c[:5])
                    + ("…" if len(missing_c) > 5 else ""),
                }
            )
            errors.append("criterion_c_indicators_incomplete")
        else:
            checks.append(
                {
                    "id": "criterion_c_indicators",
                    "ok": True,
                    "message": "Criterion C service indicators have configured point values.",
                }
            )

        for ind_id, entry in indicators.items():
            if not is_criterion_c_indicator(ind_id):
                continue
            if not isinstance(entry, dict):
                continue
            pts = _nonnegative_number(entry.get("points"))
            if pts is None:
                pts = _nonnegative_number(entry.get("maxPoints"))
            if cmax is not None and pts is not None and pts > cmax + 1e-6:
                checks.append(
                    {
                        "id": f"criterion_c_cap_{ind_id}",
                        "ok": False,
                        "message": f"{ind_id} points exceed Criterion C maximum.",
                    }
                )
                if "criterion_c_indicator_exceeds_max" not in errors:
                    errors.append("criterion_c_indicator_exceeds_max")

        if not any(not c.get("ok") for c in checks if c["id"].startswith("criterion_c_cap_")):
            if cmax is not None:
                checks.append(
                    {
                        "id": "criterion_c_indicator_caps",
                        "ok": True,
                        "message": "Criterion C indicator points do not exceed the criterion maximum.",
                    }
                )

    return checks, errors
