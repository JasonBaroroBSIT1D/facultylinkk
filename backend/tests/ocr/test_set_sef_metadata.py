"""SET/SEF metadata parsing and indicator verification (no database)."""

from __future__ import annotations

from documents.ocr.set_sef_metadata import (
    apply_set_sef_to_extracted_info,
    parse_set_sef_metadata,
    verify_selected_indicator,
)

SEF_SAMPLE = """
Supervisor Evaluation of Teaching
Faculty: Jason Baroro
Department of Computer Science
Academic Year 2025-2026
2nd Semester
Overall Evaluation Score: 95.00 / 100
"""

SET_SAMPLE = """
Student Evaluation of Teaching
Faculty Name: Maria Santos
AY 2024-2025
First Semester
Overall Rating: 88.5 / 100
"""


def test_sef_sample_extracts_jason_baroro_fields():
    parsed = parse_set_sef_metadata(SEF_SAMPLE)
    assert parsed.faculty_name == "Jason Baroro"
    assert parsed.academic_year == "2025-2026"
    assert parsed.semester == "2nd Semester"
    assert parsed.overall_rating == "95.00 / 100"
    assert parsed.rating_scale == "100"
    assert parsed.detected_kind == "SEF"
    assert "overall rating" not in parsed.missing_fields


def test_sef_indicator_match():
    parsed = parse_set_sef_metadata(SEF_SAMPLE)
    assert verify_selected_indicator("kra1-a-supervisor", parsed) == "MATCH"


def test_set_indicator_match():
    parsed = parse_set_sef_metadata(SET_SAMPLE)
    assert parsed.detected_kind == "SET"
    assert verify_selected_indicator("kra1-a-student", parsed) == "MATCH"


def test_set_sef_mismatch():
    parsed = parse_set_sef_metadata(SEF_SAMPLE)
    assert verify_selected_indicator("kra1-a-student", parsed) == "POSSIBLE_MISMATCH"


def test_apply_populates_reviewer_keys():
    info = apply_set_sef_to_extracted_info(
        {},
        text=SEF_SAMPLE,
        indicator_id="kra1-a-supervisor",
        extraction_method="pdf_text",
    )
    assert info["Faculty name"] == "Jason Baroro"
    assert info["Extracted names"] == "Jason Baroro"
    assert info["Extracted rating"] == "95.00 / 100"
    assert info["Academic year"] == "2025-2026"
    assert info["Indicator verification status"] == "MATCH"
    assert info["SET/SEF extraction status"] == "complete"


def test_unreadable_text_undetermined():
    parsed = parse_set_sef_metadata("   ")
    assert parsed.verification_status == "UNDETERMINED"
    assert parsed.missing_fields
