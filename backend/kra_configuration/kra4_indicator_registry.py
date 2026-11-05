"""KRA IV indicator catalog (rules.js export)."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from kra_configuration.kra4_annex import (
    CRITERION_A_ID,
    CRITERION_B_ID,
    CRITERION_C_ID,
    CRITERION_D_ID,
    is_kra4_indicator,
)

_DATA_PATH = Path(__file__).resolve().parent / "data" / "kra4_indicators.json"

FAMILY_ORGANIZATION = "organization"
FAMILY_EDUCATION = "education"
FAMILY_CAPACITY = "capacity_building"
FAMILY_PAPER = "paper_presentation"
FAMILY_AWARD = "award"
FAMILY_PRIOR_EXPERIENCE = "prior_experience"
FAMILY_GENERIC = "generic"


@lru_cache(maxsize=1)
def _catalog() -> dict[str, Any]:
    if not _DATA_PATH.is_file():
        return {"indicators": []}
    raw = json.loads(_DATA_PATH.read_text(encoding="utf-8"))
    return raw if isinstance(raw, dict) else {"indicators": []}


def all_indicators() -> list[dict[str, Any]]:
    items = _catalog().get("indicators")
    return list(items) if isinstance(items, list) else []


def indicator_row(indicator_id: str | None) -> dict[str, Any] | None:
    iid = (indicator_id or "").strip()
    for row in all_indicators():
        if row.get("id") == iid:
            return dict(row)
    return None


def indicators_for_criterion(criterion_id: str) -> list[dict[str, Any]]:
    cid = (criterion_id or "").strip()
    return [dict(r) for r in all_indicators() if r.get("criterionId") == cid]


def workflow_family(indicator_id: str) -> str:
    iid = (indicator_id or "").strip()
    if iid.startswith("kra4-a-"):
        return FAMILY_ORGANIZATION
    if iid.startswith("kra4-b-post") or iid.startswith("kra4-b-master") or iid == "kra4-b-doctorate":
        return FAMILY_EDUCATION
    if iid.startswith("kra4-b-part"):
        return FAMILY_CAPACITY
    if iid.startswith("kra4-b-paper"):
        return FAMILY_PAPER
    if iid.startswith("kra4-c-"):
        return FAMILY_AWARD
    if iid.startswith("kra4-d-"):
        return FAMILY_PRIOR_EXPERIENCE
    return FAMILY_GENERIC


def contribution_mode(indicator_id: str) -> str:
    row = indicator_row(indicator_id) or {}
    return (row.get("contribution") or "not-applicable").strip().lower()


def user_facing_title(indicator_id: str) -> str:
    row = indicator_row(indicator_id)
    if row and row.get("name"):
        return str(row["name"])
    return indicator_id


def scoring_group(indicator_id: str) -> str | None:
    """Scoring group id for groupMax caps (column, guest, ISR, etc.)."""
    return scoring_group_key(indicator_id)


def scoring_group_key(indicator_id: str) -> str | None:
    row = indicator_row(indicator_id)
    if not row:
        return None
    grp = row.get("group")
    return str(grp).strip() if grp else None


def scoring_group_max(indicator_id: str) -> float | None:
    row = indicator_row(indicator_id)
    if not row:
        return None
    raw = row.get("groupMax")
    try:
        return float(raw) if raw is not None else None
    except (TypeError, ValueError):
        return None


def official_indicator_max_points(indicator_id: str, settings: dict[str, Any] | None) -> float | None:
    from kra_configuration.kra4_annex import published_kra4_indicator_base_points

    base = published_kra4_indicator_base_points(indicator_id, settings, allow_annex_fallback=True)
    row = indicator_row(indicator_id)
    if row and row.get("formulaRating"):
        return float(row.get("formulaMultiplier") or 20.0)
    if base is not None and row and row.get("maxPoints") is not None:
        try:
            return float(row["maxPoints"])
        except (TypeError, ValueError):
            pass
    return base


def allows_reviewer_partial_points(indicator_id: str) -> bool:
    fam = workflow_family(indicator_id)
    return fam in (FAMILY_CAPACITY, FAMILY_PAPER, FAMILY_PRIOR_EXPERIENCE)


def reviewer_adjustment_governing_rule(indicator_id: str) -> str:
    fam = workflow_family(indicator_id)
    if fam == FAMILY_PRIOR_EXPERIENCE:
        return "Points follow verified years of qualifying experience × the published per-year rate, capped at 20 for Criterion D."
    if fam == FAMILY_CAPACITY:
        return "Verify duration, scope, and approval requirements before awarding participation points."
    if fam == FAMILY_PAPER:
        return "International presentations require verified multi-country participation when applicable."
    return "Use published official points unless rules allow adjustment."


def metadata_field_ids(indicator_id: str) -> tuple[str, ...]:
    from kra_configuration.kra4_workflow import metadata_field_ids as _fields

    return _fields(indicator_id)


def is_formula_rating_indicator(indicator_id: str) -> bool:
    row = indicator_row(indicator_id)
    return bool(row and row.get("formulaRating"))
