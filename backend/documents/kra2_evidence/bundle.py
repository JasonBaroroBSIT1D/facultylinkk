"""KRA II accomplishment bundle in ``Document.extracted_info`` (JSON only)."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any
import uuid

from kra_configuration.kra2_annex import indicator_metadata, is_kra2_indicator
from kra_configuration.kra2_indicator_registry import contribution_mode, user_facing_title, workflow_family
from documents.kra2_evidence.slots import required_slots

BUNDLE_VERSION = "1.0"
BUNDLE_EXTRACTED_KEY = "kra2EvidenceBundle"
LINK_EXTRACTED_KEY = "kra2EvidenceLink"

SLOT_STATUS_MISSING = "missing"
SLOT_STATUS_PRESENT_UNVERIFIED = "present_unverified"
SLOT_STATUS_REVIEWER_REQUIRED = "reviewer_required"
SLOT_STATUS_VERIFIED = "verified"

REVIEW_PENDING = "pending"
REVIEW_APPROVED = "approved"
REVIEW_REJECTED = "rejected"

VALIDATION_INCOMPLETE = "incomplete"
VALIDATION_REVIEWER_REQUIRED = "reviewer_required"
VALIDATION_VALID = "valid"
VALIDATION_INVALID = "invalid"


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _info(doc: Any) -> dict[str, Any]:
    raw = getattr(doc, "extracted_info", None)
    return dict(raw) if isinstance(raw, dict) else {}


def empty_checklist_entry() -> dict[str, Any]:
    return {
        "status": SLOT_STATUS_MISSING,
        "documentId": None,
        "fileHash": None,
        "reviewerNote": "",
        "ocrHintOnly": True,
    }


def build_initial_bundle(
    *,
    primary_document_id: str,
    primary_file_hash: str | None,
    indicator_id: str,
    output_title: str = "",
) -> dict[str, Any]:
    meta = indicator_metadata(indicator_id) or {}
    contrib = contribution_mode(indicator_id)
    checklist: dict[str, Any] = {}
    for slot in required_slots(indicator_id=indicator_id):
        entry = empty_checklist_entry()
        if slot == "primary_output":
            entry["documentId"] = primary_document_id
            entry["fileHash"] = primary_file_hash
            entry["status"] = SLOT_STATUS_PRESENT_UNVERIFIED
        checklist[slot] = entry

    accomplishment_id = str(uuid.uuid4())
    return {
        "version": BUNDLE_VERSION,
        "accomplishmentId": accomplishment_id,
        "indicatorId": indicator_id,
        "criterionId": meta.get("criterionId"),
        "outputFamily": meta.get("outputFamily"),
        "contribution": contrib if contrib != "unknown" else meta.get("contribution"),
        "workflowFamily": workflow_family(indicator_id),
        "indicatorTitle": user_facing_title(indicator_id),
        "outputTitle": (output_title or "").strip(),
        "outputVenue": "",
        "journalTitle": "",
        "authorsLine": "",
        "publicationDate": "",
        "publicationReference": "",
        "registrationNumber": "",
        "registrationDate": "",
        "citationContext": "",
        "declaredContributionPercent": None,
        "indexingAttestation": "",
        "reviewStatus": REVIEW_PENDING,
        "submittedForReviewAt": None,
        "checklist": checklist,
        "supportingDocumentIds": [],
        "duplicateFlags": [],
        "policyFlags": [],
        "reviewerRemarks": "",
        "reviewerAssessment": None,
        "validationStatus": VALIDATION_INCOMPLETE,
        "flags": [],
        "metadataConfirmed": {},
        "updatedAt": _utcnow_iso(),
        "primaryDocumentId": primary_document_id,
        "primaryFileHash": primary_file_hash,
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
    if link and link.get("role") == "supporting":
        return True
    if bundle_from_document(doc):
        return False
    info = _info(doc)
    legacy = info.get(LINK_EXTRACTED_KEY)
    if isinstance(legacy, dict) and legacy.get("role") == "supporting":
        return True
    return False


def is_kra2_primary_accomplishment(doc: Any) -> bool:
    if not is_kra2_indicator(getattr(doc, "indicator_id", None)):
        return False
    return not is_supporting_evidence_document(doc)


def persist_bundle(doc: Any, bundle: dict[str, Any]) -> None:
    info = _info(doc)
    bundle["updatedAt"] = _utcnow_iso()
    info[BUNDLE_EXTRACTED_KEY] = bundle
    doc.extracted_info = info


def persist_link(doc: Any, link: dict[str, Any]) -> None:
    info = _info(doc)
    info[LINK_EXTRACTED_KEY] = link
    doc.extracted_info = info


def apply_slot_link(
    bundle: dict[str, Any],
    *,
    slot_id: str,
    supporting_document_id: str,
    supporting_file_hash: str | None,
) -> dict[str, Any]:
    bundle = deepcopy(bundle)
    checklist = bundle.setdefault("checklist", {})
    entry = checklist.get(slot_id)
    if not isinstance(entry, dict):
        entry = empty_checklist_entry()
    entry["documentId"] = supporting_document_id
    entry["fileHash"] = supporting_file_hash
    if entry.get("status") == SLOT_STATUS_MISSING:
        entry["status"] = SLOT_STATUS_PRESENT_UNVERIFIED
    entry["ocrHintOnly"] = True
    checklist[slot_id] = entry
    ids = list(bundle.get("supportingDocumentIds") or [])
    if supporting_document_id not in ids:
        ids.append(supporting_document_id)
    bundle["supportingDocumentIds"] = ids
    return bundle
