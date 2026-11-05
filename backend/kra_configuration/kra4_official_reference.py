"""
Independent official reference values for KRA IV scoring tests.

Sources: DBM–CHED JC 01 s. 2026 §§28–36; Annex A pp. 92–96 (see docs/KRA4_OFFICIAL_SCORING_AUDIT.md).
These values are NOT read from the implementation catalog at test time.
"""

from __future__ import annotations

from typing import Any

# Criterion caps (§28)
CRITERION_CAPS = {
    "kra4-a": 30.0,
    "kra4-b": 50.0,
    "kra4-c": 20.0,
    "kra4-d": 20.0,
}
KRA4_CAP = 100.0

# Per-indicator base points verified in audit (MATCH).
VERIFIED_BASE_POINTS: dict[str, float] = {
    "kra4-a-linkage": 5.0,
    "kra4-a-income-lead-100k": 2.0,
    "kra4-a-income-lead-500k": 4.0,
    "kra4-a-income-lead-6m": 6.0,
    "kra4-a-income-lead-12m": 12.0,
    "kra4-a-income-lead-over": 18.0,
    "kra4-a-income-co-100k": 1.0,
    "kra4-a-income-co-500k": 2.0,
    "kra4-a-income-co-6m": 3.0,
    "kra4-a-income-co-12m": 6.0,
    "kra4-a-income-co-over": 9.0,
    "kra4-b-qa-local": 8.0,
    "kra4-b-qa-intl": 10.0,
    "kra4-b-judge-research": 2.0,
    "kra4-b-judge-academic": 1.0,
    "kra4-b-consult-local": 8.0,
    "kra4-b-consult-intl": 10.0,
    "kra4-b-column-occasional": 2.0,
    "kra4-b-column-regular": 10.0,
    "kra4-b-host": 10.0,
    "kra4-b-guest": 1.0,
    "kra4-b-train-local": 2.0,
    "kra4-b-train-intl": 3.0,
    "kra4-b-ext-head": 5.0,
    "kra4-b-ext-participant": 2.0,
}

VERIFIED_GROUP_MAX: dict[str, float] = {
    "kra4-b-column-occasional": 10.0,
    "kra4-b-guest": 10.0,
    "kra4-b-ext-head": 30.0,
    "kra4-b-ext-participant": 30.0,
}

# CSR — formula indicator (not flat base points)
FORMULA_INDICATORS = frozenset({"kra4-c-satisfaction"})

# Criterion D — per-role points UNVERIFIED in Annex extract (audit § Criterion D)
DESIGNATION_INDICATORS_BLOCKED = frozenset(
    {
        f"kra4-d-{suffix}"
        for suffix in (
            "president",
            "vp",
            "chancellor",
            "vc",
            "campus",
            "regent",
            "director",
            "usec",
            "project",
            "inst-chair",
            "inst-member",
            "inst-coord",
            "dean",
            "adean",
            "csec",
            "dept",
            "chair",
            "dept-chair",
            "dept-member",
            "dept-coord",
        )
    }
)


def scoring_unit(indicator_id: str) -> str:
    if indicator_id in FORMULA_INDICATORS:
        return "csr_formula"
    if indicator_id.startswith("kra4-b-train"):
        return "per_hour"
    if indicator_id.startswith("kra4-d-"):
        return "per_year_designation"
    if "income" in indicator_id:
        return "per_accomplishment_band"
    return "per_accomplishment"


def reference_status(indicator_id: str) -> str:
    if indicator_id in DESIGNATION_INDICATORS_BLOCKED:
        return "BLOCKED"
    if indicator_id in FORMULA_INDICATORS:
        return "FORMULA"
    if indicator_id in VERIFIED_BASE_POINTS:
        return "PASS"
    return "NOT_TESTED"
