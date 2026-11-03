"""RRPA/COPC applicability decisions for academic program bundles (§14, Annex A §2)."""

from __future__ import annotations

from typing import Any

from documents.criterion_b_evidence.bundle import _utcnow_iso

RRPA_APPLICABILITY_UNKNOWN: str = "unknown"
RRPA_APPLICABILITY_APPLICABLE: str = "applicable"
RRPA_APPLICABILITY_NOT_APPLICABLE: str = "not_applicable"

RRPA_APPLICABILITY_VALUES: frozenset[str] = frozenset(
    {
        RRPA_APPLICABILITY_UNKNOWN,
        RRPA_APPLICABILITY_APPLICABLE,
        RRPA_APPLICABILITY_NOT_APPLICABLE,
    }
)


def empty_rrpa_copc_applicability_decision() -> dict[str, Any]:
    return {
        "status": RRPA_APPLICABILITY_UNKNOWN,
        "note": "",
        "decidedAt": None,
        "decidedByRole": None,
    }


def rrpa_copc_applicability_from_bundle(bundle: dict[str, Any] | None) -> str:
    if not bundle or not isinstance(bundle, dict):
        return RRPA_APPLICABILITY_UNKNOWN
    decision = bundle.get("rrpaCopcApplicabilityDecision")
    if isinstance(decision, dict):
        status = (decision.get("status") or "").strip()
        if status in RRPA_APPLICABILITY_VALUES:
            return status
    legacy = (bundle.get("rrpaCopcApplicability") or "").strip()
    if legacy in RRPA_APPLICABILITY_VALUES:
        return legacy
    return RRPA_APPLICABILITY_UNKNOWN


def rrpa_copc_applicability_note_from_bundle(bundle: dict[str, Any] | None) -> str:
    if not bundle or not isinstance(bundle, dict):
        return ""
    decision = bundle.get("rrpaCopcApplicabilityDecision")
    if isinstance(decision, dict):
        return (decision.get("note") or "").strip()
    return (bundle.get("rrpaCopcApplicabilityNote") or "").strip()


def apply_rrpa_copc_applicability_decision(
    bundle: dict[str, Any],
    *,
    status: str,
    note: str,
    decided_by_role: str = "reviewer",
) -> None:
    normalized = (status or "").strip()
    if normalized not in RRPA_APPLICABILITY_VALUES:
        raise ValueError("invalid_rrpa_copc_applicability")
    cleaned_note = (note or "").strip()
    if normalized == RRPA_APPLICABILITY_NOT_APPLICABLE and not cleaned_note:
        raise ValueError("rrpa_copc_exemption_note_required")

    decided_at = _utcnow_iso() if normalized != RRPA_APPLICABILITY_UNKNOWN else None
    role = decided_by_role if normalized != RRPA_APPLICABILITY_UNKNOWN else None

    bundle["rrpaCopcApplicabilityDecision"] = {
        "status": normalized,
        "note": cleaned_note,
        "decidedAt": decided_at,
        "decidedByRole": role,
    }
    bundle["rrpaCopcApplicability"] = normalized
    bundle["rrpaCopcApplicabilityNote"] = cleaned_note
