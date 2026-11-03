"""Evidence slots for academic program development / revision (§14, Annex A §2)."""

from __future__ import annotations

from typing import Final

CLAIM_TYPE_ACADEMIC_PROGRAM: Final[str] = "academic_program"

PROGRAM_KIND_NEW: Final[str] = "new_program"
PROGRAM_KIND_REVISION: Final[str] = "substantial_revision"

SLOT_PRIMARY_CONTRIBUTION: Final[str] = "primary_contribution_document"
SLOT_FEASIBILITY_STUDY: Final[str] = "feasibility_study"
SLOT_BENCHMARKING: Final[str] = "benchmarking_report"
SLOT_PROGRAM_OUTCOMES: Final[str] = "approved_program_outcomes"
SLOT_OBE_MAPPING: Final[str] = "curriculum_obe_mapping"
SLOT_REVISED_CURRICULUM: Final[str] = "revised_curriculum_stakeholder_consultation"
SLOT_DEAN_CERTIFICATION: Final[str] = "dean_contribution_certification"
SLOT_ACADEMIC_COUNCIL: Final[str] = "academic_council_resolution"
SLOT_GOVERNING_BOARD: Final[str] = "governing_board_resolution"
SLOT_RRPA_COPC: Final[str] = "rrpa_or_copc"
SLOT_IMPLEMENTATION: Final[str] = "implementation_evidence"

# One-of groups (at least one document when the condition applies).
GROUP_DEVELOPMENT_STUDY: Final[str] = "development_study"
DEVELOPMENT_STUDY_SLOTS: Final[tuple[str, ...]] = (SLOT_FEASIBILITY_STUDY, SLOT_BENCHMARKING)

MANDATORY_APPROVAL_SLOTS: Final[tuple[str, ...]] = (
    SLOT_DEAN_CERTIFICATION,
    SLOT_ACADEMIC_COUNCIL,
    SLOT_GOVERNING_BOARD,
    SLOT_IMPLEMENTATION,
)

OPTIONAL_REVIEWER_SLOTS: Final[tuple[str, ...]] = (
    SLOT_PROGRAM_OUTCOMES,
    SLOT_OBE_MAPPING,
)


def all_program_checklist_slots() -> tuple[str, ...]:
    """Initialize every slot; validation applies mandatory vs conditional rules."""
    return (
        SLOT_PRIMARY_CONTRIBUTION,
        SLOT_FEASIBILITY_STUDY,
        SLOT_BENCHMARKING,
        SLOT_PROGRAM_OUTCOMES,
        SLOT_OBE_MAPPING,
        SLOT_REVISED_CURRICULUM,
        *MANDATORY_APPROVAL_SLOTS,
        SLOT_RRPA_COPC,
    )


def allowed_supporting_slots() -> frozenset[str]:
    """Slots faculty may link via upload (excludes primary row)."""
    return frozenset(s for s in all_program_checklist_slots() if s != SLOT_PRIMARY_CONTRIBUTION)


def slot_label(slot_id: str) -> str:
    labels = {
        SLOT_PRIMARY_CONTRIBUTION: "Primary documentary proof of faculty contribution",
        SLOT_FEASIBILITY_STUDY: "Feasibility study (new programs, as applicable)",
        SLOT_BENCHMARKING: "Benchmarking report (as applicable)",
        SLOT_PROGRAM_OUTCOMES: "Approved program outcomes (as applicable)",
        SLOT_OBE_MAPPING: "Curriculum design / OBE mapping (as applicable)",
        SLOT_REVISED_CURRICULUM: "Revised curriculum and stakeholder consultation report",
        SLOT_DEAN_CERTIFICATION: "Dean or academic unit head certification of role and contribution",
        SLOT_ACADEMIC_COUNCIL: "Academic Council resolution approving the program action",
        SLOT_GOVERNING_BOARD: "Governing Board resolution",
        SLOT_RRPA_COPC: "Valid RRPA or COPC (as applicable)",
        SLOT_IMPLEMENTATION: "Evidence of program implementation",
    }
    return labels.get(slot_id, slot_id)
