"""System-managed verified SET/SEF scoring method (DBM–CHED JC 01 s. 2026 §§7–10)."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from config import Config
from documents.scoring.section10 import CIRCULAR_AGGREGATION_METHOD, default_evaluation_coverage

SET_INDICATOR = "kra1-a-student"
SEF_INDICATOR = "kra1-a-supervisor"
CRITERION_A_ID = "kra1-a"

OFFICIAL_FORMULA_REFERENCE = (
    "DBM–CHED Joint Circular No. 01, s. 2026, Sections 7–10: OSETR/OSEFR as the average of "
    "semester ratings divided by the applicable divisor; indicator points from "
    "(overall rating ÷ 100) × published multiplier. Section 10 exceptions require "
    "reviewer-verified eligibility before the divisor changes."
)

SCORING_METHOD_LABEL = "SET/SEF semester average (OSETR / OSEFR)"


def verified_set_sef_metadata(*, rounding_rule: str | None = None) -> dict[str, Any]:
    """Metadata stored on publish when draft passes validation."""
    meta: dict[str, Any] = {
        "officialFormulaVerified": True,
        "aggregationMethod": CIRCULAR_AGGREGATION_METHOD,
        "formulaReference": OFFICIAL_FORMULA_REFERENCE,
        "scoringMethodLabel": SCORING_METHOD_LABEL,
        "incompleteReason": "",
    }
    if rounding_rule:
        meta["roundingRule"] = rounding_rule
    return meta


def _indicator_points(entry: dict | None) -> tuple[float | None, float | None]:
    if not isinstance(entry, dict):
        return None, None
    max_pts = entry.get("maxPoints")
    multiplier = entry.get("multiplier")
    formula = entry.get("formula") if isinstance(entry.get("formula"), dict) else {}
    if multiplier is None and formula.get("type") == "rating":
        multiplier = formula.get("multiplier")
    if max_pts is None and multiplier is not None:
        max_pts = multiplier
    if multiplier is None and max_pts is not None:
        multiplier = max_pts
    try:
        max_f = float(max_pts) if max_pts is not None else None
        mult_f = float(multiplier) if multiplier is not None else None
    except (TypeError, ValueError):
        return None, None
    if max_f is None or mult_f is None or max_f <= 0 or mult_f <= 0:
        return None, None
    return max_f, mult_f


def _coverage_ok(coverage: dict | None) -> tuple[bool, str | None]:
    cov = coverage if isinstance(coverage, dict) else default_evaluation_coverage()
    standard = cov.get("standardRequiredSemesters") or cov.get("requiredSemesters")
    try:
        semesters = int(standard) if standard is not None else 6
    except (TypeError, ValueError):
        return False, "Standard required semesters must be a positive number."
    if semesters < 1:
        return False, "Standard required semesters must be at least 1."
    return True, None


def assess_publish_readiness(
    settings_json: dict,
    *,
    effective_from: str | None,
) -> dict[str, Any]:
    """Non-destructive validation for Admin publish preview and publish gate."""
    settings = settings_json if isinstance(settings_json, dict) else {}
    indicators = settings.get("indicators") if isinstance(settings.get("indicators"), dict) else {}
    criteria = settings.get("criteria") if isinstance(settings.get("criteria"), dict) else {}
    coverage = settings.get("evaluationCoverage") or settings.get("teachingEffectivenessCoverage")
    if not isinstance(coverage, dict):
        coverage = default_evaluation_coverage()

    checks: list[dict[str, Any]] = []
    errors: list[str] = []

    eff = (effective_from or settings.get("effectiveFrom") or "").strip()
    if not eff:
        checks.append(
            {
                "id": "effective_date",
                "ok": False,
                "message": "Effective date is required.",
            }
        )
        errors.append("effective_from_required")
    else:
        try:
            from datetime import date

            date.fromisoformat(eff[:10])
            checks.append(
                {
                    "id": "effective_date",
                    "ok": True,
                    "message": f"Effective from {eff[:10]}.",
                }
            )
        except ValueError:
            checks.append(
                {
                    "id": "effective_date",
                    "ok": False,
                    "message": "Effective date must be a valid calendar date (YYYY-MM-DD).",
                }
            )
            errors.append("effective_from_invalid")

    set_max, set_mult = _indicator_points(indicators.get(SET_INDICATOR))
    if set_max is None:
        checks.append(
            {
                "id": "set_indicator",
                "ok": False,
                "message": "Student Evaluation of Teaching (SET) maximum points / multiplier is missing or invalid.",
            }
        )
        errors.append("set_indicator_incomplete")
    else:
        checks.append(
            {
                "id": "set_indicator",
                "ok": True,
                "message": f"SET configured ({set_max:g} points maximum).",
            }
        )

    sef_max, sef_mult = _indicator_points(indicators.get(SEF_INDICATOR))
    if sef_max is None:
        checks.append(
            {
                "id": "sef_indicator",
                "ok": False,
                "message": "Supervisor Evaluation of Faculty (SEF) maximum points / multiplier is missing or invalid.",
            }
        )
        errors.append("sef_indicator_incomplete")
    else:
        checks.append(
            {
                "id": "sef_indicator",
                "ok": True,
                "message": f"SEF configured ({sef_max:g} points maximum).",
            }
        )

    cov_ok, cov_msg = _coverage_ok(coverage)
    standard = int(coverage.get("standardRequiredSemesters") or coverage.get("requiredSemesters") or 6)
    if cov_ok:
        checks.append(
            {
                "id": "evaluation_coverage",
                "ok": True,
                "message": f"Standard evaluation coverage: {standard} semester rating(s) before Section 10 adjustments.",
            }
        )
    else:
        checks.append({"id": "evaluation_coverage", "ok": False, "message": cov_msg or "Invalid coverage."})
        errors.append("evaluation_coverage_invalid")

    crit = criteria.get(CRITERION_A_ID) if isinstance(criteria.get(CRITERION_A_ID), dict) else {}
    crit_max = crit.get("maxPoints")
    if crit_max is not None and set_max is not None and sef_max is not None:
        try:
            cmax = float(crit_max)
            if cmax > 0 and (set_max + sef_max) > cmax + 1e-6:
                checks.append(
                    {
                        "id": "criterion_a_totals",
                        "ok": False,
                        "message": (
                            f"Criterion A maximum ({cmax:g}) is less than SET + SEF maxima ({set_max + sef_max:g})."
                        ),
                    }
                )
                errors.append("criterion_a_inconsistent")
            else:
                checks.append(
                    {
                        "id": "criterion_a_totals",
                        "ok": True,
                        "message": "Criterion A maximum is consistent with SET and SEF caps.",
                    }
                )
        except (TypeError, ValueError):
            checks.append(
                {
                    "id": "criterion_a_totals",
                    "ok": True,
                    "message": "Criterion A maximum not set or not numeric (SET/SEF caps still apply).",
                }
            )
    else:
        checks.append(
            {
                "id": "criterion_a_totals",
                "ok": True,
                "message": "SET and SEF caps will apply under Teaching Effectiveness (Criterion A).",
            }
        )

    checks.append(
        {
            "id": "verified_method",
            "ok": not errors,
            "message": (
                f"Official method: {SCORING_METHOD_LABEL} ({Config.GUIDELINE_LABEL})."
                if not errors
                else "Complete the checks above before the verified SET/SEF method can be activated."
            ),
        }
    )

    ready = len(errors) == 0
    summary = {
        "guidelineLabel": Config.GUIDELINE_LABEL,
        "scoringMethodLabel": SCORING_METHOD_LABEL,
        "formulaReference": OFFICIAL_FORMULA_REFERENCE,
        "aggregationMethod": CIRCULAR_AGGREGATION_METHOD,
        "evaluationCoverage": deepcopy(coverage),
        "setMaxPoints": set_max,
        "sefMaxPoints": sef_max,
        "section10Note": (
            "Section 10 divisor exceptions remain subject to reviewer verification per faculty; "
            "they are not changed by publishing this configuration."
        ),
    }

    return {
        "ready": ready,
        "errors": errors,
        "checks": checks,
        "summary": summary,
        "effectiveFrom": eff[:10] if eff else None,
    }


def apply_verified_scoring_to_settings(settings_json: dict, *, effective_from: str) -> dict[str, Any]:
    """Merge publish metadata after readiness checks pass."""
    merged = deepcopy(settings_json)
    assessment = assess_publish_readiness(merged, effective_from=effective_from)
    if not assessment["ready"]:
        code = assessment["errors"][0] if assessment["errors"] else "publish_validation_failed"
        raise ValueError(code)

    merged["effectiveFrom"] = effective_from[:10]
    if not isinstance(merged.get("evaluationCoverage"), dict):
        merged["evaluationCoverage"] = default_evaluation_coverage()

    rounding = merged.get("roundingRule")
    set_sef = verified_set_sef_metadata(rounding_rule=rounding if isinstance(rounding, str) else None)
    merged["setSefScoring"] = set_sef
    merged["setSefAggregationMethod"] = CIRCULAR_AGGREGATION_METHOD
    return merged
