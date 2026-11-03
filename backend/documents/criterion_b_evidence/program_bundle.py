"""Academic program evidence bundles (JSON on Document.extracted_info)."""

from __future__ import annotations

from typing import Any

from kra_configuration.criterion_b_annex import (
    annex_row_for_indicator,
    faculty_role_for_program_indicator,
)
from documents.criterion_b_evidence.bundle import (
    VALIDATION_INCOMPLETE,
    empty_checklist_entry,
)
from documents.criterion_b_evidence.program_checklist import (
    CLAIM_TYPE_ACADEMIC_PROGRAM,
    SLOT_PRIMARY_CONTRIBUTION,
    all_program_checklist_slots,
)
from documents.criterion_b_evidence.program_applicability import (
    empty_rrpa_copc_applicability_decision,
)
from documents.criterion_b_evidence.bundle import _utcnow_iso


def build_initial_program_bundle(
    *,
    primary_document_id: str,
    primary_file_hash: str | None,
    indicator_id: str,
    program_name: str,
) -> dict[str, Any]:
    role = faculty_role_for_program_indicator(indicator_id)
    row = annex_row_for_indicator(indicator_id)
    checklist: dict[str, Any] = {}
    for slot in all_program_checklist_slots():
        checklist[slot] = empty_checklist_entry()
    checklist[SLOT_PRIMARY_CONTRIBUTION] = {
        "status": "present_unverified",
        "documentId": primary_document_id,
        "fileHash": primary_file_hash,
        "reviewerNote": "",
        "ocrHintOnly": True,
    }
    return {
        "version": "1.0",
        "claimType": CLAIM_TYPE_ACADEMIC_PROGRAM,
        "claimRole": "primary",
        "programName": (program_name or "").strip(),
        "programDevelopmentKind": None,
        "facultyRole": role,
        "contributionDescription": "",
        "committeeName": "",
        "annexRowId": row.row_id if row else None,
        "indicatorId": indicator_id,
        "checklist": checklist,
        "supportingDocumentIds": [],
        "validationStatus": VALIDATION_INCOMPLETE,
        "reviewerRemarks": "",
        "reviewerDisqualificationConfirmed": False,
        "flags": [],
        "crossKraWarnings": [],
        "rrpaCopcApplicabilityDecision": empty_rrpa_copc_applicability_decision(),
        "rrpaCopcApplicability": "unknown",
        "rrpaCopcApplicabilityNote": "",
        "updatedAt": _utcnow_iso(),
    }


def is_academic_program_bundle(bundle: dict[str, Any] | None) -> bool:
    return bool(
        bundle
        and isinstance(bundle, dict)
        and bundle.get("claimType") == CLAIM_TYPE_ACADEMIC_PROGRAM
    )
