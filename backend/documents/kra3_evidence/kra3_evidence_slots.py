"""Structured evidence slot IDs for KRA III (Annex A pp. 92–96)."""

from __future__ import annotations

from typing import Final

from kra_configuration.kra3_indicator_registry import workflow_family

SLOT_PRIMARY: Final[str] = "primary_output"
SLOT_PARTNERSHIP_APPROVAL: Final[str] = "partnership_approval"
SLOT_MOA: Final[str] = "moa_mou"
SLOT_IMPLEMENTATION_REPORT: Final[str] = "implementation_report"
SLOT_FACULTY_INITIATIVE: Final[str] = "faculty_initiative_certification"
SLOT_FINANCE_CERT: Final[str] = "finance_certification"
SLOT_INCOME_RECORDS: Final[str] = "income_records"
SLOT_APPOINTMENT: Final[str] = "official_appointment"
SLOT_ENGAGEMENT_PROOF: Final[str] = "engagement_proof"
SLOT_PRESIDENT_AUTH: Final[str] = "president_authorization"
SLOT_INVITATION: Final[str] = "official_invitation"
SLOT_COMPETITION_PROOF: Final[str] = "competition_proof"
SLOT_CONSULT_AGREEMENT: Final[str] = "consultancy_agreement"
SLOT_CONSULT_REPORT: Final[str] = "consultancy_report"
SLOT_MEDIA_PROOF: Final[str] = "media_proof"
SLOT_SCHEDULE_PROOF: Final[str] = "broadcast_schedule"
SLOT_CSR_REPORT: Final[str] = "csr_report"
SLOT_CSR_INSTRUMENT: Final[str] = "csr_survey_instrument"
SLOT_LINKED_PROJECT: Final[str] = "linked_extension_project"
SLOT_SPECIAL_ORDER: Final[str] = "special_order_designation"

_SLOT_LABELS: dict[str, str] = {
    SLOT_PRIMARY: "Primary evidence document",
    SLOT_PARTNERSHIP_APPROVAL: "Board or executive approval for the partnership",
    SLOT_MOA: "Notarized MOA or MOU (or project proposal)",
    SLOT_IMPLEMENTATION_REPORT: "Implementation or terminal report",
    SLOT_FACULTY_INITIATIVE: "Certification that you initiated the partnership",
    SLOT_FINANCE_CERT: "Finance Division certification of your contribution",
    SLOT_INCOME_RECORDS: "Financial reports or Sub-ARO equivalent",
    SLOT_APPOINTMENT: "Official appointment or designation letter",
    SLOT_ENGAGEMENT_PROOF: "Proof of engagement (certificate, report, or travel order)",
    SLOT_PRESIDENT_AUTH: "President or Vice President authorization",
    SLOT_INVITATION: "Official invitation letter",
    SLOT_COMPETITION_PROOF: "Proof of award or competition",
    SLOT_CONSULT_AGREEMENT: "Consultancy agreement or contract",
    SLOT_CONSULT_REPORT: "Consultancy certificate or terminal report",
    SLOT_MEDIA_PROOF: "Published article, recording, or program proof",
    SLOT_SCHEDULE_PROOF: "On-air schedule or hosting contract",
    SLOT_CSR_REPORT: "Client Satisfaction Rating report",
    SLOT_CSR_INSTRUMENT: "Official CSR survey instrument",
    SLOT_LINKED_PROJECT: "Reference to eligible extension project",
    SLOT_SPECIAL_ORDER: "Special Order or official designation document",
}

_FAMILY_SLOTS: dict[str, tuple[str, ...]] = {
    "linkage": (
        SLOT_PARTNERSHIP_APPROVAL,
        SLOT_MOA,
        SLOT_IMPLEMENTATION_REPORT,
        SLOT_FACULTY_INITIATIVE,
    ),
    "income": (SLOT_PRIMARY, SLOT_FINANCE_CERT, SLOT_INCOME_RECORDS),
    "accreditation": (SLOT_PRIMARY, SLOT_APPOINTMENT, SLOT_ENGAGEMENT_PROOF, SLOT_PRESIDENT_AUTH),
    "judging": (SLOT_PRIMARY, SLOT_INVITATION, SLOT_COMPETITION_PROOF, SLOT_ENGAGEMENT_PROOF, SLOT_PRESIDENT_AUTH),
    "consultancy": (SLOT_PRIMARY, SLOT_CONSULT_AGREEMENT, SLOT_CONSULT_REPORT, SLOT_PRESIDENT_AUTH),
    "media_column": (SLOT_PRIMARY, SLOT_MEDIA_PROOF),
    "media_host": (SLOT_PRIMARY, SLOT_SCHEDULE_PROOF, SLOT_MEDIA_PROOF),
    "media_guest": (SLOT_PRIMARY, SLOT_INVITATION, SLOT_MEDIA_PROOF),
    "resource_person": (SLOT_PRIMARY, SLOT_INVITATION, SLOT_ENGAGEMENT_PROOF),
    "extension_project": (SLOT_PRIMARY, SLOT_ENGAGEMENT_PROOF),
    "csr": (SLOT_CSR_REPORT, SLOT_CSR_INSTRUMENT, SLOT_LINKED_PROJECT),
    "designation": (SLOT_SPECIAL_ORDER, SLOT_PRIMARY),
    "generic_service": (SLOT_PRIMARY, SLOT_ENGAGEMENT_PROOF),
}


def required_slots_for_indicator(indicator_id: str) -> tuple[str, ...]:
    fam = workflow_family(indicator_id)
    return _FAMILY_SLOTS.get(fam, _FAMILY_SLOTS["generic_service"])


def slot_label_for(slot_id: str, *, indicator_id: str | None = None) -> str:
    _ = indicator_id
    return _SLOT_LABELS.get(slot_id, slot_id.replace("_", " "))
