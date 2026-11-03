"""Required evidence slots per instructional material type (Annex A + §§12–13)."""

from __future__ import annotations

from typing import Final

# Evidence slot identifiers (stable API).
SLOT_PRIMARY_MATERIAL: Final[str] = "primary_material"
SLOT_IMDC_APPROVAL: Final[str] = "imdc_evaluation_approval"
SLOT_APPROVED_SYLLABUS: Final[str] = "approved_syllabus"
SLOT_LIBRARY_CERTIFICATION: Final[str] = "library_certification"
SLOT_ANNEX_C_CONTRIBUTION: Final[str] = "annex_c_contribution"
SLOT_COMPLETE_SET: Final[str] = "complete_set_attestation"
SLOT_ORIGINALITY_PROOF: Final[str] = "originality_proof"
SLOT_PEDAGOGICAL_VALIDITY: Final[str] = "pedagogical_validity_proof"

# material_type -> row_id from criterion_b_annex
MATERIAL_TEXTBOOK: Final[str] = "textbook"
MATERIAL_MODULE: Final[str] = "module"
MATERIAL_MANUAL: Final[str] = "instructional_manual"
MATERIAL_MULTIMEDIA: Final[str] = "multimedia"

ROW_TO_MATERIAL: Final[dict[str, str]] = {
    "textbook": MATERIAL_TEXTBOOK,
    "module": MATERIAL_MODULE,
    "instructional_manual": MATERIAL_MANUAL,
    "multimedia": MATERIAL_MULTIMEDIA,
}


def required_slots(
    material_type: str,
    *,
    authorship: str,
) -> tuple[str, ...]:
    """Return required evidence slot IDs for a claim (excludes primary file row itself)."""
    auth = (authorship or "sole").strip().lower()
    base: list[str] = [
        SLOT_IMDC_APPROVAL,
        SLOT_APPROVED_SYLLABUS,
        SLOT_LIBRARY_CERTIFICATION,
    ]
    if auth == "co":
        base.append(SLOT_ANNEX_C_CONTRIBUTION)
    if material_type in (MATERIAL_MODULE, MATERIAL_MANUAL):
        base.append(SLOT_COMPLETE_SET)
    if material_type == MATERIAL_MULTIMEDIA:
        base.extend([SLOT_ORIGINALITY_PROOF, SLOT_PEDAGOGICAL_VALIDITY])
    return tuple(base)


def slot_label(slot_id: str) -> str:
    labels = {
        SLOT_PRIMARY_MATERIAL: "Instructional material (primary file)",
        SLOT_IMDC_APPROVAL: "IMDC or equivalent evaluation and approval for use",
        SLOT_APPROVED_SYLLABUS: "Approved syllabus or course guide listing the material",
        SLOT_LIBRARY_CERTIFICATION: "Librarian certification of library holdings",
        SLOT_ANNEX_C_CONTRIBUTION: "Annex C — Certificate of Contribution Form_IM",
        SLOT_COMPLETE_SET: "Complete stand-alone module/manual or complete set attestation",
        SLOT_ORIGINALITY_PROOF: "Proof of originality (concept note, project files, or raw sources)",
        SLOT_PEDAGOGICAL_VALIDITY: "Proof of pedagogical validity (expert review or student feedback)",
    }
    return labels.get(slot_id, slot_id)
