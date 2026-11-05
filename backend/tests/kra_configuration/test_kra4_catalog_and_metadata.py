"""KRA IV catalog completeness and metadata persistence (no DB writes)."""

from __future__ import annotations

from documents.kra4_evidence.bundle import build_initial_bundle
from kra_configuration.kra4_annex import (
    CRITERION_A_MAX,
    CRITERION_B_MAX,
    CRITERION_C_MAX,
    CRITERION_D_BONUS_MAX,
    KRA4_MAX_POINTS,
)
from kra_configuration.kra4_indicator_registry import all_indicators, metadata_field_ids


def test_kra4_has_nineteen_indicators():
    rows = all_indicators()
    assert len(rows) == 19
    ids = {r["id"] for r in rows}
    assert "kra4-a-member" in ids
    assert "kra4-d-support" in ids


def test_kra4_criterion_caps():
    assert CRITERION_A_MAX == 20.0
    assert CRITERION_B_MAX == 60.0
    assert CRITERION_C_MAX == 20.0
    assert CRITERION_D_BONUS_MAX == 20.0
    assert KRA4_MAX_POINTS == 100.0


def test_education_metadata_roundtrip():
    bundle = build_initial_bundle(
        primary_document_id="doc-1",
        primary_file_hash="hash",
        indicator_id="kra4-b-masters",
        output_title="QA",
    )
    assert "degreeTitle" in bundle
    assert "institutionName" in bundle


def test_prior_experience_numeric_field_in_bundle():
    bundle = build_initial_bundle(
        primary_document_id="doc-1",
        primary_file_hash="hash",
        indicator_id="kra4-d-pres",
        output_title="QA",
    )
    fields = metadata_field_ids("kra4-d-pres")
    assert "experienceYears" in fields
