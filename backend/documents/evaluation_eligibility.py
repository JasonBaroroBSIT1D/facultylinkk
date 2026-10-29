"""Reviewer-managed Section 10 evaluation eligibility (audited, scoring-facing)."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

from extensions import db
from models import FacultyProfile, User

from documents.scoring.section10 import SECTION_10_CATALOG, section10_catalog_for_api

MAX_AUDIT_ENTRIES = 40
MIN_JUSTIFICATION_LEN = 16
STANDARD_SEMESTERS_MAX = 6


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _empty_store() -> dict[str, Any]:
    return {"current": None, "auditLog": []}


def normalize_store(raw: dict | None) -> dict[str, Any]:
    if not isinstance(raw, dict):
        return _empty_store()
    store = {
        "current": raw.get("current") if isinstance(raw.get("current"), dict) else None,
        "auditLog": list(raw.get("auditLog") or []) if isinstance(raw.get("auditLog"), list) else [],
    }
    return store


def eligibility_for_scoring(raw: dict | None) -> dict | None:
    """Shape consumed by `resolve_divisor` / SET–SEF aggregation."""
    store = normalize_store(raw)
    current = store.get("current")
    if not isinstance(current, dict):
        return None
    code = (current.get("section10Code") or "").strip() or None
    if not code:
        return None
    verified = current.get("reviewerVerified") is True and current.get("evidenceOnFileAttested") is True
    count = current.get("eligibleSemesterCount")
    try:
        count_int = int(count) if count is not None else None
    except (TypeError, ValueError):
        count_int = None
    return {
        "section10Code": code,
        "eligibleSemesterCount": count_int,
        "reviewerVerified": verified,
        "exceptionVerified": verified,
    }


def payload_for_api(profile: FacultyProfile) -> dict[str, Any]:
    raw = getattr(profile, "evaluation_eligibility_json", None)
    store = normalize_store(raw)
    current = store.get("current")
    scoring = eligibility_for_scoring(raw)
    return {
        "facultyId": profile.public_id,
        "current": current,
        "auditLog": store.get("auditLog") or [],
        "section10Catalog": section10_catalog_for_api(),
        "scoringEligibility": scoring,
        "standardRequiredSemesters": STANDARD_SEMESTERS_MAX,
    }


def reviewer_can_manage(reviewer: User, profile: FacultyProfile) -> bool:
    return bool(profile and profile.reviewer_user_id == reviewer.id)


def _validate_body(body: dict, *, verifying: bool, clearing: bool) -> tuple[dict | None, str | None]:
    if clearing:
        reason = (body.get("justification") or body.get("reason") or "").strip()
        if len(reason) < MIN_JUSTIFICATION_LEN:
            return None, "justification_required"
        return None, None

    code = (body.get("section10Code") or body.get("exceptionCode") or "").strip() or None
    if not code or code not in SECTION_10_CATALOG:
        return None, "invalid_section10_code"

    meta = SECTION_10_CATALOG[code]
    justification = (body.get("justification") or body.get("reason") or "").strip()
    evidence_summary = (body.get("supportingEvidenceSummary") or body.get("evidenceSummary") or "").strip()
    attested = body.get("evidenceOnFileAttested") is True
    verified = body.get("reviewerVerified") is True

    if len(justification) < MIN_JUSTIFICATION_LEN:
        return None, "justification_required"

    try:
        count = int(body.get("eligibleSemesterCount")) if body.get("eligibleSemesterCount") is not None else None
    except (TypeError, ValueError):
        count = None

    if verified or verifying:
        if not attested:
            return None, "evidence_attestation_required"
        if len(evidence_summary) < MIN_JUSTIFICATION_LEN:
            return None, "evidence_summary_required"
        if meta.get("requiresEligibleSemesterCount") and (count is None or count <= 0):
            return None, "eligible_semester_count_required"
        if count is not None and count > STANDARD_SEMESTERS_MAX:
            return None, "eligible_semester_count_too_high"

    next_current = {
        "section10Code": code,
        "section10Label": meta["label"],
        "eligibleSemesterCount": count,
        "reviewerVerified": verified and attested,
        "evidenceOnFileAttested": attested,
        "supportingEvidenceSummary": evidence_summary or None,
        "justification": justification,
    }
    return next_current, None


def apply_eligibility_update(
    reviewer: User,
    profile: FacultyProfile,
    body: dict,
) -> FacultyProfile:
    if not reviewer_can_manage(reviewer, profile):
        raise ValueError("forbidden")

    raw = getattr(profile, "evaluation_eligibility_json", None)
    store = normalize_store(raw if isinstance(raw, dict) else None)
    previous = deepcopy(store.get("current")) if store.get("current") else None

    clearing = body.get("clear") is True
    verifying = body.get("reviewerVerified") is True
    next_current, error = _validate_body(body, verifying=verifying, clearing=clearing)
    if error:
        raise ValueError(error)

    action = "clear" if clearing else "update"
    if clearing:
        store["current"] = None
    else:
        assert next_current is not None
        next_current["updatedAt"] = _utcnow_iso()
        next_current["updatedById"] = reviewer.public_id
        next_current["updatedByName"] = reviewer.full_name
        store["current"] = next_current

    entry = {
        "at": _utcnow_iso(),
        "reviewerId": reviewer.public_id,
        "reviewerName": reviewer.full_name,
        "action": action,
        "justification": (body.get("justification") or body.get("reason") or "").strip(),
        "previous": previous,
        "next": deepcopy(store.get("current")),
    }
    log = list(store.get("auditLog") or [])
    log.append(entry)
    store["auditLog"] = log[-MAX_AUDIT_ENTRIES:]

    profile.evaluation_eligibility_json = store
    db.session.commit()
    return profile
