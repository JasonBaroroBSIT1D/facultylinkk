"""54-indicator OCR metadata profile and parser routing coverage."""

from __future__ import annotations

import pytest

from documents.kra2_evidence.ocr_extraction import (
    build_extraction_payload,
    extract_fields_for_indicator,
    is_metadata_label_value,
    validate_extracted_field,
)
from documents.kra2_evidence.ocr_profiles import (
    coverage_rows,
    filter_extracted_fields,
    ocr_keys_for_indicator,
)
from kra_configuration.kra2_indicator_registry import (
    all_indicators,
    metadata_field_ids,
    workflow_family,
)

_CATALOG_IDS = [row["id"] for row in all_indicators()]

# Minimal labeled snippets per workflow family (not production metadata).
_FAMILY_SNIPPETS: dict[str, str] = {
    "publication_output": """
Article title
Sample Research Output for OCR Routing
Authors
Alex Rivera
Journal
Journal of Sample Studies
Publication date
2024-06-01
DOI
10.1234/sample.2024.001
""",
    "citation_impact": """
Title of cited work
Prior Study on Sample Topic
Citation context
Cited in Journal of Sample Studies, vol. 12, 2024.
Publication date
2024-03-10
""",
    "invention_ip": """
Invention title
Sample Device for Testing
Inventor(s)
Alex Rivera
Application No.
SAMPLE-APP-2024-0001
Filing date
2024-01-15
""",
    "commercialization": """
Title of work
Licensed Sample Product
Author(s)
Alex Rivera
Organization
Sample Tech Transfer Office
Publication date
2024-09-01
""",
    "creative_work": """
Title of creative work
Sample Visual Composition
Author(s) / creator(s)
Alex Rivera
Venue
City Gallery (TEST)
Exhibition date
2024-07-20
""",
    "performance_work": """
Performance title
Sample Stage Production
Creator(s)
Alex Rivera
Presented at
Sample Theater (TEST)
Performance date
2024-05-05
""",
}


def test_coverage_matrix_has_54_indicators():
    rows = coverage_rows()
    assert len(rows) == 54
    ids = {r["indicatorId"] for r in rows}
    assert ids == set(_CATALOG_IDS)


@pytest.mark.parametrize("indicator_id", _CATALOG_IDS)
def test_metadata_fields_subset_of_ocr_keys(indicator_id: str):
    required = frozenset(metadata_field_ids(indicator_id)) - {"declaredContributionPercent"}
    allowed = frozenset(ocr_keys_for_indicator(indicator_id))
    missing = required - allowed
    assert not missing, f"{indicator_id} requires {missing} not in OCR profile"


@pytest.mark.parametrize("indicator_id", _CATALOG_IDS)
def test_extract_empty_text_returns_dict(indicator_id: str):
    assert extract_fields_for_indicator("", indicator_id) == {}


@pytest.mark.parametrize("indicator_id", _CATALOG_IDS)
def test_family_snippet_yields_title(indicator_id: str):
    family = workflow_family(indicator_id)
    text = _FAMILY_SNIPPETS[family]
    fields = extract_fields_for_indicator(text, indicator_id)
    payload = build_extraction_payload(fields, indicator_id=indicator_id)
    title = payload["fields"].get("outputTitle", {}).get("value", "")
    assert title
    assert not is_metadata_label_value(title, field_id="outputTitle")
    for key, block in payload["fields"].items():
        val = block.get("value", "")
        cleaned, status = validate_extracted_field(key, val, indicator_id)
        assert status != "rejected", f"{indicator_id}.{key}={val!r}"


@pytest.mark.parametrize("indicator_id", _CATALOG_IDS)
def test_filter_drops_unknown_keys(indicator_id: str):
    raw = {
        "outputTitle": "Sample",
        "authorsLine": "Alex Rivera",
        "unexpectedField": "drop me",
    }
    filtered = filter_extracted_fields(raw, indicator_id)
    assert "unexpectedField" not in filtered


def test_negative_label_values_rejected_for_all_families():
    bad = "Journal / publisher / issuing organization /"
    for family in _FAMILY_SNIPPETS:
        assert is_metadata_label_value(bad, field_id="outputVenue")
    cleaned, status = validate_extracted_field("outputVenue", bad, "kra2-a-book-sole")
    assert status == "rejected" or not cleaned
