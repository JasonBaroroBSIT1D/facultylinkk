"""Annex C contribution percentage confirmation (reviewer-controlled; OCR advisory only)."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from kra_configuration.criterion_b_annex import indicator_requires_contribution_percent
from kra_configuration.criterion_b_scoring import validate_contribution_percent
from documents.criterion_b_evidence.checklist import SLOT_ANNEX_C_CONTRIBUTION
from documents.criterion_b_evidence.reviewer_assessment import assessment_from_bundle

BUNDLE_KEY = "contributionConfirmation"

STATUS_NOT_CONFIRMED = "not_confirmed"
STATUS_CONFIRMED = "confirmed"
STATUS_MISMATCH = "mismatch"
STATUS_NEEDS_CLARIFICATION = "needs_clarification"
STATUS_LEGACY_GRANDFATHERED = "legacy_grandfathered"

HISTORY_LIMIT = 20
MATCH_TOLERANCE = 0.01


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _confirmation_record(bundle: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(bundle, dict):
        return None
    raw = bundle.get(BUNDLE_KEY)
    return raw if isinstance(raw, dict) else None


def _has_completed_reviewer_assessment(bundle: dict[str, Any] | None) -> bool:
    proposed = assessment_from_bundle(bundle) or {}
    pts = proposed.get("points")
    just = (proposed.get("justification") or "").strip()
    return pts is not None and len(just) >= 10


def _percent_values_in_text(text: str) -> list[float]:
    if not text:
        return []
    found: list[float] = []
    for match in re.finditer(r"(\d+(?:\.\d+)?)\s*(?:%|percent)", text, flags=re.IGNORECASE):
        try:
            found.append(float(match.group(1)))
        except ValueError:
            continue
    return found


def suggest_contribution_percent_from_ocr(
    extracted_info: dict[str, Any] | None,
    *,
    faculty_name: str | None = None,
) -> dict[str, Any]:
    """
    Advisory OCR hint only — never used to auto-confirm or mutate bundle.contributionPercent.
    """
    if not isinstance(extracted_info, dict):
        return {
            "ocrSuggestedPercent": None,
            "ocrAmbiguous": False,
            "ocrNote": "No OCR text available for this Annex C file.",
        }
    parts: list[str] = []
    for key in ("OCR excerpt", "ocrExcerpt", "OCR text", "text"):
        val = extracted_info.get(key)
        if isinstance(val, str) and val.strip():
            parts.append(val)
    text = "\n".join(parts)
    if not text.strip():
        return {
            "ocrSuggestedPercent": None,
            "ocrAmbiguous": False,
            "ocrNote": "No OCR text available for this Annex C file.",
        }

    name = (faculty_name or "").strip()
    scoped = text
    if name:
        for line in text.splitlines():
            if name.lower() in line.lower():
                scoped = line
                break

    scoped_values = _percent_values_in_text(scoped)
    all_values = _percent_values_in_text(text)
    candidates = scoped_values if scoped_values else all_values
    unique = sorted(set(round(v, 4) for v in candidates))

    if len(unique) == 1:
        return {
            "ocrSuggestedPercent": unique[0],
            "ocrAmbiguous": False,
            "ocrNote": "OCR suggests one percentage — verify against the actual Annex C document.",
        }
    if len(unique) > 1:
        return {
            "ocrSuggestedPercent": None,
            "ocrAmbiguous": True,
            "ocrNote": "OCR found multiple percentages — confirm manually from the document.",
        }
    return {
        "ocrSuggestedPercent": None,
        "ocrAmbiguous": False,
        "ocrNote": "OCR did not detect a clear contribution percentage.",
    }


def effective_confirmation_status(
    bundle: dict[str, Any] | None,
    *,
    indicator_id: str,
) -> str:
    if not indicator_requires_contribution_percent(indicator_id):
        return STATUS_CONFIRMED

    record = _confirmation_record(bundle)
    if record and record.get("status"):
        return str(record["status"])

    if _has_completed_reviewer_assessment(bundle):
        return STATUS_LEGACY_GRANDFATHERED

    return STATUS_NOT_CONFIRMED


def build_contribution_verification_view(
    bundle: dict[str, Any] | None,
    *,
    indicator_id: str,
    annex_extracted_info: dict[str, Any] | None = None,
    faculty_name: str | None = None,
) -> dict[str, Any] | None:
    if not indicator_requires_contribution_percent(indicator_id):
        return None

    bundle = bundle if isinstance(bundle, dict) else {}
    recorded_raw = bundle.get("contributionPercent")
    recorded, err = validate_contribution_percent(recorded_raw)
    ocr = suggest_contribution_percent_from_ocr(annex_extracted_info, faculty_name=faculty_name)
    record = _confirmation_record(bundle) or {}
    status = effective_confirmation_status(bundle, indicator_id=indicator_id)

    confirmed = record.get("confirmedPercent")
    try:
        confirmed_f = float(confirmed) if confirmed is not None else None
    except (TypeError, ValueError):
        confirmed_f = None

    display_match = {
        STATUS_NOT_CONFIRMED: "Not Confirmed",
        STATUS_CONFIRMED: "Confirmed",
        STATUS_MISMATCH: "Mismatch",
        STATUS_NEEDS_CLARIFICATION: "Needs Clarification",
        STATUS_LEGACY_GRANDFATHERED: "Contribution Confirmation Required",
    }.get(status, "Not Confirmed")

    return {
        "recordedContributionPercent": recorded,
        "recordedContributionError": err,
        "ocrSuggestedPercent": ocr.get("ocrSuggestedPercent"),
        "ocrAmbiguous": ocr.get("ocrAmbiguous"),
        "ocrAdvisoryNote": ocr.get("ocrNote"),
        "confirmationStatus": status,
        "matchStatusLabel": display_match,
        "confirmedContributionPercent": confirmed_f,
        "confirmedAt": record.get("confirmedAt"),
        "confirmedByReviewerId": record.get("reviewerUserId"),
        "confirmedByReviewerName": record.get("reviewerDisplayName"),
        "clarificationReason": record.get("clarificationReason"),
        "legacyGrandfathered": status == STATUS_LEGACY_GRANDFATHERED,
        "requiresConfirmationBeforeNewAssessment": status
        in (STATUS_NOT_CONFIRMED, STATUS_MISMATCH, STATUS_NEEDS_CLARIFICATION),
    }


def apply_contribution_confirmation(
    bundle: dict[str, Any],
    *,
    reviewer_user_id: int,
    reviewer_display_name: str,
    confirmed_percent: float | int | str,
    clarification_reason: str = "",
) -> dict[str, Any]:
    """
    Reviewer confirms the recorded contribution % matches Annex C after document review.
    """
    recorded, rec_err = validate_contribution_percent(bundle.get("contributionPercent"))
    if rec_err:
        raise ValueError("contribution_percent_required_on_claim")

    pct, err = validate_contribution_percent(confirmed_percent)
    if err:
        raise ValueError("contribution_confirmation_percent_invalid")

    checklist = bundle.get("checklist") if isinstance(bundle.get("checklist"), dict) else {}
    annex = checklist.get(SLOT_ANNEX_C_CONTRIBUTION) if isinstance(checklist, dict) else {}
    if not isinstance(annex, dict) or not annex.get("documentId"):
        raise ValueError("annex_c_document_required")

    prior = _confirmation_record(bundle) or {}
    history = prior.get("history")
    if not isinstance(history, list):
        history = []
    if prior.get("status"):
        history.append(
            {
                "status": prior.get("status"),
                "confirmedPercent": prior.get("confirmedPercent"),
                "recordedPercent": prior.get("recordedPercent"),
                "updatedAt": prior.get("confirmedAt"),
                "reviewerUserId": prior.get("reviewerUserId"),
            }
        )
    history = history[-HISTORY_LIMIT:]

    if abs(float(pct) - float(recorded)) > MATCH_TOLERANCE:
        status = STATUS_MISMATCH
    else:
        status = STATUS_CONFIRMED

    reason = (clarification_reason or "").strip()
    if status == STATUS_MISMATCH and not reason:
        raise ValueError("contribution_mismatch_reason_required")

    record = {
        "status": status,
        "recordedPercent": float(recorded),
        "confirmedPercent": float(pct),
        "reviewerUserId": int(reviewer_user_id),
        "reviewerDisplayName": (reviewer_display_name or "").strip() or None,
        "confirmedAt": _utc_iso(),
        "clarificationReason": reason or None,
        "history": history,
    }
    bundle[BUNDLE_KEY] = record
    return record


def mark_needs_clarification(
    bundle: dict[str, Any],
    *,
    reviewer_user_id: int,
    reviewer_display_name: str,
    clarification_reason: str,
) -> dict[str, Any]:
    reason = (clarification_reason or "").strip()
    if len(reason) < 10:
        raise ValueError("contribution_clarification_reason_required")
    recorded, _ = validate_contribution_percent(bundle.get("contributionPercent"))
    record = {
        "status": STATUS_NEEDS_CLARIFICATION,
        "recordedPercent": float(recorded) if recorded is not None else None,
        "confirmedPercent": None,
        "reviewerUserId": int(reviewer_user_id),
        "reviewerDisplayName": (reviewer_display_name or "").strip() or None,
        "confirmedAt": _utc_iso(),
        "clarificationReason": reason,
        "history": (_confirmation_record(bundle) or {}).get("history") or [],
    }
    bundle[BUNDLE_KEY] = record
    return record


def _assessment_unchanged(bundle: dict[str, Any], points: float, justification: str) -> bool:
    prior = assessment_from_bundle(bundle) or {}
    try:
        prior_pts = round(float(prior.get("points")), 2) if prior.get("points") is not None else None
    except (TypeError, ValueError):
        prior_pts = None
    prior_just = (prior.get("justification") or "").strip()
    return prior_pts == round(float(points), 2) and prior_just == (justification or "").strip()


def assert_can_save_reviewer_assessment(
    bundle: dict[str, Any],
    *,
    indicator_id: str,
    points: float,
    justification: str,
) -> None:
    """Raise ValueError with stable code if collaborative assessment may not be saved."""
    if not indicator_requires_contribution_percent(indicator_id):
        return

    status = effective_confirmation_status(bundle, indicator_id=indicator_id)
    if status == STATUS_LEGACY_GRANDFATHERED:
        if _assessment_unchanged(bundle, points, justification):
            return
        raise ValueError("contribution_confirmation_required_for_assessment_change")

    if status == STATUS_CONFIRMED:
        record = _confirmation_record(bundle) or {}
        recorded, _ = validate_contribution_percent(bundle.get("contributionPercent"))
        confirmed = record.get("confirmedPercent")
        try:
            confirmed_f = float(confirmed) if confirmed is not None else None
        except (TypeError, ValueError):
            confirmed_f = None
        if recorded is None or confirmed_f is None:
            raise ValueError("contribution_confirmation_incomplete")
        if abs(recorded - confirmed_f) > MATCH_TOLERANCE:
            raise ValueError("contribution_percent_mismatch_unresolved")
        return

    if status == STATUS_MISMATCH:
        raise ValueError("contribution_percent_mismatch_unresolved")

    raise ValueError("contribution_confirmation_required")


def augment_validation_with_contribution_blockers(
    validation: dict[str, Any],
    bundle: dict[str, Any] | None,
    *,
    indicator_id: str,
) -> dict[str, Any]:
    """Add scoring blockers for missing contribution confirmation (non-destructive copy)."""
    out = dict(validation)
    if not indicator_requires_contribution_percent(indicator_id):
        return out

    status = effective_confirmation_status(bundle, indicator_id=indicator_id)
    flags = list(out.get("flags") or [])
    blockers = list(out.get("scoringBlockers") or [])
    if status not in (STATUS_CONFIRMED, STATUS_LEGACY_GRANDFATHERED):
        msg = contribution_scoring_blocker_message(bundle, indicator_id=indicator_id)
        if msg:
            flags.append("contribution_confirmation_pending")
            checklist = (bundle or {}).get("checklist") if isinstance(bundle, dict) else {}
            annex = checklist.get(SLOT_ANNEX_C_CONTRIBUTION) if isinstance(checklist, dict) else {}
            blockers.append(
                {
                    "code": "contribution_confirmation_pending",
                    "slotId": SLOT_ANNEX_C_CONTRIBUTION,
                    "label": "Annex C contribution",
                    "documentId": (annex or {}).get("documentId", "") if isinstance(annex, dict) else "",
                    "message": msg,
                    "reviewAction": "Confirm the contribution percentage against Annex C.",
                }
            )
    elif status == STATUS_LEGACY_GRANDFATHERED:
        flags.append("contribution_confirmation_legacy_grandfathered")
    out["flags"] = flags
    out["scoringBlockers"] = blockers
    return out


def contribution_scoring_blocker_message(bundle: dict[str, Any] | None, *, indicator_id: str) -> str | None:
    if not indicator_requires_contribution_percent(indicator_id):
        return None
    status = effective_confirmation_status(bundle, indicator_id=indicator_id)
    if status == STATUS_LEGACY_GRANDFATHERED:
        return (
            "Contribution confirmation is recommended for this historical assessment. "
            "Existing scores remain until you confirm the Annex C percentage."
        )
    if status == STATUS_CONFIRMED:
        return None
    if status == STATUS_MISMATCH:
        return (
            "The recorded contribution percentage does not match the reviewed Annex C. "
            "Resolve the difference before finalizing the assessment."
        )
    if status == STATUS_NEEDS_CLARIFICATION:
        return "Contribution percentage needs clarification before finalizing the assessment."
    return (
        "Confirm the contribution percentage against Annex C before finalizing "
        "a reviewer assessment."
    )
