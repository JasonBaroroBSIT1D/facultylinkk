"""Indicator-driven KRA II workflow configuration (delegates to registry)."""

from __future__ import annotations

from kra_configuration.kra2_indicator_registry import (
    contribution_mode,
    metadata_field_ids,
    patent_stage_key,
    scoring_group,
    scoring_group_max,
    user_facing_description,
    user_facing_title,
    workflow_family,
)
def primary_upload_label(indicator_id: str) -> str:
    family = workflow_family(indicator_id)
    if family == "invention_ip":
        return "Upload your proof document (certificate, registration, or patent copy)"
    if family == "citation_impact":
        return "Upload citation evidence (citing document or index proof)"
    if family == "commercialization":
        return "Upload proof of commercialization"
    if family in ("creative_work", "performance_work"):
        return "Upload your creative work evidence"
    return "Upload your published output (PDF)"


def metadata_labels() -> dict[str, str]:
    return {
        "outputTitle": "Title of work or accomplishment",
        "authorsLine": "Author or inventor name(s)",
        "outputVenue": "Journal, venue, publisher, or registry",
        "publicationDate": "Publication or registration date",
        "publicationReference": "DOI or reference number (optional)",
        "registrationNumber": "Registration or patent number",
        "registrationDate": "Registration date",
        "citationContext": "Describe the citing publication or index",
        "declaredContributionPercent": "Your contribution (%)",
        "indexingAttestation": "Indexing or eligibility note (optional)",
    }
