"""Academic program bundle validation (reviewer-gated; OCR hints only)."""

from __future__ import annotations

from typing import Any

from kra_configuration.criterion_b_annex import faculty_role_for_program_indicator
from documents.criterion_b_evidence.bundle import (
    SLOT_STATUS_MISSING,
    SLOT_STATUS_NOT_APPLICABLE,
    SLOT_STATUS_PRESENT_UNVERIFIED,
    SLOT_STATUS_REVIEWER_REQUIRED,
    SLOT_STATUS_VERIFIED,
    VALIDATION_INCOMPLETE,
    VALIDATION_INVALID,
    VALIDATION_REVIEWER_REQUIRED,
    VALIDATION_VALID,
)
from documents.criterion_b_evidence.program_applicability import (
    RRPA_APPLICABILITY_APPLICABLE,
    RRPA_APPLICABILITY_NOT_APPLICABLE,
    RRPA_APPLICABILITY_UNKNOWN,
    rrpa_copc_applicability_from_bundle,
    rrpa_copc_applicability_note_from_bundle,
)
from documents.criterion_b_evidence.program_checklist import (
    DEVELOPMENT_STUDY_SLOTS,
    MANDATORY_APPROVAL_SLOTS,
    OPTIONAL_REVIEWER_SLOTS,
    PROGRAM_KIND_NEW,
    PROGRAM_KIND_REVISION,
    SLOT_DEAN_CERTIFICATION,
    SLOT_PRIMARY_CONTRIBUTION,
    SLOT_REVISED_CURRICULUM,
    SLOT_RRPA_COPC,
)


def _slot_entry(checklist: dict[str, Any], slot_id: str) -> dict[str, Any]:
    entry = checklist.get(slot_id)
    return entry if isinstance(entry, dict) else {}


def _has_linked_document(entry: dict[str, Any]) -> bool:
    return bool(entry.get("documentId"))


def _slot_status(checklist: dict[str, Any], slot_id: str) -> str:
    entry = _slot_entry(checklist, slot_id)
    if not _has_linked_document(entry):
        return SLOT_STATUS_MISSING
    return (entry.get("status") or SLOT_STATUS_PRESENT_UNVERIFIED).strip()


def _any_group_satisfied(checklist: dict[str, Any], slots: tuple[str, ...]) -> bool:
    return any(_has_linked_document(_slot_entry(checklist, s)) for s in slots)


def validate_academic_program_bundle(bundle: dict[str, Any] | None) -> dict[str, Any]:
    flags: list[str] = []
    blockers: list[str] = []
    checklist_summary: dict[str, str] = {}

    if not bundle or not isinstance(bundle, dict):
        return {
            "validationStatus": VALIDATION_INCOMPLETE,
            "flags": ["bundle_missing"],
            "blockers": ["Evidence bundle is not initialized."],
            "checklistSummary": {},
            "readyForReviewer": False,
            "readyForScoring": False,
        }

    if bundle.get("reviewerDisqualificationConfirmed") is True:
        return {
            "validationStatus": VALIDATION_INVALID,
            "flags": ["reviewer_disqualification_confirmed"],
            "blockers": ["Reviewer confirmed this claim is not eligible."],
            "checklistSummary": {},
            "readyForReviewer": False,
            "readyForScoring": False,
        }

    indicator_id = (bundle.get("indicatorId") or "").strip()
    expected_role = faculty_role_for_program_indicator(indicator_id)
    faculty_role = (bundle.get("facultyRole") or "").strip().lower()
    if expected_role and faculty_role and faculty_role != expected_role:
        flags.append("role_indicator_mismatch")
        blockers.append("Claimed faculty role does not match the selected indicator.")

    program_name = (bundle.get("programName") or "").strip()
    if not program_name:
        flags.append("program_name_missing")
        blockers.append("Academic program name is required.")

    description = (bundle.get("contributionDescription") or "").strip()
    if not description:
        flags.append("contribution_description_missing")

    kind = (bundle.get("programDevelopmentKind") or "").strip()
    if kind not in (PROGRAM_KIND_NEW, PROGRAM_KIND_REVISION):
        flags.append("program_development_kind_pending")

    checklist = bundle.get("checklist") if isinstance(bundle.get("checklist"), dict) else {}

    for slot in MANDATORY_APPROVAL_SLOTS:
        st = _slot_status(checklist, slot)
        checklist_summary[slot] = st
        if st == SLOT_STATUS_MISSING:
            flags.append(f"missing_{slot}")

    primary = _slot_entry(checklist, SLOT_PRIMARY_CONTRIBUTION)
    if not _has_linked_document(primary):
        flags.append("missing_primary_contribution")
        checklist_summary[SLOT_PRIMARY_CONTRIBUTION] = SLOT_STATUS_MISSING
    else:
        checklist_summary[SLOT_PRIMARY_CONTRIBUTION] = _slot_status(checklist, SLOT_PRIMARY_CONTRIBUTION)

    if kind == PROGRAM_KIND_NEW:
        if not _any_group_satisfied(checklist, DEVELOPMENT_STUDY_SLOTS):
            flags.append("development_study_required")
        for slot in DEVELOPMENT_STUDY_SLOTS:
            if slot not in checklist_summary:
                checklist_summary[slot] = _slot_status(checklist, slot)
    elif kind == PROGRAM_KIND_REVISION:
        st = _slot_status(checklist, SLOT_REVISED_CURRICULUM)
        checklist_summary[SLOT_REVISED_CURRICULUM] = st
        if st == SLOT_STATUS_MISSING:
            flags.append("revised_curriculum_consultation_required")
    else:
        for slot in DEVELOPMENT_STUDY_SLOTS + (SLOT_REVISED_CURRICULUM,):
            checklist_summary[slot] = _slot_status(checklist, slot)

    for slot in OPTIONAL_REVIEWER_SLOTS:
        st = _slot_status(checklist, slot)
        checklist_summary[slot] = st
        if st in (SLOT_STATUS_PRESENT_UNVERIFIED, SLOT_STATUS_REVIEWER_REQUIRED):
            flags.append(f"optional_{slot}_reviewer_required")

    rrpa_applicability = rrpa_copc_applicability_from_bundle(bundle)
    rrpa_applicability_note = rrpa_copc_applicability_note_from_bundle(bundle)
    rrpa_st = _slot_status(checklist, SLOT_RRPA_COPC)
    checklist_summary[SLOT_RRPA_COPC] = rrpa_st

    if rrpa_applicability == RRPA_APPLICABILITY_UNKNOWN:
        flags.append("rrpa_copc_applicability_undetermined")
    elif rrpa_applicability == RRPA_APPLICABILITY_APPLICABLE:
        if rrpa_st == SLOT_STATUS_MISSING:
            flags.append("missing_rrpa_or_copc")
        elif rrpa_st != SLOT_STATUS_VERIFIED:
            flags.append("rrpa_or_copc_reviewer_required")
    elif rrpa_applicability == RRPA_APPLICABILITY_NOT_APPLICABLE:
        decision = bundle.get("rrpaCopcApplicabilityDecision")
        decided_by = (
            decision.get("decidedByRole") if isinstance(decision, dict) else None
        )
        if not rrpa_applicability_note or decided_by != "reviewer":
            flags.append("rrpa_copc_exemption_not_documented")
        elif rrpa_st == SLOT_STATUS_MISSING:
            checklist_summary[SLOT_RRPA_COPC] = SLOT_STATUS_NOT_APPLICABLE

    approval_verified = all(
        _slot_status(checklist, slot) == SLOT_STATUS_VERIFIED for slot in MANDATORY_APPROVAL_SLOTS
    )
    primary_verified = _slot_status(checklist, SLOT_PRIMARY_CONTRIBUTION) == SLOT_STATUS_VERIFIED
    dean_verified = _slot_status(checklist, SLOT_DEAN_CERTIFICATION) == SLOT_STATUS_VERIFIED

    if _has_linked_document(_slot_entry(checklist, SLOT_DEAN_CERTIFICATION)) and not dean_verified:
        flags.append("dean_certification_reviewer_required")

    has_missing_mandatory = any(
        checklist_summary.get(s) == SLOT_STATUS_MISSING for s in MANDATORY_APPROVAL_SLOTS
    ) or checklist_summary.get(SLOT_PRIMARY_CONTRIBUTION) == SLOT_STATUS_MISSING
    if rrpa_applicability == RRPA_APPLICABILITY_APPLICABLE and rrpa_st == SLOT_STATUS_MISSING:
        has_missing_mandatory = True

    hard_invalid_flags = {"role_indicator_mismatch", "reviewer_disqualification_confirmed"}
    if any(f in hard_invalid_flags for f in flags):
        status = VALIDATION_INVALID
    elif has_missing_mandatory or "contribution_description_missing" in flags or blockers:
        status = VALIDATION_INCOMPLETE
    elif kind == PROGRAM_KIND_NEW and "development_study_required" in flags:
        status = VALIDATION_INCOMPLETE
    elif kind == PROGRAM_KIND_REVISION and "revised_curriculum_consultation_required" in flags:
        status = VALIDATION_INCOMPLETE
    elif "program_development_kind_pending" in flags:
        status = VALIDATION_INCOMPLETE
    elif "missing_rrpa_or_copc" in flags:
        status = VALIDATION_INCOMPLETE
    elif flags:
        status = VALIDATION_REVIEWER_REQUIRED
    else:
        status = VALIDATION_VALID

    if status == VALIDATION_VALID and not (approval_verified and primary_verified):
        status = VALIDATION_REVIEWER_REQUIRED
        flags.append("checklist_not_fully_verified")

    ready_for_reviewer = bool(program_name and description and not has_missing_mandatory)
    rrpa_ready = False
    if rrpa_applicability == RRPA_APPLICABILITY_UNKNOWN:
        rrpa_ready = False
    elif rrpa_applicability == RRPA_APPLICABILITY_NOT_APPLICABLE:
        decision = bundle.get("rrpaCopcApplicabilityDecision")
        decided_by = (
            decision.get("decidedByRole") if isinstance(decision, dict) else None
        )
        rrpa_ready = bool(rrpa_applicability_note) and decided_by == "reviewer"
    else:
        rrpa_ready = rrpa_st == SLOT_STATUS_VERIFIED

    ready_for_scoring = (
        status == VALIDATION_VALID and approval_verified and primary_verified and rrpa_ready
    )

    return {
        "validationStatus": status,
        "flags": flags,
        "blockers": blockers,
        "checklistSummary": checklist_summary,
        "readyForReviewer": ready_for_reviewer,
        "readyForScoring": ready_for_scoring,
        "rrpaCopcApplicability": rrpa_applicability,
        "rrpaCopcApplicabilityNote": rrpa_applicability_note,
    }
