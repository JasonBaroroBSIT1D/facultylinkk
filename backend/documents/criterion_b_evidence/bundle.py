"""Evidence bundle schema stored in ``Document.extracted_info`` (no new tables)."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

from kra_configuration.criterion_b_annex import (
    annex_row_for_indicator,
    indicator_requires_contribution_percent,
    is_instructional_material_indicator,
)
from documents.criterion_b_evidence.checklist import (
    ROW_TO_MATERIAL,
    SLOT_PRIMARY_MATERIAL,
    required_slots,
)

BUNDLE_VERSION = "1.0"
BUNDLE_EXTRACTED_KEY = "criterionBEvidenceBundle"
LINK_EXTRACTED_KEY = "criterionBEvidenceLink"
CLAIM_TYPE_INSTRUCTIONAL_MATERIAL = "instructional_material"

SLOT_STATUS_MISSING = "missing"
SLOT_STATUS_PRESENT_UNVERIFIED = "present_unverified"
SLOT_STATUS_REVIEWER_REQUIRED = "reviewer_required"
SLOT_STATUS_VERIFIED = "verified"
SLOT_STATUS_NOT_APPLICABLE = "not_applicable"

VALIDATION_INCOMPLETE = "incomplete"
VALIDATION_REVIEWER_REQUIRED = "reviewer_required"
VALIDATION_VALID = "valid"
VALIDATION_INVALID = "invalid"


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _info(doc: Any) -> dict[str, Any]:
    raw = getattr(doc, "extracted_info", None)
    return dict(raw) if isinstance(raw, dict) else {}


def authorship_from_indicator(indicator_id: str) -> str:
    return "co" if indicator_requires_contribution_percent(indicator_id) else "sole"


def material_type_from_indicator(indicator_id: str) -> str | None:
    row = annex_row_for_indicator(indicator_id)
    if not row:
        return None
    return ROW_TO_MATERIAL.get(row.row_id)


def empty_checklist_entry() -> dict[str, Any]:
    return {
        "status": SLOT_STATUS_MISSING,
        "documentId": None,
        "fileHash": None,
        "reviewerNote": "",
        "ocrHintOnly": False,
    }


def build_initial_bundle(
    *,
    primary_document_id: str,
    primary_file_hash: str | None,
    indicator_id: str,
    material_title: str,
) -> dict[str, Any]:
    material_type = material_type_from_indicator(indicator_id)
    authorship = authorship_from_indicator(indicator_id)
    row = annex_row_for_indicator(indicator_id)
    slots_needed = required_slots(material_type or "", authorship=authorship)
    checklist: dict[str, Any] = {}
    for slot in slots_needed:
        checklist[slot] = empty_checklist_entry()
    checklist[SLOT_PRIMARY_MATERIAL] = {
        "status": SLOT_STATUS_PRESENT_UNVERIFIED,
        "documentId": primary_document_id,
        "fileHash": primary_file_hash,
        "reviewerNote": "",
        "ocrHintOnly": True,
    }
    return {
        "version": BUNDLE_VERSION,
        "claimType": CLAIM_TYPE_INSTRUCTIONAL_MATERIAL,
        "claimRole": "primary",
        "materialTitle": (material_title or "").strip(),
        "materialType": material_type,
        "annexRowId": row.row_id if row else None,
        "indicatorId": indicator_id,
        "authorship": authorship,
        "contributionPercent": None,
        "specializationAligned": None,
        "completeSetDeclared": None,
        "checklist": checklist,
        "supportingDocumentIds": [],
        "validationStatus": VALIDATION_INCOMPLETE,
        "reviewerRemarks": "",
        "flags": [],
        "updatedAt": _utcnow_iso(),
    }


def bundle_from_document(doc: Any) -> dict[str, Any] | None:
    info = _info(doc)
    raw = info.get(BUNDLE_EXTRACTED_KEY)
    return deepcopy(raw) if isinstance(raw, dict) else None


def link_from_document(doc: Any) -> dict[str, Any] | None:
    info = _info(doc)
    raw = info.get(LINK_EXTRACTED_KEY)
    return deepcopy(raw) if isinstance(raw, dict) else None


def is_supporting_evidence_document(doc: Any) -> bool:
    link = link_from_document(doc)
    return bool(link and link.get("role") == "supporting")


def is_primary_im_claim(doc: Any) -> bool:
    if not is_instructional_material_indicator(getattr(doc, "indicator_id", None)):
        return False
    if is_supporting_evidence_document(doc):
        return False
    return bundle_from_document(doc) is not None or (
        getattr(doc, "criterion_id", None) == "kra1-b"
        and link_from_document(doc) is None
    )


def persist_bundle(doc: Any, bundle: dict[str, Any]) -> None:
    info = _info(doc)
    bundle["updatedAt"] = _utcnow_iso()
    info[BUNDLE_EXTRACTED_KEY] = bundle
    doc.extracted_info = info


def persist_link(doc: Any, link: dict[str, Any]) -> None:
    info = _info(doc)
    link["updatedAt"] = _utcnow_iso()
    info[LINK_EXTRACTED_KEY] = link
    doc.extracted_info = info


def apply_slot_link(
    bundle: dict[str, Any],
    *,
    slot_id: str,
    supporting_document_id: str,
    supporting_file_hash: str | None,
) -> dict[str, Any]:
    """Attach a supporting document to a checklist slot (does not mark verified)."""
    bundle = deepcopy(bundle)
    checklist = bundle.setdefault("checklist", {})
    if slot_id not in checklist and slot_id != SLOT_PRIMARY_MATERIAL:
        checklist[slot_id] = empty_checklist_entry()
    entry = checklist.get(slot_id) or empty_checklist_entry()
    entry["documentId"] = supporting_document_id
    entry["fileHash"] = supporting_file_hash
    entry["status"] = SLOT_STATUS_PRESENT_UNVERIFIED
    entry["ocrHintOnly"] = True
    checklist[slot_id] = entry
    supporting_ids = list(bundle.get("supportingDocumentIds") or [])
    if supporting_document_id not in supporting_ids:
        supporting_ids.append(supporting_document_id)
    bundle["supportingDocumentIds"] = supporting_ids
    return bundle
