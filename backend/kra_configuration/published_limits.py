"""KRA and criterion maximum points from published Admin scoring configuration."""

from __future__ import annotations

import re
from typing import Any

from datetime import date

from kra_configuration.resolver import resolve_scoring_configuration, settings_blob_from_resolution
from kra_configuration.service import get_published_row, kra_settings_from_json

_CRITERION_ID_RE = re.compile(r"^kra\d+-([a-d])$", re.IGNORECASE)


def published_settings_blob(
    settings_json: dict | None = None,
    *,
    as_of: date | None = None,
    kra_configuration_id: int | None = None,
) -> dict[str, Any]:
    if settings_json is not None:
        return kra_settings_from_json(settings_json)
    resolution = resolve_scoring_configuration(as_of=as_of, kra_configuration_id=kra_configuration_id)
    return settings_blob_from_resolution(resolution)


def kra_config_row(settings: dict[str, Any], kra_id: str) -> dict[str, Any] | None:
    """Published KRA row (overall maximum, labels) — not the sum of criteria."""
    kras = settings.get("kras")
    if isinstance(kras, dict):
        entry = kras.get(kra_id)
        if isinstance(entry, dict):
            return entry
    if isinstance(kras, list):
        for entry in kras:
            if isinstance(entry, dict) and entry.get("id") == kra_id:
                return entry
    return None


def criteria_entries_for_kra(settings: dict[str, Any], kra_id: str) -> list[dict[str, Any]]:
    """Ordered criterion rows for one KRA (id prefix ``kra1-``, etc.)."""
    prefix = f"{kra_id}-"
    criteria = settings.get("criteria")
    rows: list[dict[str, Any]] = []
    if not isinstance(criteria, dict):
        return rows
    for cid in sorted(criteria.keys()):
        if not str(cid).startswith(prefix):
            continue
        entry = criteria.get(cid)
        if not isinstance(entry, dict):
            continue
        rows.append({"criterionId": cid, **entry})
    return rows


def criterion_is_bonus(entry: dict[str, Any]) -> bool:
    """Bonus criteria (e.g. KRA III/IV D) count toward KRA total only up to overall KRA max."""
    if entry.get("bonus") is True or entry.get("isBonus") is True:
        return True
    return False


def published_criterion_max_points(
    criterion_id: str,
    settings: dict[str, Any] | None = None,
) -> float | None:
    blob = settings if settings is not None else published_settings_blob()
    criteria = blob.get("criteria")
    if not isinstance(criteria, dict):
        return None
    entry = criteria.get(criterion_id)
    if not isinstance(entry, dict):
        return None
    raw = entry.get("maxPoints")
    if raw is None:
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def published_kra_max_points(kra_id: str, settings: dict[str, Any] | None = None) -> float:
    """
    Overall KRA maximum from published configuration (JC 01 s. 2026: 100 per KRA).

    This is **not** the sum of criterion maximums. Research KRA II uses alternative
    100-point categories (A, B, or C). Extension/Prof Dev may include bonus criteria
    whose points do not increase the overall KRA cap beyond the published KRA max.
    """
    blob = settings if settings is not None else published_settings_blob()
    row = kra_config_row(blob, kra_id)
    if row is not None and row.get("maxPoints") is not None:
        try:
            return float(row["maxPoints"])
        except (TypeError, ValueError):
            pass

    # Legacy configs without a KRA row: sum non-bonus criteria only (additive KRA I style).
    crits = criteria_entries_for_kra(blob, kra_id)
    total = 0.0
    found = False
    for entry in crits:
        if criterion_is_bonus(entry):
            continue
        raw = entry.get("maxPoints")
        if raw is None:
            continue
        try:
            total += float(raw)
            found = True
        except (TypeError, ValueError):
            continue
    if found:
        return total
    return 100.0


def criterion_letter(criterion_id: str | None) -> str | None:
    if not criterion_id:
        return None
    match = _CRITERION_ID_RE.match(str(criterion_id).strip())
    return match.group(1).upper() if match else None


def _looks_like_internal_id(value: str) -> bool:
    return bool(_CRITERION_ID_RE.match(value.strip()))


def format_criterion_user_label(
    criterion_id: str,
    entry: dict[str, Any] | None = None,
    *,
    settings: dict[str, Any] | None = None,
) -> str:
    """
    User-facing label: ``Criterion A — Official name`` (never ``kra1-a``).
    Names come from published Admin criteria config when available.
    """
    cid = (criterion_id or "").strip()
    if not cid:
        return "—"

    if entry is None and settings is not None:
        criteria = settings.get("criteria")
        if isinstance(criteria, dict):
            raw = criteria.get(cid)
            entry = raw if isinstance(raw, dict) else None

    letter = criterion_letter(cid)
    prefix = f"Criterion {letter}" if letter else "Criterion"

    descriptive = ""
    if entry and isinstance(entry, dict):
        descriptive = str(entry.get("name") or entry.get("label") or "").strip()
    if descriptive and _looks_like_internal_id(descriptive):
        descriptive = ""

    if descriptive:
        lowered = descriptive.lower()
        if lowered.startswith("criterion ") and "—" in descriptive:
            return descriptive
        if letter and lowered.startswith(f"criterion {letter.lower()}"):
            if "—" in descriptive:
                return descriptive
            tail = re.sub(r"^criterion\s+[a-d]\s*[-–:]?\s*", "", descriptive, flags=re.I).strip()
            return f"{prefix} — {tail}" if tail else prefix
        return f"{prefix} — {descriptive}"

    return prefix


def published_criterion_user_label(
    criterion_id: str,
    settings: dict[str, Any] | None = None,
) -> str:
    blob = settings if settings is not None else published_settings_blob()
    return format_criterion_user_label(criterion_id, settings=blob)


def criterion_display_name(criterion_id: str, entry: dict[str, Any] | None) -> str:
    """Alias used by rank simulation criterion breakdown rows."""
    return format_criterion_user_label(criterion_id, entry)
