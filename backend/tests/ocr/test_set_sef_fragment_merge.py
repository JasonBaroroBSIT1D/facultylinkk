"""Fragmented SET/SEF OCR merge tests (synthetic text only)."""

from documents.ocr.set_sef_metadata import (
    EXTRACTION_COMPLETE,
    classify_document_composition,
    parse_set_sef_metadata_multi,
)
from documents.teaching_evaluation_sync import dedupe_parsed_drafts, sync_key


def test_fragmented_period_and_rating_merge_to_one():
    block_a = """
Student Evaluation of Teaching
Faculty Name: Maria Santos
Academic Year 2025-2026
2nd Semester
Department of Information Technology
"""
    block_b = """
Student Evaluation of Teaching
Overall Rating: 85.00 / 100
"""
    records = parse_set_sef_metadata_multi(block_a + "\n\n" + block_b)
    assert len(records) == 1
    r = records[0]
    assert r.evaluation_type == "SET"
    assert r.academic_year == "2025-2026"
    assert r.semester == "2nd Semester"
    assert r.overall_rating == "85.00 / 100"
    assert r.extraction_status == EXTRACTION_COMPLETE


def test_filename_style_content_not_used_for_kind():
    text = """
Student Evaluation of Teaching
Academic Year 2025-2026
2nd Semester
Overall Rating: 90 / 100
"""
    records = parse_set_sef_metadata_multi(text)
    assert len(records) == 1
    assert records[0].evaluation_type == "SET"


def test_mixed_set_sef_composition_label():
    text = """
Student Evaluation of Teaching
Academic Year 2024-2025
1st Semester
Overall Rating: 88 / 100

Supervisor Evaluation of Faculty
Academic Year 2024-2025
1st Semester
Overall Rating: 86 / 100
"""
    records = parse_set_sef_metadata_multi(text)
    assert classify_document_composition(records) == "Mixed SET and SEF"
    assert len(records) == 2


def test_dedupe_merges_orphan_rating_into_period_draft():
    period_draft = {
        "key": sync_key(
            evaluation_type="SET",
            academic_year="2025-2026",
            semester="2nd Semester",
            source_section_ref="section:1",
        ),
        "evaluation_type": "SET",
        "academic_year": "2025-2026",
        "semester": "2nd Semester",
        "rating_raw": None,
    }
    rating_draft = {
        "key": sync_key(
            evaluation_type="SET",
            academic_year=None,
            semester=None,
            source_section_ref="section:2",
            fallback_index=1,
        ),
        "evaluation_type": "SET",
        "rating_raw": "85.00 / 100",
        "rating_percent": 85.0,
    }
    merged = dedupe_parsed_drafts([period_draft, rating_draft])
    assert len(merged) == 1
    assert merged[0]["rating_raw"] == "85.00 / 100"
