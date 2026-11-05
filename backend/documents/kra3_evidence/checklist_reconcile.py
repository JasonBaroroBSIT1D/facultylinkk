"""Align KRA III checklist rows with supporting-document evidence links."""

from __future__ import annotations

from typing import Any

from models import Document

from documents.kra2_evidence.checklist_reconcile import reconcile_checklist_from_links_generic
from documents.kra3_evidence.bundle import ensure_checklist_slots, link_from_document
from documents.kra3_evidence.slots import primary_evidence_slot, required_slots


def reconcile_kra3_checklist_from_links(primary: Document, bundle: dict[str, Any]) -> bool:
    indicator_id = (getattr(primary, "indicator_id", None) or bundle.get("indicatorId") or "").strip()
    return reconcile_checklist_from_links_generic(
        primary,
        bundle,
        indicator_id=indicator_id,
        link_reader=link_from_document,
        ensure_slots=ensure_checklist_slots,
        primary_slot_resolver=primary_evidence_slot,
        required_slot_ids=required_slots,
    )
