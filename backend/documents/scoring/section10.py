"""Section 10 — special evaluation-period circumstances (DBM–CHED JC No. 01, s. 2026)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Catalog keys align with published Admin `evaluationCoverage.section10Exceptions`.
SECTION_10_CATALOG: dict[str, dict[str, Any]] = {
    "newly_appointed": {
        "label": "Newly appointed faculty",
        "requiresReviewerVerification": True,
        "requiresEligibleSemesterCount": True,
        "evidenceHint": "Appointment order and semesters of service within the evaluation period.",
    },
    "study_leave": {
        "label": "Official study leave",
        "requiresReviewerVerification": True,
        "requiresEligibleSemesterCount": True,
        "evidenceHint": "Approved study-leave documentation for absent semesters.",
    },
    "maternity_leave": {
        "label": "Approved maternity leave",
        "requiresReviewerVerification": True,
        "requiresEligibleSemesterCount": True,
        "evidenceHint": "Approved maternity leave and return-to-service records.",
    },
    "sabbatical_leave": {
        "label": "Sabbatical leave",
        "requiresReviewerVerification": True,
        "requiresEligibleSemesterCount": True,
        "evidenceHint": "Sabbatical approval and applicable service timeline.",
    },
    "suc_laboratory_school": {
        "label": "SUC laboratory-school teaching",
        "requiresReviewerVerification": True,
        "requiresEligibleSemesterCount": True,
        "evidenceHint": "Laboratory-school assignment and institutional evaluation policy.",
    },
}

CIRCULAR_AGGREGATION_METHOD = "circular_jc_2026_semester_average"


@dataclass
class DivisorResolution:
    standard_required_semesters: int
    eligible_divisor: int | None
    finalized: bool
    section10_code: str | None = None
    section10_verified: bool = False
    audit: list[str] = field(default_factory=list)
    incomplete_reason: str | None = None


def default_evaluation_coverage() -> dict[str, Any]:
    return {
        "standardRequiredSemesters": 6,
        "description": (
            "Standard reclassification evaluation period: three academic years with "
            "two semesters each (six semester ratings)."
        ),
        "section10Exceptions": [
            {"code": code, **{k: v for k, v in meta.items() if k != "code"}}
            for code, meta in SECTION_10_CATALOG.items()
        ],
    }


def resolve_divisor(
    coverage: dict | None,
    faculty_eligibility: dict | None,
) -> DivisorResolution:
    cov = coverage if isinstance(coverage, dict) else {}
    standard = cov.get("standardRequiredSemesters") or cov.get("requiredSemesters") or 6
    try:
        standard = int(standard)
    except (TypeError, ValueError):
        standard = 6
    if standard <= 0:
        standard = 6

    audit: list[str] = [f"Standard evaluation coverage: {standard} semester(s) per circular baseline."]
    elig = faculty_eligibility if isinstance(faculty_eligibility, dict) else {}
    code = (elig.get("section10Code") or elig.get("exceptionCode") or "").strip() or None
    verified = elig.get("reviewerVerified") is True or elig.get("exceptionVerified") is True
    count = elig.get("eligibleSemesterCount")

    if not code:
        return DivisorResolution(
            standard_required_semesters=standard,
            eligible_divisor=standard,
            finalized=True,
            audit=audit,
        )

    if code not in SECTION_10_CATALOG:
        return DivisorResolution(
            standard_required_semesters=standard,
            eligible_divisor=None,
            finalized=False,
            section10_code=code,
            section10_verified=verified,
            audit=audit + [f"Unknown Section 10 code: {code}."],
            incomplete_reason="Section 10 exception code is not recognized in published configuration.",
        )

    meta = SECTION_10_CATALOG[code]
    audit.append(f"Section 10 circumstance: {meta['label']} ({code}).")
    if not verified:
        return DivisorResolution(
            standard_required_semesters=standard,
            eligible_divisor=standard,
            finalized=True,
            section10_code=code,
            section10_verified=False,
            audit=audit
            + ["Section 10 exception recorded but not reviewer-verified; standard divisor applies."],
        )

    audit.append("Section 10 exception reviewer-verified.")
    try:
        eligible = int(count) if count is not None else None
    except (TypeError, ValueError):
        eligible = None

    if meta.get("requiresEligibleSemesterCount") and (eligible is None or eligible <= 0):
        return DivisorResolution(
            standard_required_semesters=standard,
            eligible_divisor=None,
            finalized=False,
            section10_code=code,
            section10_verified=True,
            audit=audit + ["Eligible semester count is required for this Section 10 circumstance."],
            incomplete_reason=(
                f"Provide verified eligibleSemesterCount for {meta['label']} "
                "before official OSETR/OSEFR can be computed."
            ),
        )

    divisor = eligible if eligible is not None else standard
    audit.append(f"Applicable divisor after Section 10: {divisor} semester(s).")
    return DivisorResolution(
        standard_required_semesters=standard,
        eligible_divisor=divisor,
        finalized=True,
        section10_code=code,
        section10_verified=True,
        audit=audit,
    )


def section10_catalog_for_api() -> list[dict[str, Any]]:
    return [{"code": code, **meta} for code, meta in SECTION_10_CATALOG.items()]
