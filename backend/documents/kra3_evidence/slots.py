"""KRA III evidence slots (family-driven checklist)."""

from __future__ import annotations

from documents.kra3_evidence.kra3_evidence_slots import (
    required_slots_for_indicator,
    slot_label_for,
    SLOT_PRIMARY,
)


def primary_evidence_slot(*, indicator_id: str) -> str:
    slots = required_slots(indicator_id=indicator_id)
    if SLOT_PRIMARY in slots:
        return SLOT_PRIMARY
    return slots[0] if slots else SLOT_PRIMARY


def required_slots(*, indicator_id: str) -> tuple[str, ...]:
    return required_slots_for_indicator(indicator_id)


def slot_label(slot_id: str, *, indicator_id: str | None = None) -> str:
    return slot_label_for(slot_id, indicator_id=indicator_id)
