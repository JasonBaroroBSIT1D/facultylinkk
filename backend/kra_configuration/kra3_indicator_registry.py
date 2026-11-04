"""KRA III indicator catalog (rules.js export)."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from kra_configuration.kra3_annex import (
    CRITERION_A_ID,
    CRITERION_B_ID,
    CRITERION_C_ID,
    CRITERION_D_ID,
    is_kra3_indicator,
)

_DATA_PATH = Path(__file__).resolve().parent / "data" / "kra3_indicators.json"

FAMILY_LINKAGE = "linkage"
FAMILY_INCOME = "income"
FAMILY_ACCREDITATION = "accreditation"
FAMILY_JUDGING = "judging"
FAMILY_CONSULTANCY = "consultancy"
FAMILY_MEDIA_COLUMN = "media_column"
FAMILY_MEDIA_HOST = "media_host"
FAMILY_MEDIA_GUEST = "media_guest"
FAMILY_RESOURCE = "resource_person"
FAMILY_EXTENSION = "extension_project"
FAMILY_CSR = "csr"
FAMILY_DESIGNATION = "designation"
FAMILY_GENERIC = "generic_service"

DESIGNATION_POINTS_UNVERIFIED = True  # Annex D table not fully verified in repo PDF renders.


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
    if iid == "kra3-a-linkage":
        return FAMILY_LINKAGE
    if "income" in iid:
        return FAMILY_INCOME
    if iid.startswith("kra3-b-qa"):
        return FAMILY_ACCREDITATION
    if iid.startswith("kra3-b-judge"):
        return FAMILY_JUDGING
    if iid.startswith("kra3-b-consult"):
        return FAMILY_CONSULTANCY
    if "column" in iid:
        return FAMILY_MEDIA_COLUMN
    if iid == "kra3-b-host":
        return FAMILY_MEDIA_HOST
    if iid == "kra3-b-guest":
        return FAMILY_MEDIA_GUEST
    if iid.startswith("kra3-b-train"):
        return FAMILY_RESOURCE
    if iid.startswith("kra3-b-ext"):
        return FAMILY_EXTENSION
    if iid == "kra3-c-satisfaction":
        return FAMILY_CSR
    if iid.startswith("kra3-d-"):
        return FAMILY_DESIGNATION
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
    from kra_configuration.kra3_annex import published_kra3_indicator_base_points

    base = published_kra3_indicator_base_points(indicator_id, settings, allow_annex_fallback=True)
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
    return fam in (FAMILY_RESOURCE, FAMILY_CSR) or "income" in indicator_id


def reviewer_adjustment_governing_rule(indicator_id: str) -> str:
    fam = workflow_family(indicator_id)
    if fam == FAMILY_CSR:
        return "CSR points follow (rating ÷ 100) × 20 when evidence is verified."
    if fam == FAMILY_RESOURCE:
        return "Points may scale with verified eligible service hours."
    if fam == FAMILY_INCOME:
        return "Income bracket must match certified gross amount and lead/co role."
    if fam == FAMILY_DESIGNATION and DESIGNATION_POINTS_UNVERIFIED:
        return "Designation points use published Admin configuration when available."
    return "Use published official points unless rules allow adjustment."


def metadata_field_ids(indicator_id: str) -> tuple[str, ...]:
    from kra_configuration.kra3_workflow import metadata_field_ids as _fields

    return _fields(indicator_id)


def is_formula_rating_indicator(indicator_id: str) -> bool:
    row = indicator_row(indicator_id)
    return bool(row and row.get("formulaRating"))
