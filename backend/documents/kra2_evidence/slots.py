"""Reusable KRA II evidence slots (catalog-driven; no per-indicator bespoke rules)."""

from __future__ import annotations

from typing import Final

from kra_configuration.kra2_indicator_registry import contribution_mode

SLOT_PRIMARY_OUTPUT: Final[str] = "primary_output"
SLOT_CONTRIBUTION_CERTIFICATE: Final[str] = "contribution_certificate"


def required_slots(*, indicator_id: str) -> tuple[str, ...]:
    slots: list[str] = [SLOT_PRIMARY_OUTPUT]
    if contribution_mode(indicator_id) == "declared":
        slots.append(SLOT_CONTRIBUTION_CERTIFICATE)
    return tuple(slots)


def slot_label(slot_id: str, *, indicator_id: str | None = None) -> str:
    from kra_configuration.kra2_indicator_registry import workflow_family

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
