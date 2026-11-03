"""KRA II bundle validation (indicator-driven; reviewer-gated)."""

from __future__ import annotations

from typing import Any

from kra_configuration.kra2_indicator_registry import metadata_field_ids
from documents.kra2_evidence.bundle import (
    REVIEW_APPROVED,
    REVIEW_REJECTED,
    SLOT_STATUS_MISSING,
    SLOT_STATUS_VERIFIED,
    VALIDATION_INCOMPLETE,
    VALIDATION_INVALID,
    VALIDATION_REVIEWER_REQUIRED,
    VALIDATION_VALID,
)
from documents.kra2_evidence.slots import required_slots, slot_label
from documents.kra2_evidence.user_messages import message_for_field


def _field_value(bundle: dict[str, Any], field_id: str) -> str:
    if field_id == "outputVenue":
        return (bundle.get("outputVenue") or bundle.get("journalTitle") or "").strip()
    if field_id == "journalTitle":
        return _field_value(bundle, "outputVenue")
    raw = bundle.get(field_id)
    if raw is None:
        return ""
    return str(raw).strip()


def validate_kra2_bundle(bundle: dict[str, Any] | None, *, indicator_id: str) -> dict[str, Any]:
    flags: list[str] = []
    submission_blockers: list[str] = []
    reviewer_blockers: list[str] = []
    user_blockers: list[str] = []
    if not isinstance(bundle, dict):
        return _empty_validation("bundle_missing", "This accomplishment is not set up yet.")

    ind = (indicator_id or bundle.get("indicatorId") or "").strip()

    for field_id in metadata_field_ids(ind):
        if field_id == "declaredContributionPercent":
            if (bundle.get("contribution") or "").strip().lower() != "declared":
                continue
            raw_pct = bundle.get("declaredContributionPercent")
            try:
                pct = float(raw_pct) if raw_pct is not None else None
            except (TypeError, ValueError):
                pct = None
            if pct is None or pct <= 0 or pct > 100:
                flags.append("contribution_percent_invalid")
                msg = message_for_field("declaredContributionPercent")
                submission_blockers.append(msg)
            continue
        if not _field_value(bundle, field_id):
            flags.append(f"missing_{field_id}")
            msg = message_for_field(field_id)
            submission_blockers.append(msg)

    confirmed = bundle.get("metadataConfirmed") if isinstance(bundle.get("metadataConfirmed"), dict) else {}
    if not bundle.get("submittedForReviewAt"):
        flags.append("not_submitted")
    elif not all(confirmed.get(k) for k in metadata_field_ids(ind) if k != "declaredContributionPercent"):
        flags.append("metadata_not_confirmed")
        reviewer_blockers.append(message_for_field("metadata_not_confirmed"))

    if "duplicate_output_suspected" in (bundle.get("duplicateFlags") or []):
        flags.append("duplicate_output_suspected")
        msg = "This accomplishment may already have been submitted."
        submission_blockers.append(msg)

    patent_flags = bundle.get("duplicateFlags") or []
    if "patent_lower_stage_superseded" in patent_flags:
        flags.append("patent_lower_stage_superseded")
        user_blockers.append(
            "A higher patent stage for this invention is already on file. Only the highest stage is credited."
        )
    if "patent_higher_stage_exists_peer" in patent_flags:
        flags.append("patent_higher_stage_exists_peer")
        user_blockers.append(
            "Another submission shows a higher patent stage for the same invention. Reviewers will apply highest-stage scoring."
        )

    checklist = bundle.get("checklist") if isinstance(bundle.get("checklist"), dict) else {}
    checklist_summary: dict[str, str] = {}
    for slot in required_slots(indicator_id=ind):
        entry = checklist.get(slot) if isinstance(checklist.get(slot), dict) else {}
        status = (entry.get("status") or SLOT_STATUS_MISSING).strip()
        doc_id = entry.get("documentId")
        if not doc_id or status == SLOT_STATUS_MISSING:
            checklist_summary[slot] = SLOT_STATUS_MISSING
            flags.append(f"missing_{slot}")
            msg = f"Please upload: {slot_label(slot, indicator_id=ind)}."
            submission_blockers.append(msg)
            continue
        if status == SLOT_STATUS_VERIFIED:
            checklist_summary[slot] = SLOT_STATUS_VERIFIED
        else:
            checklist_summary[slot] = "reviewer_required"
            flags.append(f"reviewer_required_{slot}")
            slot_msg = f"Verify supporting evidence: {slot_label(slot, indicator_id=ind)}."
            reviewer_blockers.append(slot_msg)

    review_status = (bundle.get("reviewStatus") or "").strip().lower()
    if review_status == REVIEW_REJECTED:
        flags.append("review_rejected")
        status = VALIDATION_INVALID
    elif submission_blockers or any(v == SLOT_STATUS_MISSING for v in checklist_summary.values()):
        status = VALIDATION_INCOMPLETE
    elif flags or reviewer_blockers:
        status = VALIDATION_REVIEWER_REQUIRED
    else:
        status = VALIDATION_VALID

    if status == VALIDATION_VALID:
        for st in checklist_summary.values():
            if st != SLOT_STATUS_VERIFIED:
                status = VALIDATION_REVIEWER_REQUIRED
                flags.append("checklist_not_fully_verified")
                break
        if review_status != REVIEW_APPROVED:
            status = VALIDATION_REVIEWER_REQUIRED
            flags.append("reviewer_accomplishment_not_approved")

    ready_for_scoring = status == VALIDATION_VALID and review_status == REVIEW_APPROVED

    blockers = list(submission_blockers)
    user_blockers = list(submission_blockers)

    approval_blockers: list[str] = []
    seen_blocker: set[str] = set()
    for msg in submission_blockers + reviewer_blockers:
        text = (msg or "").strip()
        if text and text not in seen_blocker:
            seen_blocker.add(text)
            approval_blockers.append(text)

    ready_for_submission = len(submission_blockers) == 0

    return {
        "validationStatus": status,
        "flags": flags,
        "blockers": blockers,
        "submissionBlockers": list(submission_blockers),
        "reviewerBlockers": list(reviewer_blockers),
        "userBlockers": user_blockers,
        "approvalBlockers": approval_blockers,
        "checklistSummary": checklist_summary,
        "readyForSubmission": ready_for_submission,
        "readyForReviewer": ready_for_submission and bool(bundle.get("submittedForReviewAt")),
        "readyForApproval": not approval_blockers
        and all(v == SLOT_STATUS_VERIFIED for v in checklist_summary.values())
        and bool(bundle.get("submittedForReviewAt")),
        "readyForScoring": ready_for_scoring,
        "scoringBlockers": _scoring_blockers(
            bundle,
            checklist=checklist,
            checklist_summary=checklist_summary,
            blockers=submission_blockers + reviewer_blockers,
            review_status=review_status,
            indicator_id=ind,
        ),
        "reviewStatus": review_status or "pending",
    }


def _empty_validation(code: str, message: str) -> dict[str, Any]:
    return {
        "validationStatus": VALIDATION_INCOMPLETE,
        "flags": [code],
        "blockers": [message],
        "userBlockers": [message],
        "checklistSummary": {},
        "readyForReviewer": False,
        "readyForScoring": False,
        "scoringBlockers": [
            {
                "code": code,
                "slotId": "",
                "label": "Evidence bundle",
                "documentId": "",
                "message": message,
                "reviewAction": "Start a new accomplishment from the KRA II menu.",
            }
        ],
        "reviewStatus": "pending",
        "approvalBlockers": [message],
        "readyForApproval": False,
        "submissionBlockers": [message],
        "reviewerBlockers": [],
        "readyForSubmission": False,
    }


def _scoring_blockers(
    bundle: dict[str, Any],
    *,
    checklist: dict[str, Any],
    checklist_summary: dict[str, str],
    blockers: list[str],
    review_status: str,
    indicator_id: str,
) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for slot, summary_status in checklist_summary.items():
        label = slot_label(slot, indicator_id=indicator_id)
        entry = checklist.get(slot) if isinstance(checklist.get(slot), dict) else {}
        doc_id = (entry.get("documentId") or "").strip()
        if summary_status == SLOT_STATUS_MISSING or not doc_id:
            items.append(
                {
                    "code": f"missing_{slot}",
                    "slotId": slot,
                    "label": label,
                    "documentId": "",
                    "message": f"{label} is still required.",
                    "reviewAction": "Ask the faculty member to upload this document.",
                }
            )
        elif summary_status != SLOT_STATUS_VERIFIED:
            items.append(
                {
                    "code": f"unverified_{slot}",
                    "slotId": slot,
                    "label": label,
                    "documentId": doc_id,
                    "message": f"{label} is uploaded but not verified.",
                    "reviewAction": "Verify this document before approving.",
                }
            )
    for text in blockers:
        if any(text in i.get("message", "") for i in items):
            continue
        items.append(
            {
                "code": "blocker",
                "slotId": "",
                "label": "Requirement",
                "documentId": "",
                "message": text,
                "reviewAction": "Resolve before approving.",
            }
        )
    if review_status != REVIEW_APPROVED:
        items.append(
            {
                "code": "accomplishment_not_approved",
                "slotId": "",
                "label": "Reviewer decision",
                "documentId": "",
                "message": "This accomplishment has not been approved yet.",
                "reviewAction": "Complete verification and approve or reject.",
            }
        )
    return items
