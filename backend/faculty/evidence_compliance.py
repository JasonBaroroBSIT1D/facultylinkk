"""Unified evidence compliance (SET/SEF semester records vs document workflow)."""

from __future__ import annotations

from typing import Any

from models import Document, FacultyProfile

from documents.set_sef_parent_context import set_sef_parent_context
from documents.status_map import document_status_to_web

_PARENT_PENDING = frozenset(
    {"pending_review", "reviewer_required", "pending-review", "reviewer-required", "draft"}
)
_PARENT_APPROVED = frozenset({"approved", "valid", "system-approved"})


def _child_totals(teaching_summary: dict[str, Any]) -> dict[str, int]:
    workspace = teaching_summary.get("criterionAWorkspace") or {}
    child = (workspace.get("totals") or {}).get("childValidation") or {}
    keys = ("total", "validated", "pending", "needsRevision", "rejected", "incomplete")
    return {k: int(child.get(k) or 0) for k in keys}


def _document_workflow_counts(profile: FacultyProfile) -> dict[str, int]:
    pending = 0
    approved = 0
    set_sef_parent_pdfs = 0
    other_submitted = 0
    other_approved = 0

    rows = (
        Document.query.filter_by(faculty_profile_id=profile.id)
        .filter(Document.deleted_at.is_(None))
        .all()
    )
    for doc in rows:
        ctx = set_sef_parent_context(doc)
        child_total = int((ctx or {}).get("allChildValidationSummary", {}).get("total") or 0)
        is_set_sef_parent = child_total > 0 or doc.criterion_id == "kra1-a"
        workflow = document_status_to_web(doc)

        if is_set_sef_parent:
            set_sef_parent_pdfs += 1
            if workflow in _PARENT_APPROVED:
                approved += 1
            elif workflow in _PARENT_PENDING or workflow not in _PARENT_APPROVED:
                pending += 1
        else:
            other_submitted += 1
            if workflow in _PARENT_APPROVED:
                other_approved += 1

    return {
        "setSefParentPdfCount": set_sef_parent_pdfs,
        "documentsPendingReview": pending,
        "documentsApprovedWorkflow": approved,
        "otherEvidenceDocuments": other_submitted,
        "otherEvidenceApproved": other_approved,
    }


def _requirements_complete(teaching_summary: dict[str, Any], child: dict[str, int]) -> bool:
    set_b = teaching_summary.get("set") if isinstance(teaching_summary.get("set"), dict) else {}
    sef_b = teaching_summary.get("sef") if isinstance(teaching_summary.get("sef"), dict) else {}
    set_missing = list(set_b.get("missingPeriods") or [])
    sef_missing = list(sef_b.get("missingPeriods") or [])
    if set_missing or sef_missing:
        return False
    total = child.get("total") or 0
    validated = child.get("validated") or 0
    if total <= 0:
        return False
    pending = (child.get("pending") or 0) + (child.get("incomplete") or 0)
    pending += child.get("needsRevision") or 0
    if pending > 0:
        return False
    return validated >= total


def _status_label(
    *,
    requirements_complete: bool,
    child: dict[str, int],
    doc_counts: dict[str, int],
) -> tuple[str, str]:
    """Return (legacyStatus, userFacingLabel)."""
    sem_val = child.get("validated") or 0
    sem_total = child.get("total") or 0
    pdf_pending = doc_counts.get("documentsPendingReview") or 0

    if requirements_complete and pdf_pending == 0:
        return "On track", "Requirements Complete"

    if sem_total > 0 and sem_val == sem_total and pdf_pending > 0:
        return "Needs attention", "Semester Evaluations Validated — Documents Pending Review"

    if sem_val > 0 or (doc_counts.get("otherEvidenceApproved") or 0) > 0:
        return "Needs attention", "Needs attention"

    if sem_total == 0 and (doc_counts.get("otherEvidenceDocuments") or 0) == 0:
        return "Incomplete", "Incomplete"

    return "Incomplete", "Incomplete"


def evidence_compliance_snapshot(
    profile: FacultyProfile,
    teaching_summary: dict[str, Any],
) -> dict[str, Any]:
    """
    Compliance for faculty detail / dashboards.

    Semester SET/SEF validation is tracked separately from parent PDF workflow status.
    """
    child = _child_totals(teaching_summary)
    doc_counts = _document_workflow_counts(profile)
    requirements_complete = _requirements_complete(teaching_summary, child)
    legacy_status, status_label = _status_label(
        requirements_complete=requirements_complete,
        child=child,
        doc_counts=doc_counts,
    )

    sem_total = child.get("total") or 0
    sem_val = child.get("validated") or 0
    progress_label = (
        f"{sem_val} of {sem_total} semester evaluations validated"
        if sem_total > 0
        else "No semester evaluation records linked yet"
    )

    notes: list[str] = []
    if sem_val > 0 and doc_counts.get("documentsPendingReview"):
        notes.append(
            "All linked semester records may be validated while the uploaded PDF remains "
            "pending document-level review. Instruction (KRA I) estimated scoring uses "
            "validated semester records, not PDF approval alone."
        )

    crit_disp = teaching_summary.get("criterionADisplay")
    if isinstance(crit_disp, dict) and crit_disp.get("explanation"):
        notes.append(str(crit_disp["explanation"]))

    return {
        "status": legacy_status,
        "statusLabel": status_label,
        "requirementsComplete": requirements_complete,
        "semesterEvaluations": {
            "total": sem_total,
            "validated": sem_val,
            "pending": child.get("pending") or 0,
            "needsRevision": child.get("needsRevision") or 0,
            "rejected": child.get("rejected") or 0,
            "incomplete": child.get("incomplete") or 0,
        },
        "semesterEvaluationsValidatedLabel": (
            f"Semester Evaluations Validated: {sem_val}/{sem_total}" if sem_total else None
        ),
        "documentsPendingReview": doc_counts.get("documentsPendingReview") or 0,
        "documentsPendingReviewLabel": (
            f"Documents Pending Review: {doc_counts['documentsPendingReview']}"
            if doc_counts.get("documentsPendingReview")
            else None
        ),
        "submittedDocuments": (
            doc_counts.get("setSefParentPdfCount") or 0
        ) + (doc_counts.get("otherEvidenceDocuments") or 0),
        "validatedDocumentsWorkflow": (doc_counts.get("documentsApprovedWorkflow") or 0)
        + (doc_counts.get("otherEvidenceApproved") or 0),
        "progressLabel": progress_label,
        "parentPdfPendingReview": (doc_counts.get("documentsPendingReview") or 0) > 0,
        "notes": notes,
        "criterionAEstimatedPoints": (
            crit_disp.get("estimatedPoints")
            if isinstance(crit_disp, dict)
            else teaching_summary.get("estimatedPoints")
        ),
        "criterionADisplayLabel": (
            crit_disp.get("displayLabel") if isinstance(crit_disp, dict) else None
        ),
    }
