"""Criterion C evidence slots (Annex A + Section 15)."""

from __future__ import annotations

from typing import Final

SLOT_APPROVAL_SHEET: Final[str] = "approval_sheet"
SLOT_RRPA_COPC: Final[str] = "rrpa_copc"
SLOT_MENTOR_DESIGNATION: Final[str] = "mentor_designation"
SLOT_AWARD_CERTIFICATE: Final[str] = "award_certificate"
SLOT_COMPETITION_MECHANICS: Final[str] = "competition_mechanics"
SLOT_AWARDING_ORGANIZATION: Final[str] = "awarding_organization"


def required_slots(*, service_category: str) -> tuple[str, ...]:
    cat = (service_category or "").strip().lower()
    if cat == "mentorship":
        return (
            SLOT_MENTOR_DESIGNATION,
            SLOT_AWARD_CERTIFICATE,
            SLOT_COMPETITION_MECHANICS,
            SLOT_AWARDING_ORGANIZATION,
        )
    return (SLOT_APPROVAL_SHEET, SLOT_RRPA_COPC)


def slot_label(slot_id: str) -> str:
    labels = {
        SLOT_APPROVAL_SHEET: "Approval sheet (signed)",
        SLOT_RRPA_COPC: "RRPA or COPC for the academic program",
        SLOT_MENTOR_DESIGNATION: "Official mentor/coach designation",
        SLOT_AWARD_CERTIFICATE: "Award, certificate, or photo of major prize",
        SLOT_COMPETITION_MECHANICS: "Competition mechanics (major awards/winners)",
        SLOT_AWARDING_ORGANIZATION: "Award-giving organization profile",
    }
    return labels.get(slot_id, slot_id.replace("_", " "))
