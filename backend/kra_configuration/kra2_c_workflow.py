"""KRA II Criterion C — workflow subfamilies, metadata labels, OCR routing (25 indicators)."""

from __future__ import annotations

from kra_configuration.kra2_annex import CRITERION_C_ID
from kra_configuration.kra2_indicator_registry import contribution_mode, indicator_row, workflow_family

# Annex A creative-work groupings (Sec. 25–27); not separate scoring rules.
SUBFAMILY_MUSIC_COMPOSITION = "music_composition"
SUBFAMILY_MUSIC_PRODUCTION = "music_production"
SUBFAMILY_MUSIC_PERFORMANCE = "music_performance"
SUBFAMILY_DANCE_CHOREOGRAPHY = "dance_choreography"
SUBFAMILY_DANCE_PERFORMANCE = "dance_performance"
SUBFAMILY_THEATER = "theater"
SUBFAMILY_THEATER_PERFORMANCE = "theater_performance"
SUBFAMILY_VISUAL_ARTS = "visual_arts"
SUBFAMILY_DESIGN_EXHIBITION = "design_exhibition"
SUBFAMILY_FILM = "film"
SUBFAMILY_LITERARY = "literary"

_METADATA_PROFILES: dict[str, dict[str, str]] = {
    SUBFAMILY_MUSIC_COMPOSITION: {
        "outputTitle": "Title of composition or arrangement",
        "authorsLine": "Composer or arranger",
        "outputVenue": "Venue, organizer, or publisher",
        "publicationDate": "Date of first performance or publication",
    },
    SUBFAMILY_MUSIC_PRODUCTION: {
        "outputTitle": "Title of produced work",
        "authorsLine": "Producer or creator",
        "outputVenue": "Label, platform, or release venue",
        "publicationDate": "Release or publication date",
    },
    SUBFAMILY_MUSIC_PERFORMANCE: {
        "outputTitle": "Title of performance",
        "authorsLine": "Performer or conductor",
        "outputVenue": "Performance venue or organizer",
        "publicationDate": "Date of performance",
    },
    SUBFAMILY_DANCE_CHOREOGRAPHY: {
        "outputTitle": "Title of choreography",
        "authorsLine": "Choreographer",
        "outputVenue": "Venue or organizer",
        "publicationDate": "Date of first performance",
    },
    SUBFAMILY_DANCE_PERFORMANCE: {
        "outputTitle": "Title of dance performance",
        "authorsLine": "Dancer or performer",
        "outputVenue": "Performance venue or organizer",
        "publicationDate": "Date of performance",
    },
    SUBFAMILY_THEATER: {
        "outputTitle": "Title of production or role",
        "authorsLine": "Playwright or creator",
        "outputVenue": "Theater, organizer, or festival",
        "publicationDate": "Date of production or publication",
    },
    SUBFAMILY_THEATER_PERFORMANCE: {
        "outputTitle": "Title of performance",
        "authorsLine": "Performer or director",
        "outputVenue": "Performance venue or organizer",
        "publicationDate": "Date of performance",
    },
    SUBFAMILY_VISUAL_ARTS: {
        "outputTitle": "Title of artwork",
        "authorsLine": "Artist or creator",
        "outputVenue": "Gallery or exhibition venue",
        "publicationDate": "Exhibition date",
    },
    SUBFAMILY_DESIGN_EXHIBITION: {
        "outputTitle": "Title of design or project",
        "authorsLine": "Designer or creator",
        "outputVenue": "Exhibition, competition, or organizer",
        "publicationDate": "Exhibition or competition date",
    },
    SUBFAMILY_FILM: {
        "outputTitle": "Film title",
        "authorsLine": "Director or creator",
        "outputVenue": "Festival, venue, or organizer",
        "publicationDate": "Screening or release date",
    },
    SUBFAMILY_LITERARY: {
        "outputTitle": "Title of literary work",
        "authorsLine": "Author or contributor",
        "outputVenue": "Publisher or publication",
        "publicationDate": "Publication date",
    },
}


def is_criterion_c_indicator(indicator_id: str | None) -> bool:
    return (indicator_id or "").strip().startswith(f"{CRITERION_C_ID}-")


def criterion_c_subfamily(indicator_id: str) -> str:
    iid = (indicator_id or "").strip()
    if not is_criterion_c_indicator(iid):
        return SUBFAMILY_LITERARY
    if iid.startswith("kra2-c-music-comp-") or iid.startswith("kra2-c-music-arr-"):
        return SUBFAMILY_MUSIC_COMPOSITION
    if iid.startswith("kra2-c-music-prod-"):
        return SUBFAMILY_MUSIC_PRODUCTION
    if iid.startswith("kra2-c-music-perf") or iid.startswith("kra2-c-conducting"):
        return SUBFAMILY_MUSIC_PERFORMANCE
    if iid.startswith("kra2-c-choreo-"):
        return SUBFAMILY_DANCE_CHOREOGRAPHY
    if iid.startswith("kra2-c-dance-perf"):
        return SUBFAMILY_DANCE_PERFORMANCE
    if iid.startswith("kra2-c-directing") or iid.startswith("kra2-c-acting"):
        return SUBFAMILY_THEATER_PERFORMANCE
    if iid.startswith("kra2-c-playwright-") or iid.startswith("kra2-c-prod-design"):
        return SUBFAMILY_THEATER
    if iid.startswith("kra2-c-visual"):
        return SUBFAMILY_VISUAL_ARTS
    if iid.startswith("kra2-c-arch-design"):
        return SUBFAMILY_DESIGN_EXHIBITION
    if iid.startswith("kra2-c-film"):
        return SUBFAMILY_FILM
    if iid.startswith("kra2-c-novel-") or iid.startswith("kra2-c-story-") or iid.startswith("kra2-c-poetry") or iid.startswith(
        "kra2-c-essay"
    ):
        return SUBFAMILY_LITERARY
    return SUBFAMILY_LITERARY


def criterion_c_metadata_label(field_id: str, indicator_id: str) -> str:
    sub = criterion_c_subfamily(indicator_id)
    profile = _METADATA_PROFILES.get(sub, _METADATA_PROFILES[SUBFAMILY_LITERARY])
    if field_id == "declaredContributionPercent":
        return "Your verified contribution (%)"
    return profile.get(field_id, field_id.replace("_", " ").title())


def criterion_c_ocr_parser_id(indicator_id: str) -> str:
    """Route Tesseract post-parse logic for Criterion C."""
    sub = criterion_c_subfamily(indicator_id)
    if sub == SUBFAMILY_LITERARY:
        return "literary"
    if sub == SUBFAMILY_FILM:
        return "film"
    if sub in (SUBFAMILY_VISUAL_ARTS, SUBFAMILY_DESIGN_EXHIBITION):
        return "exhibition"
    if sub in (SUBFAMILY_MUSIC_COMPOSITION, SUBFAMILY_MUSIC_PRODUCTION):
        return "music_work"
    if sub in (
        SUBFAMILY_MUSIC_PERFORMANCE,
        SUBFAMILY_DANCE_PERFORMANCE,
        SUBFAMILY_DANCE_CHOREOGRAPHY,
        SUBFAMILY_THEATER_PERFORMANCE,
    ):
        return "performance"
    return "creative"


def all_criterion_c_indicators() -> list[dict]:
    from kra_configuration.kra2_indicator_registry import indicators_for_criterion

    return indicators_for_criterion(CRITERION_C_ID)


def coverage_row(indicator_id: str) -> dict[str, str]:
    from documents.kra2_evidence.kra2_c_evidence_slots import criterion_c_required_slots
    from documents.kra2_evidence.ocr_profiles import ocr_keys_for_indicator
    from kra_configuration.kra2_indicator_registry import metadata_field_ids

    row = indicator_row(indicator_id) or {}
    sub = criterion_c_subfamily(indicator_id)
    return {
        "indicatorId": indicator_id,
        "name": str(row.get("name") or indicator_id),
        "subfamily": sub,
        "workflowFamily": workflow_family(indicator_id),
        "contribution": contribution_mode(indicator_id),
        "points": str(row.get("points") or ""),
        "maxPoints": str(row.get("maxPoints") or ""),
        "metadataFields": ",".join(metadata_field_ids(indicator_id)),
        "ocrKeys": ",".join(ocr_keys_for_indicator(indicator_id)),
        "ocrParser": criterion_c_ocr_parser_id(indicator_id),
        "evidenceSlots": ",".join(criterion_c_required_slots(indicator_id)),
    }
