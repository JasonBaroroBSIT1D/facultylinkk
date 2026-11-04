"""Criterion C — Creative Works (Annex A pp. 84–92) evidence checklist slots — JC Sec. 25–27."""

from __future__ import annotations

from typing import Final

from kra_configuration.kra2_annex import CRITERION_C_ID

SLOT_PRIMARY_OUTPUT: Final[str] = "primary_output"
SLOT_CONTRIBUTION_CERT: Final[str] = "contribution_certificate"
SLOT_INVITATION_ACCEPTANCE: Final[str] = "invitation_acceptance"
SLOT_PERFORMANCE_PROOF: Final[str] = "performance_proof"
SLOT_ROLE_CERTIFICATION: Final[str] = "role_certification"
SLOT_COPYRIGHT_REGISTRATION: Final[str] = "copyright_registration"
SLOT_PUBLISHED_RELEASE: Final[str] = "published_release"
SLOT_PRODUCTION_PROOF: Final[str] = "production_proof"
SLOT_PROGRAM_DOCUMENTATION: Final[str] = "program_documentation"
SLOT_MEDIA_DOCUMENTATION: Final[str] = "media_documentation"
SLOT_DESIGN_PORTFOLIO: Final[str] = "design_portfolio"
SLOT_EXHIBITION_CATALOG: Final[str] = "exhibition_catalog"
SLOT_GALLERY_DOCUMENTATION: Final[str] = "gallery_documentation"
SLOT_EXHIBITION_DOCUMENTATION: Final[str] = "exhibition_documentation"
SLOT_AUTHORSHIP_DOCUMENTATION: Final[str] = "authorship_documentation"
SLOT_ORGANIZING_BODY_INFO: Final[str] = "organizing_body_info"
SLOT_FESTIVAL_PROGRAM: Final[str] = "festival_program"
SLOT_EDITORIAL_REVIEW: Final[str] = "editorial_review"
SLOT_PUBLISHER_CREDIBILITY: Final[str] = "publisher_credibility"

_CO: tuple[str, ...] = (SLOT_PRIMARY_OUTPUT, SLOT_CONTRIBUTION_CERT)
_COMPOSED_SOLE: tuple[str, ...] = (
    SLOT_PRIMARY_OUTPUT,
    SLOT_INVITATION_ACCEPTANCE,
    SLOT_PERFORMANCE_PROOF,
)
_ARRANGEMENT_SOLE: tuple[str, ...] = _COMPOSED_SOLE + (SLOT_ROLE_CERTIFICATION,)
_MUSIC_PROD_SOLE: tuple[str, ...] = (
    SLOT_PRIMARY_OUTPUT,
    SLOT_COPYRIGHT_REGISTRATION,
    SLOT_PUBLISHED_RELEASE,
    SLOT_ROLE_CERTIFICATION,
)
_PERF_SOLE: tuple[str, ...] = (
    SLOT_PRIMARY_OUTPUT,
    SLOT_INVITATION_ACCEPTANCE,
    SLOT_ROLE_CERTIFICATION,
)
_DANCE_PERF: tuple[str, ...] = (SLOT_PRIMARY_OUTPUT, SLOT_ROLE_CERTIFICATION)
_PLAYWRIGHT_SOLE: tuple[str, ...] = (
    SLOT_PRIMARY_OUTPUT,
    SLOT_COPYRIGHT_REGISTRATION,
    SLOT_INVITATION_ACCEPTANCE,
    SLOT_PRODUCTION_PROOF,
    SLOT_ROLE_CERTIFICATION,
)
_DIRECTING_ACTING: tuple[str, ...] = (
    SLOT_PRIMARY_OUTPUT,
    SLOT_PROGRAM_DOCUMENTATION,
    SLOT_MEDIA_DOCUMENTATION,
    SLOT_ROLE_CERTIFICATION,
)
_PROD_DESIGN: tuple[str, ...] = (
    SLOT_PRIMARY_OUTPUT,
    SLOT_DESIGN_PORTFOLIO,
    SLOT_MEDIA_DOCUMENTATION,
    SLOT_PROGRAM_DOCUMENTATION,
    SLOT_ROLE_CERTIFICATION,
)
_VISUAL: tuple[str, ...] = (
    SLOT_PRIMARY_OUTPUT,
    SLOT_INVITATION_ACCEPTANCE,
    SLOT_EXHIBITION_CATALOG,
    SLOT_GALLERY_DOCUMENTATION,
    SLOT_ROLE_CERTIFICATION,
)
_ARCH_DESIGN: tuple[str, ...] = (
    SLOT_PRIMARY_OUTPUT,
    SLOT_INVITATION_ACCEPTANCE,
    SLOT_EXHIBITION_DOCUMENTATION,
    SLOT_AUTHORSHIP_DOCUMENTATION,
    SLOT_ORGANIZING_BODY_INFO,
)
_FILM: tuple[str, ...] = (
    SLOT_PRIMARY_OUTPUT,
    SLOT_INVITATION_ACCEPTANCE,
    SLOT_FESTIVAL_PROGRAM,
    SLOT_ROLE_CERTIFICATION,
)
_LITERARY_SOLE: tuple[str, ...] = (
    SLOT_PRIMARY_OUTPUT,
    SLOT_EDITORIAL_REVIEW,
    SLOT_PUBLISHER_CREDIBILITY,
)

_CRITERION_C_SLOTS: dict[str, tuple[str, ...]] = {
    "kra2-c-music-comp-sole": _COMPOSED_SOLE,
    "kra2-c-music-comp-co": _CO,
    "kra2-c-music-arr-sole": _ARRANGEMENT_SOLE,
    "kra2-c-music-arr-co": _CO,
    "kra2-c-music-perf": _PERF_SOLE,
    "kra2-c-conducting": _PERF_SOLE,
    "kra2-c-music-prod-sole": _MUSIC_PROD_SOLE,
    "kra2-c-music-prod-co": _CO,
    "kra2-c-choreo-sole": _COMPOSED_SOLE + (SLOT_ROLE_CERTIFICATION,),
    "kra2-c-choreo-co": _CO,
    "kra2-c-dance-perf": _DANCE_PERF,
    "kra2-c-playwright-sole": _PLAYWRIGHT_SOLE,
    "kra2-c-playwright-co": _CO,
    "kra2-c-directing": _DIRECTING_ACTING,
    "kra2-c-acting": _DIRECTING_ACTING,
    "kra2-c-prod-design": _PROD_DESIGN,
    "kra2-c-visual": _VISUAL,
    "kra2-c-arch-design": _ARCH_DESIGN,
    "kra2-c-film": _FILM,
    "kra2-c-novel-sole": _LITERARY_SOLE,
    "kra2-c-novel-co": _CO,
    "kra2-c-story-sole": _LITERARY_SOLE,
    "kra2-c-story-co": _CO,
    "kra2-c-poetry": _LITERARY_SOLE,
    "kra2-c-essay": _LITERARY_SOLE,
}

_SLOT_LABELS: dict[str, str] = {
    SLOT_PRIMARY_OUTPUT: "Primary creative or performance evidence (PDF)",
    SLOT_CONTRIBUTION_CERT: "Certificate of Contribution — Creative Works (Annex I)",
    SLOT_INVITATION_ACCEPTANCE: "Proof of invitation or acceptance",
    SLOT_PERFORMANCE_PROOF: "Proof of performance or first performance",
    SLOT_ROLE_CERTIFICATION: "Certification of role (director, organizer, dean, etc.)",
    SLOT_COPYRIGHT_REGISTRATION: "Copyright registration",
    SLOT_PUBLISHED_RELEASE: "Published release or distribution details",
    SLOT_PRODUCTION_PROOF: "Proof of production or staging",
    SLOT_PROGRAM_DOCUMENTATION: "Program, playbill, or event flyer",
    SLOT_MEDIA_DOCUMENTATION: "Photo or video documentation",
    SLOT_DESIGN_PORTFOLIO: "Design portfolio or proposal",
    SLOT_EXHIBITION_CATALOG: "Exhibition catalog, brochure, or program",
    SLOT_GALLERY_DOCUMENTATION: "Gallery or venue information",
    SLOT_EXHIBITION_DOCUMENTATION: "Exhibition or competition documentation",
    SLOT_AUTHORSHIP_DOCUMENTATION: "Authorship documentation",
    SLOT_ORGANIZING_BODY_INFO: "Organizing body or gallery profile",
    SLOT_FESTIVAL_PROGRAM: "Festival program or screening announcement",
    SLOT_EDITORIAL_REVIEW: "Publisher guidelines and editorial review evidence",
    SLOT_PUBLISHER_CREDIBILITY: "Proof of publisher credibility",
}


def is_criterion_c_indicator(indicator_id: str | None) -> bool:
    iid = (indicator_id or "").strip()
    return iid.startswith(f"{CRITERION_C_ID}-")


def criterion_c_required_slots(indicator_id: str) -> tuple[str, ...]:
    iid = (indicator_id or "").strip()
    if iid in _CRITERION_C_SLOTS:
        return _CRITERION_C_SLOTS[iid]
    if is_criterion_c_indicator(iid):
        return (SLOT_PRIMARY_OUTPUT,)
    return ()


def criterion_c_slot_label(slot_id: str, *, indicator_id: str = "") -> str:
    _ = indicator_id
    return _SLOT_LABELS.get(slot_id, slot_id.replace("_", " "))
