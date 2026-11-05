"""Structured evidence slot IDs for KRA IV (JC Annex A — Professional Development)."""

from __future__ import annotations

from typing import Final

from kra_configuration.kra4_indicator_registry import workflow_family

SLOT_PRIMARY: Final[str] = "primary_output"
SLOT_MEMBERSHIP: Final[str] = "membership_proof"
SLOT_ORG_PROFILE: Final[str] = "organization_profile"
SLOT_PARTICIPATION: Final[str] = "participation_proof"
SLOT_DIPLOMA: Final[str] = "diploma_or_certificate"
SLOT_TRANSCRIPT: Final[str] = "certified_transcript"
SLOT_PARTICIPATION_CERT: Final[str] = "participation_certificate"
SLOT_EVENT_PROGRAM: Final[str] = "event_program"
SLOT_APPROVAL: Final[str] = "approval_evidence"
SLOT_ACCEPTANCE: Final[str] = "acceptance_letter"
SLOT_PRESENTATION_CERT: Final[str] = "presentation_certificate"
SLOT_AWARD_CERT: Final[str] = "award_certificate"
SLOT_AWARD_CRITERIA: Final[str] = "award_criteria"
SLOT_AWARD_ORG_PROFILE: Final[str] = "awarding_org_profile"
SLOT_EMPLOYMENT: Final[str] = "employment_record"
SLOT_JOB_DESC: Final[str] = "position_description"

_SLOT_LABELS: dict[str, str] = {
    SLOT_PRIMARY: "Primary evidence document",
    SLOT_MEMBERSHIP: "Membership certificate or ID",
    SLOT_ORG_PROFILE: "Organization registration or profile",
    SLOT_PARTICIPATION: "Evidence of active participation",
    SLOT_DIPLOMA: "Diploma or certificate",
    SLOT_TRANSCRIPT: "Certified transcript or TOR",
    SLOT_PARTICIPATION_CERT: "Certificate of participation",
    SLOT_EVENT_PROGRAM: "Event program or agenda",
    SLOT_APPROVAL: "Official approval (when required)",
    SLOT_ACCEPTANCE: "Letter or certificate of acceptance",
    SLOT_PRESENTATION_CERT: "Presenter certificate",
    SLOT_AWARD_CERT: "Award certificate or photo of award",
    SLOT_AWARD_CRITERIA: "Award criteria and selection process",
    SLOT_AWARD_ORG_PROFILE: "Awarding organization profile",
    SLOT_EMPLOYMENT: "Service record or certificate of employment",
    SLOT_JOB_DESC: "Position description or appointment",
}

_FAMILY_SLOTS: dict[str, tuple[str, ...]] = {
    "organization": (SLOT_MEMBERSHIP, SLOT_ORG_PROFILE, SLOT_PARTICIPATION),
    "education": (SLOT_DIPLOMA, SLOT_TRANSCRIPT),
    "capacity_building": (SLOT_PARTICIPATION_CERT, SLOT_EVENT_PROGRAM, SLOT_APPROVAL),
    "paper_presentation": (SLOT_ACCEPTANCE, SLOT_PRESENTATION_CERT, SLOT_APPROVAL, SLOT_EVENT_PROGRAM),
    "award": (SLOT_AWARD_CERT, SLOT_AWARD_CRITERIA, SLOT_AWARD_ORG_PROFILE),
    "prior_experience": (SLOT_EMPLOYMENT, SLOT_JOB_DESC),
    "generic": (SLOT_PRIMARY, SLOT_PARTICIPATION),
}


def required_slots_for_indicator(indicator_id: str) -> tuple[str, ...]:
    fam = workflow_family(indicator_id)
    return _FAMILY_SLOTS.get(fam, _FAMILY_SLOTS["generic"])


def slot_label_for(slot_id: str, *, indicator_id: str | None = None) -> str:
    _ = indicator_id
    return _SLOT_LABELS.get(slot_id, slot_id.replace("_", " "))
