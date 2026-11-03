"""Server-side instructional material bundle validation (reviewer-gated; OCR never certifies)."""

from __future__ import annotations

from typing import Any

from kra_configuration.criterion_b_scoring import validate_contribution_percent
from documents.criterion_b_evidence.bundle import (
    VALIDATION_INCOMPLETE,
    VALIDATION_INVALID,
    VALIDATION_REVIEWER_REQUIRED,
    VALIDATION_VALID,
    SLOT_STATUS_MISSING,
    SLOT_STATUS_PRESENT_UNVERIFIED,
    SLOT_STATUS_REVIEWER_REQUIRED,
    SLOT_STATUS_VERIFIED,
)
from documents.criterion_b_evidence.checklist import (
    SLOT_ANNEX_C_CONTRIBUTION,
    SLOT_ORIGINALITY_PROOF,
    SLOT_PEDAGOGICAL_VALIDITY,
    SLOT_IMDC_APPROVAL,
    SLOT_COMPLETE_SET,
    SLOT_PRIMARY_MATERIAL,
    required_slots,
    slot_label,
)


def validate_instructional_material_bundle(bundle: dict[str, Any] | None) -> dict[str, Any]:
    """
    Validate bundle metadata and checklist without assuming OCR or upload equals approval.

    Returns a summary dict suitable for API responses (no DB access).
    """
    flags: list[str] = []
    blockers: list[str] = []

    if not bundle or not isinstance(bundle, dict):
        return {
            "validationStatus": VALIDATION_INCOMPLETE,
            "flags": ["bundle_missing"],
            "blockers": ["Evidence bundle is not initialized."],
            "checklistSummary": {},
            "readyForReviewer": False,
            "readyForScoring": False,
            "scoringBlockers": [
                {
                    "code": "bundle_missing",
                    "slotId": "",
                    "label": "Evidence bundle",
                    "documentId": "",
                    "message": "Evidence bundle is not initialized.",
                    "reviewAction": "Ask the faculty member to complete their Criterion B claim setup.",
                }
            ],
        }

    material_type = (bundle.get("materialType") or "").strip()
    authorship = (bundle.get("authorship") or "sole").strip().lower()
    if not material_type:
        flags.append("material_type_missing")

    title = (bundle.get("materialTitle") or "").strip()
    if not title:
        flags.append("material_title_missing")
        blockers.append("Instructional material title is required.")

    slots_required = required_slots(material_type, authorship=authorship)
    checklist = bundle.get("checklist") if isinstance(bundle.get("checklist"), dict) else {}
    checklist_summary: dict[str, str] = {}

    for slot in slots_required:
        entry = checklist.get(slot) if isinstance(checklist.get(slot), dict) else {}
        status = (entry.get("status") or SLOT_STATUS_MISSING).strip()
        doc_id = entry.get("documentId")
        if not doc_id or status == SLOT_STATUS_MISSING:
            checklist_summary[slot] = SLOT_STATUS_MISSING
            flags.append(f"missing_{slot}")
            continue
        if status == SLOT_STATUS_VERIFIED:
            checklist_summary[slot] = SLOT_STATUS_VERIFIED
        elif status in (SLOT_STATUS_PRESENT_UNVERIFIED, SLOT_STATUS_REVIEWER_REQUIRED):
            checklist_summary[slot] = SLOT_STATUS_REVIEWER_REQUIRED
            flags.append(f"reviewer_required_{slot}")
        else:
            checklist_summary[slot] = status

    if authorship == "co":
        pct = bundle.get("contributionPercent")
        parsed, err = validate_contribution_percent(pct)
        if err:
            flags.append(err)
            blockers.append("Co-author contribution percentage is required (0–100).")
        annex = checklist.get(SLOT_ANNEX_C_CONTRIBUTION) or {}
        if not annex.get("documentId"):
            flags.append("missing_annex_c_contribution")
    else:
        parsed = None

    complete = bundle.get("completeSetDeclared")
    if material_type in ("module", "instructional_manual"):
        if complete is not True:
            flags.append("complete_set_not_attested")
            blockers.append(
                "Stand-alone or complete set attestation is required for modules and manuals (§13)."
            )

    spec = bundle.get("specializationAligned")
    if spec is None:
        flags.append("specialization_alignment_pending")
    elif spec is False:
        flags.append("specialization_not_aligned")
        blockers.append("Contribution must align with the faculty member's field of specialization.")

    originality_verified = _slot_verified(checklist, SLOT_ORIGINALITY_PROOF)
    pedagogical_verified = _slot_verified(checklist, SLOT_PEDAGOGICAL_VALIDITY)
    if material_type == "multimedia":
        if not originality_verified:
            flags.append("multimedia_originality_reviewer_required")
        if not pedagogical_verified:
            flags.append("multimedia_pedagogical_reviewer_required")

    imdc_verified = _slot_verified(checklist, SLOT_IMDC_APPROVAL)
    if not imdc_verified:
        flags.append("imdc_approval_reviewer_required")

    has_missing = any(v == SLOT_STATUS_MISSING for v in checklist_summary.values())
    hard_invalid_flags = {
        "specialization_not_aligned",
        "contribution_percent_invalid",
        "contribution_percent_out_of_range",
    }
    if any(f in hard_invalid_flags for f in flags):
        status = VALIDATION_INVALID
    elif has_missing or blockers:
        status = VALIDATION_INCOMPLETE
    elif flags:
        status = VALIDATION_REVIEWER_REQUIRED
    else:
        status = VALIDATION_VALID

    # Never auto-valid from OCR-only present files
    if status == VALIDATION_VALID:
        for slot, st in checklist_summary.items():
            if st != SLOT_STATUS_VERIFIED:
                status = VALIDATION_REVIEWER_REQUIRED
                flags.append("checklist_not_fully_verified")
                break

    ready_for_reviewer = not has_missing and title != ""
    if authorship == "co":
        ready_for_scoring = status == VALIDATION_VALID and parsed is not None
    else:
        ready_for_scoring = status == VALIDATION_VALID

    scoring_blockers = _build_scoring_blockers(
        bundle,
        checklist=checklist,
        checklist_summary=checklist_summary,
        blockers=blockers,
        flags=flags,
        authorship=authorship,
        contribution_parsed=parsed,
        material_type=material_type,
    )

    return {
        "validationStatus": status,
        "flags": flags,
        "blockers": blockers,
        "checklistSummary": checklist_summary,
        "readyForReviewer": ready_for_reviewer,
        "readyForScoring": ready_for_scoring,
        "contributionPercent": parsed,
        "scoringBlockers": scoring_blockers,
    }


def _build_scoring_blockers(
    bundle: dict[str, Any],
    *,
    checklist: dict[str, Any],
    checklist_summary: dict[str, str],
    blockers: list[str],
    flags: list[str],
    authorship: str,
    contribution_parsed: float | None,
    material_type: str,
) -> list[dict[str, str]]:
    """Human-readable reasons official reviewer-assessed scoring cannot finalize yet."""
    items: list[dict[str, str]] = []

    primary_entry = checklist.get(SLOT_PRIMARY_MATERIAL)
    if isinstance(primary_entry, dict) and primary_entry.get("documentId"):
        if primary_entry.get("status") != SLOT_STATUS_VERIFIED:
            label = slot_label(SLOT_PRIMARY_MATERIAL)
            items.append(
                {
                    "code": "unverified_primary_material",
                    "slotId": SLOT_PRIMARY_MATERIAL,
                    "label": label,
                    "documentId": str(primary_entry.get("documentId") or ""),
                    "message": f"{label} is uploaded but not verified by you yet.",
                    "reviewAction": "Open the main instructional file and choose “Yes, accept this file” when it meets the requirement.",
                }
            )

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
                    "documentId": doc_id or "",
                    "message": f"{label} has not been uploaded yet.",
                    "reviewAction": "Ask the faculty member to upload this document.",
                }
            )
            continue
        if summary_status != SLOT_STATUS_VERIFIED:
            if entry.get("status") == SLOT_STATUS_REVIEWER_REQUIRED:
                msg = f"{label} needs correction from the faculty member."
                action = "Return to the file step and explain what must change, or accept a replacement upload."
            else:
                msg = f"{label} is uploaded but not verified by you yet."
                action = "Open this document in step 1 and choose “Yes, accept this file” when it meets the requirement."
            items.append(
                {
                    "code": f"unverified_{slot}",
                    "slotId": slot,
                    "label": label,
                    "documentId": doc_id,
                    "message": msg,
                    "reviewAction": action,
                }
            )

    spec = bundle.get("specializationAligned")
    if spec is None:
        items.append(
            {
                "code": "specialization_alignment_pending",
                "slotId": "",
                "label": "Field of specialization",
                "documentId": "",
                "message": "You have not confirmed whether this work aligns with the faculty member's specialization.",
                "reviewAction": "Confirm specialization alignment before finishing the assessment score.",
            }
        )
    elif spec is False:
        items.append(
            {
                "code": "specialization_not_aligned",
                "slotId": "",
                "label": "Field of specialization",
                "documentId": "",
                "message": "This contribution is marked as not aligned with the faculty member's specialization.",
                "reviewAction": "Do not finalize points until alignment is resolved or the claim is withdrawn.",
            }
        )

    if material_type in ("module", "instructional_manual") and bundle.get("completeSetDeclared") is not True:
        items.append(
            {
                "code": "complete_set_not_attested",
                "slotId": SLOT_COMPLETE_SET,
                "label": "Complete set attestation",
                "documentId": "",
                "message": "Stand-alone or complete set attestation is still required for this module or manual.",
                "reviewAction": "Ask the faculty member to confirm complete set attestation on their claim.",
            }
        )

    if authorship == "co" and contribution_parsed is None:
        items.append(
            {
                "code": "contribution_percent_required",
                "slotId": "",
                "label": "Co-author contribution",
                "documentId": "",
                "message": "Co-author contribution percentage (0–100) is not recorded on this claim.",
                "reviewAction": "Ask the faculty member to enter their Annex C contribution percentage.",
            }
        )

    for text in blockers:
        if any(text in item.get("message", "") for item in items):
            continue
        items.append(
            {
                "code": "blocker",
                "slotId": "",
                "label": "Requirement",
                "documentId": "",
                "message": text,
                "reviewAction": "Resolve this requirement before finalizing the assessment score.",
            }
        )

    return items


def _slot_verified(checklist: dict[str, Any], slot: str) -> bool:
    entry = checklist.get(slot)
    if not isinstance(entry, dict):
        return False
    return entry.get("status") == SLOT_STATUS_VERIFIED and bool(entry.get("documentId"))


def detect_duplicate_supporting_hash(
    bundle: dict[str, Any],
    *,
    slot_id: str,
    file_hash: str | None,
) -> bool:
    """True if this hash is already linked to the same slot on this bundle."""
    if not file_hash:
        return False
    checklist = bundle.get("checklist") if isinstance(bundle.get("checklist"), dict) else {}
    entry = checklist.get(slot_id)
    if isinstance(entry, dict) and entry.get("fileHash") == file_hash:
        return True
    return False


def detect_cross_claim_hash_conflict(
    *,
    primary_public_id: str,
    primary_hash: str | None,
    other_bundles: list[dict[str, Any]],
    candidate_hash: str | None,
) -> bool:
    """
    Prevent using the same file hash as a primary material on another active claim.
    """
    if not candidate_hash:
        return False
    for bundle in other_bundles:
        if not isinstance(bundle, dict):
            continue
        primary = (bundle.get("checklist") or {}).get("primary_material") or {}
        if primary.get("fileHash") == candidate_hash:
            owner = primary.get("documentId")
            if owner and owner != primary_public_id:
                return True
    if primary_hash and candidate_hash == primary_hash:
        return False
    return False
