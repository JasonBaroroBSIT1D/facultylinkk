"""KRA II OCR metadata profiles by workflow family (all 54 indicators)."""

from __future__ import annotations

from kra_configuration.kra2_indicator_registry import (
    FAMILY_CITATION,
    FAMILY_COMMERCIAL,
    FAMILY_CREATIVE,
    FAMILY_INVENTION,
    FAMILY_PERFORMANCE,
    FAMILY_PUBLICATION,
    all_indicators,
    metadata_field_ids,
    workflow_family,
)

# Keys the family parser may produce (optional keys may be omitted).
FAMILY_OCR_KEYS: dict[str, tuple[str, ...]] = {
    FAMILY_PUBLICATION: (
        "outputTitle",
        "authorsLine",
        "outputVenue",
        "journalTitle",
        "publicationDate",
        "publicationReference",
    ),
    FAMILY_CITATION: (
        "outputTitle",
        "citationContext",
        "publicationDate",
        "publicationReference",
    ),
    FAMILY_INVENTION: (
        "outputTitle",
        "authorsLine",
        "registrationNumber",
        "registrationDate",
        "outputVenue",
    ),
    FAMILY_COMMERCIAL: (
        "outputTitle",
        "authorsLine",
        "outputVenue",
        "publicationDate",
        "registrationNumber",
        "registrationDate",
    ),
    FAMILY_CREATIVE: (
        "outputTitle",
        "authorsLine",
        "outputVenue",
        "publicationDate",
        "publicationReference",
    ),
    FAMILY_PERFORMANCE: (
        "outputTitle",
        "authorsLine",
        "outputVenue",
        "publicationDate",
    ),
}

_OPTIONAL_OCR_KEYS = frozenset({"publicationReference", "journalTitle", "outputVenue"})


def ocr_keys_for_indicator(indicator_id: str) -> tuple[str, ...]:
    family = workflow_family(indicator_id)
    return FAMILY_OCR_KEYS.get(family, FAMILY_OCR_KEYS[FAMILY_PUBLICATION])


def filter_extracted_fields(fields: dict[str, str], indicator_id: str) -> dict[str, str]:
    """Keep parser output aligned with bundle metadata for this indicator."""
    allowed = frozenset(ocr_keys_for_indicator(indicator_id))
    required = frozenset(metadata_field_ids(indicator_id))
    out: dict[str, str] = {}
    from kra_configuration.kra2_indicator_registry import contribution_mode

    for key, val in fields.items():
        v = (val or "").strip()
        if not v:
            continue
        if key == "declaredContributionPercent":
            if contribution_mode(indicator_id) == "declared":
                out[key] = v
            continue
        if key not in allowed:
            continue
        if key in _OPTIONAL_OCR_KEYS or key in required:
            out[key] = v
    return out


def coverage_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for row in all_indicators():
        iid = str(row.get("id") or "")
        if not iid:
            continue
        family = workflow_family(iid)
        from kra_configuration.kra2_c_workflow import criterion_c_ocr_parser_id, is_criterion_c_indicator

        parser = criterion_c_ocr_parser_id(iid) if is_criterion_c_indicator(iid) else _parser_name(family)
        rows.append(
            {
                "indicatorId": iid,
                "criterionId": str(row.get("criterionId") or ""),
                "workflowFamily": family,
                "metadataFields": ",".join(metadata_field_ids(iid)),
                "ocrKeys": ",".join(ocr_keys_for_indicator(iid)),
                "parser": parser,
            }
        )
    return rows


def _parser_name(family: str) -> str:
    return {
        FAMILY_PUBLICATION: "publication",
        FAMILY_CITATION: "citation",
        FAMILY_INVENTION: "invention",
        FAMILY_COMMERCIAL: "commercial",
        FAMILY_CREATIVE: "creative",
        FAMILY_PERFORMANCE: "performance",
    }.get(family, "publication")
