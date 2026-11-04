"""Criterion B (Annex A pp. 81–84) evidence checklist slots — JC 01 s. 2026 Sections 22–24."""

from __future__ import annotations

from typing import Final

from kra_configuration.kra2_annex import CRITERION_B_ID
from kra_configuration.kra2_indicator_registry import contribution_mode

SLOT_PRIMARY_OUTPUT: Final[str] = "primary_output"
SLOT_CONTRIBUTION_CERT: Final[str] = "contribution_certificate"
SLOT_INVENTION_PHOTO: Final[str] = "invention_photo"
SLOT_PRESIDENT_SPECIAL_ORDER: Final[str] = "president_special_order"
SLOT_PRODUCT_PHOTO: Final[str] = "product_photo"
SLOT_PATENT_CERTIFICATE: Final[str] = "patent_certificate"
SLOT_LICENSING_OR_CPR: Final[str] = "licensing_or_cpr_evidence"
SLOT_COMMERCIALIZATION_PROOF: Final[str] = "commercialization_proof"
SLOT_RD_ITSO_CERTIFICATION: Final[str] = "rd_itso_certification"
SLOT_PROJECT_SUMMARY: Final[str] = "project_summary"
SLOT_SOFTWARE_DOCUMENTATION: Final[str] = "software_documentation"
SLOT_UTILIZATION_CERTIFICATION: Final[str] = "utilization_certification"
SLOT_UPDATE_DESCRIPTION: Final[str] = "software_update_description"
SLOT_REGISTRATION_DEPOSIT: Final[str] = "registration_deposit_evidence"

# Documentary sets derived from `kra2_indicators.json` evidenceHints (Annex A B.1–B.2).
_PATENT_SOLE: tuple[str, ...] = (
    SLOT_PRIMARY_OUTPUT,
    SLOT_INVENTION_PHOTO,
    SLOT_PRESIDENT_SPECIAL_ORDER,
)
_PATENT_CO: tuple[str, ...] = (SLOT_PRIMARY_OUTPUT, SLOT_CONTRIBUTION_CERT)
_COMM: tuple[str, ...] = (
    SLOT_PRODUCT_PHOTO,
    SLOT_PATENT_CERTIFICATE,
    SLOT_LICENSING_OR_CPR,
    SLOT_COMMERCIALIZATION_PROOF,
    SLOT_RD_ITSO_CERTIFICATION,
)
_UM_ID_SOLE: tuple[str, ...] = (
    SLOT_PRIMARY_OUTPUT,
    SLOT_INVENTION_PHOTO,
    SLOT_PRESIDENT_SPECIAL_ORDER,
)
_UM_ID_CO: tuple[str, ...] = (SLOT_PRIMARY_OUTPUT, SLOT_CONTRIBUTION_CERT)
_SW_NEW_SOLE: tuple[str, ...] = (
    SLOT_PRESIDENT_SPECIAL_ORDER,
    SLOT_PROJECT_SUMMARY,
    SLOT_SOFTWARE_DOCUMENTATION,
    SLOT_PRIMARY_OUTPUT,
    SLOT_UTILIZATION_CERTIFICATION,
)
# Co-developer: same documentary set as sole + Annex G (catalog: "Same software evidence").
_SW_NEW_CO: tuple[str, ...] = _SW_NEW_SOLE + (SLOT_CONTRIBUTION_CERT,)
_SW_UPD_SOLE: tuple[str, ...] = (
    SLOT_PRESIDENT_SPECIAL_ORDER,
    SLOT_PROJECT_SUMMARY,
    SLOT_PRIMARY_OUTPUT,
    SLOT_UTILIZATION_CERTIFICATION,
    SLOT_UPDATE_DESCRIPTION,
)
_SW_UPD_CO: tuple[str, ...] = _SW_UPD_SOLE + (SLOT_CONTRIBUTION_CERT,)
_VARIETY_SOLE: tuple[str, ...] = (
    SLOT_PRESIDENT_SPECIAL_ORDER,
    SLOT_REGISTRATION_DEPOSIT,
)
# Co-developer: registration/deposit + Annex H (no separate President SO in catalog hints).
_VARIETY_CO: tuple[str, ...] = (SLOT_REGISTRATION_DEPOSIT, SLOT_CONTRIBUTION_CERT)

_CRITERION_B_SLOTS: dict[str, tuple[str, ...]] = {
    "kra2-b-patent-a-sole": _PATENT_SOLE,
    "kra2-b-patent-p-sole": _PATENT_SOLE,
    "kra2-b-patent-g-sole": _PATENT_SOLE,
    "kra2-b-patent-a-co": _PATENT_CO,
    "kra2-b-patent-p-co": _PATENT_CO,
    "kra2-b-patent-g-co": _PATENT_CO,
    "kra2-b-comm-local": _COMM,
    "kra2-b-comm-intl": _COMM,
    "kra2-b-um-sole": _UM_ID_SOLE,
    "kra2-b-id-sole": _UM_ID_SOLE,
    "kra2-b-um-co": _UM_ID_CO,
    "kra2-b-id-co": _UM_ID_CO,
    "kra2-b-sw-new-sole": _SW_NEW_SOLE,
    "kra2-b-sw-new-co": _SW_NEW_CO,
    "kra2-b-sw-upd-sole": _SW_UPD_SOLE,
    "kra2-b-sw-upd-co": _SW_UPD_CO,
    "kra2-b-variety-sole": _VARIETY_SOLE,
    "kra2-b-variety-co": _VARIETY_CO,
}

_SLOT_LABELS: dict[str, str] = {
    SLOT_PRIMARY_OUTPUT: "Official IP stage or registration document (PDF)",
    SLOT_CONTRIBUTION_CERT: "Certificate of Contribution (Annex F, G, or H as applicable)",
    SLOT_INVENTION_PHOTO: "Photo of the invention or design",
    SLOT_PRESIDENT_SPECIAL_ORDER: "Special Order signed by the President",
    SLOT_PRODUCT_PHOTO: "Photo of the patented product",
    SLOT_PATENT_CERTIFICATE: "Invention Patent Certificate",
    SLOT_LICENSING_OR_CPR: "CPR, licensing, or technology-transfer agreement",
    SLOT_COMMERCIALIZATION_PROOF: "Proof of commercialization",
    SLOT_RD_ITSO_CERTIFICATION: "Certification from Research Director / ITSO",
    SLOT_PROJECT_SUMMARY: "Project summary",
    SLOT_SOFTWARE_DOCUMENTATION: "User manual, design, or source documentation",
    SLOT_UTILIZATION_CERTIFICATION: "End-user utilization certification",
    SLOT_UPDATE_DESCRIPTION: "Description of substantial new functionalities",
    SLOT_REGISTRATION_DEPOSIT: "Registration or deposit evidence (cultivar, breed, or strain)",
}


def is_criterion_b_indicator(indicator_id: str) -> bool:
    return (indicator_id or "").startswith(f"{CRITERION_B_ID}-")


def criterion_b_required_slots(indicator_id: str) -> tuple[str, ...]:
    iid = (indicator_id or "").strip()
    if iid in _CRITERION_B_SLOTS:
        return _CRITERION_B_SLOTS[iid]
    if not is_criterion_b_indicator(iid):
        return (SLOT_PRIMARY_OUTPUT,)
    slots: list[str] = [SLOT_PRIMARY_OUTPUT]
    if contribution_mode(iid) == "declared":
        slots.append(SLOT_CONTRIBUTION_CERT)
    return tuple(slots)


def criterion_b_slot_label(slot_id: str, *, indicator_id: str = "") -> str:
    iid = (indicator_id or "").strip()
    if slot_id == SLOT_CONTRIBUTION_CERT:
        if "sw-" in iid:
            return "Certificate of Contribution (Annex G — software)"
        if "variety" in iid:
            return "Certificate of Contribution (Annex H — cultivar/breed/strain)"
        if iid.endswith("-co") and "patent" in iid:
            return "Certificate of Contribution (Annex F — intellectual property)"
    if slot_id == SLOT_PRIMARY_OUTPUT:
        if iid.startswith("kra2-b-patent-"):
            return "IPOPHL acceptance, publication, or grant document"
        if "comm-" in iid:
            return "Primary commercialization evidence (upload patent certificate here if no separate slot filled)"
        if "sw-" in iid:
            return "Copyright certificate from IPOPHL"
        if "um-" in iid or "id-" in iid:
            return "Utility model or industrial design registration certificate"
    return _SLOT_LABELS.get(slot_id, slot_id.replace("_", " "))
