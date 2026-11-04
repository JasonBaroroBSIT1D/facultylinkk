"""KRA II indicator catalog registry (rules.js export; PDF cross-check pending)."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from kra_configuration.kra2_annex import CRITERION_A_ID, CRITERION_B_ID, CRITERION_C_ID, is_kra2_indicator

_DATA_PATH = Path(__file__).resolve().parent / "data" / "kra2_indicators.json"

# Reusable workflow families (shared UX + validation, not identical evidence text).
FAMILY_PUBLICATION = "publication_output"
FAMILY_CITATION = "citation_impact"
FAMILY_INVENTION = "invention_ip"
FAMILY_COMMERCIAL = "commercialization"
FAMILY_CREATIVE = "creative_work"
FAMILY_PERFORMANCE = "performance_work"

_OFFICIAL_RULES_VERIFIED = True  # Core rules anchored in JC PDF pages (see kra2_official_verification.py).


@lru_cache(maxsize=1)
def _catalog() -> dict[str, Any]:
    if not _DATA_PATH.is_file():
        return {"indicators": []}
    raw = json.loads(_DATA_PATH.read_text(encoding="utf-8"))
    return raw if isinstance(raw, dict) else {"indicators": []}


def official_rules_verified() -> bool:
    from kra_configuration.kra2_official_verification import official_rules_verified as _pdf_core

    return _pdf_core() and _OFFICIAL_RULES_VERIFIED


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
    parts = iid.split("-")
    family_token = parts[2] if len(parts) >= 3 else ""
    crit = "-".join(parts[:2]) if len(parts) >= 2 else ""

    if family_token == "cite":
        return FAMILY_CITATION
    if crit == CRITERION_B_ID:
        if family_token.startswith("comm"):
            return FAMILY_COMMERCIAL
        if family_token.startswith("sw") or family_token == "variety":
            return FAMILY_INVENTION
        return FAMILY_INVENTION
    if crit == CRITERION_C_ID:
        perf_tokens = frozenset(
            {
                "music-perf",
                "dance-perf",
                "conducting",
                "acting",
                "directing",
            }
        )
        if family_token in perf_tokens or iid.endswith("-perf") or "perf" in family_token:
            return FAMILY_PERFORMANCE
        return FAMILY_CREATIVE
    return FAMILY_PUBLICATION


def allows_reviewer_partial_points(indicator_id: str) -> bool:
    """
    Indicators where reviewer may assess below the system-calculated eligible amount
    when official indexing/eligibility rules require it (JC Sec. 19–21), or tiered caps apply.
    """
    iid = (indicator_id or "").strip()
    if not iid:
        return False
    if "journal" in iid or "cite" in iid:
        return True
    row = indicator_row(indicator_id)
    if not row:
        return False
    try:
        base = float(row.get("points") or 0)
        mx = float(row.get("maxPoints") or base)
        group_max = row.get("groupMax")
        gm = float(group_max) if group_max is not None else None
    except (TypeError, ValueError):
        return False
    contrib = (row.get("contribution") or "").strip().lower()
    if mx > base + 0.001 and contrib == "not-applicable":
        return True
    if gm is not None and gm > base + 0.001:
        return True
    if family_token_allows_tiered_partial(iid):
        return True
    return False


def family_token_allows_tiered_partial(indicator_id: str) -> bool:
    """Commercialization indicators with published tier max above base points."""
    iid = (indicator_id or "").strip()
    parts = iid.split("-")
    if len(parts) >= 3 and parts[2].startswith("comm"):
        return True
    return False


def official_indicator_max_points(indicator_id: str, settings: dict[str, Any] | None = None) -> float | None:
    """Published per-accomplishment maximum from Admin (not criterion or group caps)."""
    iid = (indicator_id or "").strip()
    if settings and isinstance(settings.get("indicators"), dict):
        entry = settings["indicators"].get(iid)
        if isinstance(entry, dict):
            vals: list[float] = []
            for key in ("points", "maxPoints"):
                raw = entry.get(key)
                if raw is not None:
                    try:
                        vals.append(float(raw))
                    except (TypeError, ValueError):
                        pass
            if vals:
                return max(vals)
    row = indicator_row(iid)
    if not row:
        return None
    try:
        vals = [float(row.get("points") or 0), float(row.get("maxPoints") or row.get("points") or 0)]
        return max(vals)
    except (TypeError, ValueError):
        return None


def reviewer_adjustment_governing_rule(indicator_id: str) -> str:
    """Plain-language rule for reviewer UI (derived from catalog; not a new policy)."""
    iid = (indicator_id or "").strip()
    if "journal" in iid:
        return (
            "Journal outputs may receive less than the full published base when indexing or "
            "eligibility rules in the official matrix do not support the maximum."
        )
    if "cite" in iid:
        return (
            "Citation impact uses a tiered catalog; assess below the system-calculated amount "
            "when the cited work or evidence does not support full credit."
        )
    parts = iid.split("-")
    if len(parts) >= 3 and parts[2].startswith("comm"):
        return (
            "Commercialization uses tiered published caps; assess below the system-calculated "
            "amount when revenue, licensing, or market evidence supports a lower tier only."
        )
    row = indicator_row(iid)
    gm = row.get("groupMax") if row else None
    try:
        if gm is not None and float(gm) > float((row or {}).get("points") or 0) + 0.001:
            return (
                "This indicator has a published group cap; per-output base points apply and "
                "assessed points may be reduced when evidence does not support full eligibility."
            )
    except (TypeError, ValueError):
        pass
    if contribution_mode(iid) == "declared":
        return (
            "Co-authored outputs scale with verified contribution percentage. Adjust contribution "
            "after verifying authorship; you may also reduce assessed points when partial rules apply."
        )
    return (
        "Official fixed points for a fully eligible output. Approve at the system-calculated "
        "amount or reject/return when evidence is ineligible — arbitrary partial scores are not allowed."
    )


def contribution_mode(indicator_id: str) -> str:
    row = indicator_row(indicator_id)
    if row:
        c = (row.get("contribution") or "").strip().lower()
        if c in ("declared", "sole", "not-applicable"):
            return c
    parts = (indicator_id or "").split("-")
    if parts and parts[-1] == "co":
        return "declared"
    if parts and parts[-1] == "sole":
        return "sole"
    return "not-applicable"


def metadata_field_ids(indicator_id: str) -> tuple[str, ...]:
    """Bundle keys required for faculty submit (family-specific)."""
    family = workflow_family(indicator_id)
    base = ("outputTitle", "authorsLine", "outputVenue", "publicationDate")
    if family == FAMILY_CITATION:
        return ("outputTitle", "citationContext", "publicationDate")
    if family == FAMILY_INVENTION:
        fields = ["outputTitle", "registrationNumber", "registrationDate", "authorsLine"]
        if contribution_mode(indicator_id) == "declared":
            fields.append("declaredContributionPercent")
        return tuple(fields)
    if family == FAMILY_COMMERCIAL:
        return ("outputTitle", "outputVenue", "publicationDate", "authorsLine")
    if contribution_mode(indicator_id) == "declared":
        return base + ("declaredContributionPercent",)
    return base


def user_facing_title(indicator_id: str) -> str:
    row = indicator_row(indicator_id)
    return (row.get("name") if row else None) or indicator_id


def user_facing_description(indicator_id: str) -> str:
    row = indicator_row(indicator_id)
    hints = row.get("evidenceHints") if isinstance(row, dict) else None
    if isinstance(hints, list) and hints:
        return hints[0]
    family = workflow_family(indicator_id)
    if family == FAMILY_INVENTION:
        return "Upload official proof of registration, acceptance, or grant as applicable."
    if family == FAMILY_CITATION:
        return "Upload evidence that your research publication was cited."
    if family == FAMILY_CREATIVE:
        return "Upload proof of publication, exhibition, or recognized creative output."
    return "Upload a PDF copy of the published or registered output."


def scoring_group(indicator_id: str) -> str | None:
    row = indicator_row(indicator_id)
    if not row:
        return None
    g = row.get("group")
    return str(g).strip() if g else None


def scoring_group_max(indicator_id: str) -> float | None:
    row = indicator_row(indicator_id)
    if not row:
        return None
    raw = row.get("groupMax")
    try:
        return float(raw) if raw is not None else None
    except (TypeError, ValueError):
        return None


def patent_stage_key(indicator_id: str) -> str | None:
    """Within evaluation period, highest patent stage counts once."""
    iid = (indicator_id or "").strip()
    if not iid.startswith("kra2-b-patent-"):
        return None
    parts = iid.split("-")
    if len(parts) >= 4:
        return parts[3]  # a, p, g
    return None


def indicator_support_status(indicator_id: str) -> str:
    """
    COMPLETE — full workflow + catalog row.
    BLOCKED — catalog present but official PDF rules unverified (approval still reviewer-gated).
    """
    if not is_kra2_indicator(indicator_id):
        return "NOT STARTED"
    if not indicator_row(indicator_id):
        return "NOT STARTED"
    if official_rules_verified():
        return "COMPLETE"
    # Workflow implemented for all catalog rows; PDF annex proof pending.
    return "PARTIAL"
