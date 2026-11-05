"""Align KRA II checklist rows with supporting-document evidence links."""

from __future__ import annotations

from typing import Any, Callable

from models import Document

from documents.kra2_evidence.bundle import (
    SLOT_STATUS_MISSING,
    SLOT_STATUS_PRESENT_UNVERIFIED,
    empty_checklist_entry,
    ensure_checklist_slots,
    link_from_document,
)
from documents.kra2_evidence.slots import primary_evidence_slot, required_slots


def reconcile_kra2_checklist_from_links(primary: Document, bundle: dict[str, Any]) -> bool:
    """Backfill checklist documentId/fileHash from kra2EvidenceLink on supporting uploads."""
    if not isinstance(bundle, dict) or not primary or not getattr(primary, "faculty_profile_id", None):
        return False
    indicator_id = (getattr(primary, "indicator_id", None) or bundle.get("indicatorId") or "").strip()
    if not indicator_id:
        return False
    changed = ensure_checklist_slots(bundle, indicator_id=indicator_id)
    checklist = bundle.setdefault("checklist", {})
    allowed = frozenset(required_slots(indicator_id=indicator_id))
    primary_slot = primary_evidence_slot(indicator_id=indicator_id)
    if primary_slot in allowed:
        entry = checklist.get(primary_slot)
        if not isinstance(entry, dict):
            entry = empty_checklist_entry()
            checklist[primary_slot] = entry
            changed = True
        pid = (bundle.get("primaryDocumentId") or primary.public_id or "").strip()
        if pid and not (entry.get("documentId") or "").strip():
            entry["documentId"] = pid
            entry["fileHash"] = bundle.get("primaryFileHash") or getattr(primary, "file_hash", None)
            if entry.get("status") == SLOT_STATUS_MISSING:
                entry["status"] = SLOT_STATUS_PRESENT_UNVERIFIED
            changed = True

    query = Document.query.filter_by(faculty_profile_id=primary.faculty_profile_id).filter(
        Document.deleted_at.is_(None)
    )
    for sup in query:
        if sup.public_id == primary.public_id:
            continue
        link = link_from_document(sup)
        if not isinstance(link, dict) or link.get("role") != "supporting":
            continue
        if (link.get("primaryDocumentId") or "").strip() != primary.public_id:
            continue
        slot = (link.get("evidenceSlot") or "").strip()
        if not slot or slot not in allowed:
            continue
        entry = checklist.get(slot)
        if not isinstance(entry, dict):
            entry = empty_checklist_entry()
            checklist[slot] = entry
            changed = True
        if not (entry.get("documentId") or "").strip():
            entry["documentId"] = sup.public_id
            entry["fileHash"] = sup.file_hash
            if entry.get("status") == SLOT_STATUS_MISSING:
                entry["status"] = SLOT_STATUS_PRESENT_UNVERIFIED
            changed = True

    return changed


def reconcile_checklist_from_links_generic(
    primary: Document,
    bundle: dict[str, Any],
    *,
    indicator_id: str,
    link_reader: Callable[[Document], dict[str, Any] | None],
    ensure_slots: Callable[[dict[str, Any], str], bool],
    primary_slot_resolver: Callable[[str], str],
    required_slot_ids: Callable[[str], tuple[str, ...] | list[str]],
) -> bool:
    if not isinstance(bundle, dict) or not primary or not getattr(primary, "faculty_profile_id", None):
        return False
    iid = (indicator_id or "").strip()
    if not iid:
        return False
    changed = ensure_slots(bundle, iid)
    checklist = bundle.setdefault("checklist", {})
    allowed = frozenset(required_slot_ids(iid))
    primary_slot = primary_slot_resolver(iid)
    if primary_slot in allowed:
        entry = checklist.get(primary_slot)
        if not isinstance(entry, dict):
            entry = empty_checklist_entry()
            checklist[primary_slot] = entry
            changed = True
        pid = (bundle.get("primaryDocumentId") or primary.public_id or "").strip()
        if pid and not (entry.get("documentId") or "").strip():
            entry["documentId"] = pid
            entry["fileHash"] = bundle.get("primaryFileHash") or getattr(primary, "file_hash", None)
            if entry.get("status") == SLOT_STATUS_MISSING:
                entry["status"] = SLOT_STATUS_PRESENT_UNVERIFIED
            changed = True

    query = Document.query.filter_by(faculty_profile_id=primary.faculty_profile_id).filter(
        Document.deleted_at.is_(None)
    )
    for sup in query:
        if sup.public_id == primary.public_id:
            continue
        link = link_reader(sup)
        if not isinstance(link, dict) or link.get("role") != "supporting":
            continue
        if (link.get("primaryDocumentId") or "").strip() != primary.public_id:
            continue
        slot = (link.get("evidenceSlot") or "").strip()
        if not slot or slot not in allowed:
            continue
        entry = checklist.get(slot)
        if not isinstance(entry, dict):
            entry = empty_checklist_entry()
            checklist[slot] = entry
            changed = True
        if not (entry.get("documentId") or "").strip():
            entry["documentId"] = sup.public_id
            entry["fileHash"] = sup.file_hash
            if entry.get("status") == SLOT_STATUS_MISSING:
                entry["status"] = SLOT_STATUS_PRESENT_UNVERIFIED
            changed = True
    return changed
