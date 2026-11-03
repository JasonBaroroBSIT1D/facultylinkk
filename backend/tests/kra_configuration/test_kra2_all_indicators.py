"""Parameterized coverage for all 54 KRA II catalog indicators."""

from __future__ import annotations

import pytest

from kra_configuration.kra2_annex import criterion_id_for_indicator, is_kra2_indicator
from kra_configuration.kra2_indicator_registry import (
    all_indicators,
    contribution_mode,
    indicator_support_status,
    metadata_field_ids,
    workflow_family,
)
from documents.kra2_evidence.bundle import build_initial_bundle
from documents.kra2_evidence.slots import required_slots
from documents.kra2_evidence.validation import validate_kra2_bundle


@pytest.fixture(scope="module")
def catalog_ids() -> list[str]:
    ids = [row["id"] for row in all_indicators()]
    assert len(ids) == 54
    return ids


_CATALOG_IDS = [row["id"] for row in all_indicators()]


@pytest.mark.parametrize("indicator_id", _CATALOG_IDS)
def test_indicator_registry_mapping(indicator_id: str):
    assert is_kra2_indicator(indicator_id)
    assert criterion_id_for_indicator(indicator_id) in ("kra2-a", "kra2-b", "kra2-c")
    assert workflow_family(indicator_id)
    assert indicator_support_status(indicator_id) in ("PARTIAL", "COMPLETE", "BLOCKED")
    fields = metadata_field_ids(indicator_id)
    assert fields
    slots = required_slots(indicator_id=indicator_id)
    assert "primary_output" in slots
    if contribution_mode(indicator_id) == "declared":
        assert "contribution_certificate" in slots


@pytest.mark.parametrize("indicator_id", _CATALOG_IDS)
def test_initial_bundle_and_validation_incomplete(indicator_id: str):
    bundle = build_initial_bundle(
        primary_document_id="doc_test",
        primary_file_hash="hash",
        indicator_id=indicator_id,
        output_title="Sample",
    )
    validation = validate_kra2_bundle(bundle, indicator_id=indicator_id)
    assert validation["validationStatus"] == "incomplete"
    assert validation["userBlockers"]
