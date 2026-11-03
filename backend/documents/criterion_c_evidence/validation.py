"""Criterion C bundle validation (reviewer-gated; OCR never certifies eligibility)."""

from __future__ import annotations

from typing import Any

from documents.criterion_c_evidence.bundle import (
    REVIEW_APPROVED,
    REVIEW_REJECTED,
    SLOT_STATUS_MISSING,
    SLOT_STATUS_VERIFIED,
    VALIDATION_INCOMPLETE,
    VALIDATION_INVALID,
    VALIDATION_REVIEWER_REQUIRED,
    VALIDATION_VALID,
)
from documents.criterion_c_evidence.checklist import required_slots, slot_label


def validate_criterion_c_bundle(bundle: dict[str, Any] | None) -> dict[str, Any]:
    flags: list[str] = []
    blockers: list[str] = []
    if not isinstance(bundle, dict):
        return _empty_validation("bundle_missing", "Evidence bundle is not initialized.")

    service_category = (bundle.get("serviceCategory") or "research").strip().lower()
    title = (bundle.get("projectTitle") or "").strip()
    if not title:
        flags.append("project_title_missing")
        blockers.append("Project or thesis title is required.")

    if service_category == "research":
        if not (bundle.get("studentNames") or "").strip():
            flags.append("student_names_missing")
            blockers.append("Student name(s) are required for research-related services.")
        if not (bundle.get("completionDate") or "").strip():
            flags.append("completion_date_missing")
            blockers.append("Completion or approval date is required.")
    else:
        ment = bundle.get("mentorship") if isinstance(bundle.get("mentorship"), dict) else {}
        if not (ment.get("competitionName") or "").strip():
            flags.append("competition_name_missing")
            blockers.append("Competition or award name is required for mentorship.")

    checklist = bundle.get("checklist") if isinstance(bundle.get("checklist"), dict) else {}
    checklist_summary: dict[str, str] = {}
    for slot in required_slots(service_category=service_category):
        entry = checklist.get(slot) if isinstance(checklist.get(slot), dict) else {}
        status = (entry.get("status") or SLOT_STATUS_MISSING).strip()
        doc_id = entry.get("documentId")
        if not doc_id or status == SLOT_STATUS_MISSING:
            checklist_summary[slot] = SLOT_STATUS_MISSING
            flags.append(f"missing_{slot}")
            continue
        if status == SLOT_STATUS_VERIFIED:
            checklist_summary[slot] = SLOT_STATUS_VERIFIED
        else:
            checklist_summary[slot] = "reviewer_required"
            flags.append(f"reviewer_required_{slot}")

    if "duplicate_service_suspected" in (bundle.get("duplicateFlags") or []):
        flags.append("duplicate_service_suspected")
        blockers.append("This service may duplicate another accomplishment. Resolve before approval.")

    if "adviser_panel_same_thesis_review" in (bundle.get("policyFlags") or []):
        flags.append("adviser_panel_same_thesis_review")
        blockers.append(
            "Adviser and panel roles on the same thesis require policy review before both may be approved."
        )

    review_status = (bundle.get("reviewStatus") or "").strip().lower()
    if review_status == REVIEW_REJECTED:
        flags.append("review_rejected")
        status = VALIDATION_INVALID
    elif blockers or any(v == SLOT_STATUS_MISSING for v in checklist_summary.values()):
        status = VALIDATION_INCOMPLETE
    elif flags:
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

    scoring_blockers = _scoring_blockers(
        bundle,
        checklist=checklist,
        checklist_summary=checklist_summary,
        blockers=blockers,
        flags=flags,
        service_category=service_category,
    )

    return {
        "validationStatus": status,
        "flags": flags,
        "blockers": blockers,
        "checklistSummary": checklist_summary,
        "readyForReviewer": not blockers,
        "readyForScoring": ready_for_scoring,
        "scoringBlockers": scoring_blockers,
        "reviewStatus": review_status or "pending",
    }


def _empty_validation(code: str, message: str) -> dict[str, Any]:
    return {
        "validationStatus": VALIDATION_INCOMPLETE,
        "flags": [code],
        "blockers": [message],
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
                "reviewAction": "Initialize the Criterion C accomplishment.",
            }
        ],
        "reviewStatus": "pending",
    }


def _scoring_blockers(
    bundle: dict[str, Any],
    *,
    checklist: dict[str, Any],
    checklist_summary: dict[str, str],
    blockers: list[str],
    flags: list[str],
    service_category: str,
) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for slot, summary_status in checklist_summary.items():
        label = slot_label(slot)
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
                    "reviewAction": "Upload and link the required evidence.",
                }
            )
        elif summary_status != SLOT_STATUS_VERIFIED:
            items.append(
                {
                    "code": f"unverified_{slot}",
                    "slotId": slot,
                    "label": label,
                    "documentId": doc_id,
                    "message": f"{label} is uploaded but not verified by the reviewer.",
                    "reviewAction": "Verify this evidence before approving the accomplishment.",
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
    if (bundle.get("reviewStatus") or "") != REVIEW_APPROVED:
        items.append(
            {
                "code": "accomplishment_not_approved",
                "slotId": "",
                "label": "Reviewer decision",
                "documentId": "",
                "message": "This accomplishment has not been approved by a reviewer.",
                "reviewAction": "Complete evidence verification and approve or reject.",
            }
        )
    return items
