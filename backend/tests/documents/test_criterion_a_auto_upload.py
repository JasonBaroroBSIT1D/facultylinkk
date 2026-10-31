"""Synthetic tests for Criterion A auto SET/SEF classification (no database)."""

from __future__ import annotations

from documents.criterion_a_upload import (
    CRITERION_A_AUTO_INDICATOR_ID,
    classification_status_from_composition,
    normalize_upload_classification,
)
from documents.ocr.set_sef_metadata import (
    apply_set_sef_to_extracted_info,
    classify_document_composition,
    parse_set_sef_metadata_multi,
)

SET_ONLY = """
Student Evaluation of Teaching
Faculty Name: Ana Reyes
Academic Year 2024-2025
First Semester
Overall Rating: 90.0 / 100
"""

SEF_ONLY = """
Supervisor Evaluation of Faculty
Faculty: Ben Cruz
AY 2025-2026
2nd Semester
Overall Evaluation Score: 88 / 100
"""

MIXED = SET_ONLY + "\n\n---\n\n" + SEF_ONLY.replace("Ben Cruz", "Ana Reyes")

GARBAGE = "Faculty handbook appendix — no evaluation tables."


def test_normalize_criterion_a_without_indicator():
    kra, crit, ind = normalize_upload_classification(
        kra_id="kra1",
        criterion_id="kra1-a",
        indicator_id="",
    )
    assert crit == "kra1-a"
    assert ind == CRITERION_A_AUTO_INDICATOR_ID


def test_normalize_criterion_a_legacy_set_indicator():
    _, _, ind = normalize_upload_classification(
        kra_id="kra1",
        criterion_id="kra1-a",
        indicator_id="kra1-a-student",
    )
    assert ind == "kra1-a-student"


def test_auto_upload_set_only_classified():
    info = apply_set_sef_to_extracted_info(
        {},
        text=SET_ONLY,
        indicator_id=CRITERION_A_AUTO_INDICATOR_ID,
        criterion_id="kra1-a",
        extraction_method="test",
    )
    multi = parse_set_sef_metadata_multi(SET_ONLY)
    assert classify_document_composition(multi) == "SET only"
    assert info["Document classification status"] == "classified"
    assert info["Document evaluation composition"] == "SET only"
    assert info["Indicator verification status"] == "UNDETERMINED"
    assert info.get("OCR-based indicator routing") == "automatic"


def test_auto_upload_sef_only_classified():
    info = apply_set_sef_to_extracted_info(
        {},
        text=SEF_ONLY,
        indicator_id=CRITERION_A_AUTO_INDICATOR_ID,
        criterion_id="kra1-a",
        extraction_method="test",
    )
    assert info["Document evaluation composition"] == "SEF only"
    assert info["Document classification status"] == "classified"


def test_auto_upload_mixed_composition():
    info = apply_set_sef_to_extracted_info(
        {},
        text=MIXED,
        indicator_id=CRITERION_A_AUTO_INDICATOR_ID,
        criterion_id="kra1-a",
        extraction_method="test",
    )
    multi = parse_set_sef_metadata_multi(MIXED)
    assert classify_document_composition(multi) == "Mixed SET and SEF"
    assert info["Document evaluation composition"] == "Mixed SET and SEF"
    assert info["Document classification status"] == "classified"
    assert int(info["Detected evaluation section count"]) >= 2


def test_auto_upload_uncertain_needs_classification():
    info = apply_set_sef_to_extracted_info(
        {},
        text=GARBAGE,
        indicator_id=CRITERION_A_AUTO_INDICATOR_ID,
        criterion_id="kra1-a",
        extraction_method="test",
    )
    assert info["Document classification status"] == "needs_classification"
    assert info.get("Validation status") == "Needs Classification"
    assert classification_status_from_composition(
        "No evaluation sections detected", 0
    ) == "needs_classification"
