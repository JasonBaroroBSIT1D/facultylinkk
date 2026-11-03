"""Criterion C accomplishment bundle in ``Document.extracted_info`` (JSON only)."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any
import uuid

from kra_configuration.criterion_c_annex import indicator_metadata, is_criterion_c_indicator
from documents.criterion_c_evidence.checklist import required_slots

BUNDLE_VERSION = "1.0"
BUNDLE_EXTRACTED_KEY = "criterionCEvidenceBundle"
LINK_EXTRACTED_KEY = "criterionCEvidenceLink"

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
    project_title: str = "",
) -> dict[str, Any]:
    meta = indicator_metadata(indicator_id) or {}
    service_category = meta.get("serviceCategory") or "research"
    checklist: dict[str, Any] = {}
    for slot in required_slots(service_category=str(service_category)):
        checklist[slot] = empty_checklist_entry()

    accomplishment_id = str(uuid.uuid4())
    return {
        "version": BUNDLE_VERSION,
        "accomplishmentId": accomplishment_id,
        "indicatorId": indicator_id,
        "serviceCategory": service_category,
        "researchType": meta.get("researchType"),
        "role": meta.get("role"),
        "projectTitle": (project_title or "").strip(),
        "studentNames": "",
        "studentGroupLabel": "",
        "academicYear": "",
        "completionDate": "",
        "mentorship": {
            "competitionName": "",
            "prizeLevel": "",
            "prizePlacement": "",
        },
        "reviewStatus": REVIEW_PENDING,
        "checklist": checklist,
        "supportingDocumentIds": [],
        "duplicateFlags": [],
        "policyFlags": [],
        "reviewerRemarks": "",
        "reviewerAssessment": None,
        "validationStatus": VALIDATION_INCOMPLETE,
        "flags": [],
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
    bundle = bundle_from_document(doc)
    if bundle:
        return False
    info = _info(doc)
    legacy = info.get(LINK_EXTRACTED_KEY) or info.get("criterionBEvidenceLink")
    if isinstance(legacy, dict) and legacy.get("role") == "supporting":
        return True
    return False


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
