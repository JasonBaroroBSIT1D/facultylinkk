"""Reusable KRA II evidence slots (catalog-driven; no per-indicator bespoke rules)."""

from __future__ import annotations

from typing import Final

from kra_configuration.kra2_indicator_registry import contribution_mode

SLOT_PRIMARY_OUTPUT: Final[str] = "primary_output"
SLOT_CONTRIBUTION_CERTIFICATE: Final[str] = "contribution_certificate"


def primary_evidence_slot(*, indicator_id: str) -> str:
    """Checklist slot that receives the faculty's first accomplishment PDF."""
    slots = required_slots(indicator_id=indicator_id)
    if SLOT_PRIMARY_OUTPUT in slots:
        return SLOT_PRIMARY_OUTPUT
    return slots[0] if slots else SLOT_PRIMARY_OUTPUT


def required_slots(*, indicator_id: str) -> tuple[str, ...]:
    from documents.kra2_evidence.kra2_a_evidence_slots import (
        criterion_a_required_slots,
        is_criterion_a_indicator,
    )
    from documents.kra2_evidence.kra2_b_evidence_slots import (
        criterion_b_required_slots,
        is_criterion_b_indicator,
    )
    from documents.kra2_evidence.kra2_c_evidence_slots import (
        criterion_c_required_slots,
        is_criterion_c_indicator,
    )

    if is_criterion_a_indicator(indicator_id):
        return criterion_a_required_slots(indicator_id)
    if is_criterion_b_indicator(indicator_id):
        return criterion_b_required_slots(indicator_id)
    if is_criterion_c_indicator(indicator_id):
        return criterion_c_required_slots(indicator_id)
    slots: list[str] = [SLOT_PRIMARY_OUTPUT]
    if contribution_mode(indicator_id) == "declared":
        slots.append(SLOT_CONTRIBUTION_CERTIFICATE)
    return tuple(slots)


def slot_label(slot_id: str, *, indicator_id: str | None = None) -> str:
    from documents.kra2_evidence.kra2_a_evidence_slots import (
        criterion_a_slot_label,
        is_criterion_a_indicator,
    )
    from kra_configuration.kra2_indicator_registry import workflow_family

    if is_criterion_a_indicator(indicator_id or ""):
        return criterion_a_slot_label(slot_id, indicator_id=indicator_id or "")
    from documents.kra2_evidence.kra2_b_evidence_slots import (
        criterion_b_slot_label,
        is_criterion_b_indicator,
    )

    if is_criterion_b_indicator(indicator_id or ""):
        return criterion_b_slot_label(slot_id, indicator_id=indicator_id or "")
    from documents.kra2_evidence.kra2_c_evidence_slots import (
        criterion_c_slot_label,
        is_criterion_c_indicator,
    )

    if is_criterion_c_indicator(indicator_id or ""):
        return criterion_c_slot_label(slot_id, indicator_id=indicator_id or "")
    family = workflow_family(indicator_id or "")
    labels = {
        SLOT_PRIMARY_OUTPUT: "Primary evidence document",
        SLOT_CONTRIBUTION_CERTIFICATE: "Certificate of Contribution (Annex D or applicable form)",
    }
    if slot_id == SLOT_PRIMARY_OUTPUT:
        if family == "invention_ip":
            return "Official IP or patent evidence"
        if family == "citation_impact":
            return "Citation evidence document"
        if family == "commercialization":
            return "Commercialization proof"
        return "Copy of published or exhibited output"
    return labels.get(slot_id, slot_id.replace("_", " "))
