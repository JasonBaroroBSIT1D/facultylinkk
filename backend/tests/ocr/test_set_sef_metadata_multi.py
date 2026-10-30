"""Multi-record SET/SEF parser tests (synthetic text only, no database)."""

from __future__ import annotations

from documents.ocr.set_sef_metadata import (
    EXTRACTION_AMBIGUOUS,
    EXTRACTION_COMPLETE,
    EXTRACTION_PARTIAL,
    parse_set_sef_metadata,
    parse_set_sef_metadata_multi,
    verify_record_indicator,
    verify_selected_indicator,
)
from tests.ocr.test_set_sef_metadata import SET_SAMPLE as _SET
from tests.ocr.test_set_sef_metadata import SEF_SAMPLE as _SEF


def _periods(text: str):
    return parse_set_sef_metadata_multi(text)


def test_single_set_unchanged_legacy_parser():
    parsed = parse_set_sef_metadata(_SET)
    assert parsed.detected_kind == "SET"
    assert parsed.academic_year == "2024-2025"
    assert parsed.semester == "1st Semester"
    assert verify_selected_indicator("kra1-a-student", parsed) == "MATCH"


def test_single_semester_multi_returns_one_record():
    records = _periods(_SET)
    assert len(records) == 1
    r = records[0]
    assert r.evaluation_type == "SET"
    assert r.academic_year == "2024-2025"
    assert r.semester == "1st Semester"
    assert r.overall_rating == "88.5 / 100"
    assert r.extraction_status == EXTRACTION_COMPLETE


def test_six_set_semesters_in_one_document():
    blocks = []
    pairs = [
        ("2020-2021", "1st Semester", "90"),
        ("2020-2021", "2nd Semester", "91"),
        ("2021-2022", "1st Semester", "92"),
        ("2021-2022", "2nd Semester", "93"),
        ("2022-2023", "1st Semester", "94"),
        ("2022-2023", "2nd Semester", "95"),
    ]
    for year, sem, score in pairs:
        blocks.append(
            f"""
Student Evaluation of Teaching
Faculty Name: Maria Santos
Academic Year {year}
{sem}
Overall Rating: {score}.0 / 100
"""
        )
    text = "\n\n".join(blocks)
    records = _periods(text)
    assert len(records) == 6
    assert all(r.evaluation_type == "SET" for r in records)
    years = [(r.academic_year, r.semester) for r in records]
    assert ("2020-2021", "1st Semester") in years
    assert ("2022-2023", "2nd Semester") in years
    assert all(r.extraction_status == EXTRACTION_COMPLETE for r in records)


def test_six_sef_semesters():
    blocks = []
    for i, (year, sem) in enumerate(
        [
            ("2020-2021", "1st Semester"),
            ("2020-2021", "2nd Semester"),
            ("2021-2022", "1st Semester"),
            ("2021-2022", "2nd Semester"),
            ("2022-2023", "1st Semester"),
            ("2022-2023", "2nd Semester"),
        ]
    ):
        blocks.append(
            f"""
Supervisor Evaluation of Teaching
Faculty: Jason Baroro
Academic Year {year}
{sem}
Overall Evaluation Score: {88 + i}.0 / 100
"""
        )
    records = _periods("\n\n".join(blocks))
    assert len(records) == 6
    assert all(r.evaluation_type == "SEF" for r in records)


def test_twelve_set_and_sef_mixed_order():
    chunks = []
    set_pairs = [("2020-2021", "1st Semester"), ("2020-2021", "2nd Semester")]
    sef_pairs = [("2021-2022", "1st Semester"), ("2021-2022", "2nd Semester")]
    for year, sem in set_pairs:
        chunks.append(
            f"Student Evaluation of Teaching\nAY {year}\n{sem}\nOverall Rating: 90 / 100\n"
        )
    for year, sem in sef_pairs:
        chunks.append(
            f"Supervisor Evaluation of Faculty\nAcademic Year {year}\n{sem}\n"
            f"Overall Rating: 85 / 100\n"
        )
    # interleave more to reach 12 total
    extra_set = [
        ("2022-2023", "1st Semester"),
        ("2022-2023", "2nd Semester"),
        ("2023-2024", "1st Semester"),
        ("2023-2024", "2nd Semester"),
    ]
    extra_sef = [
        ("2024-2025", "1st Semester"),
        ("2024-2025", "2nd Semester"),
        ("2025-2026", "1st Semester"),
        ("2025-2026", "2nd Semester"),
    ]
    for year, sem in extra_set:
        chunks.append(
            f"Student Evaluation of Teaching\nAcademic Year {year}\n{sem}\nOverall Rating: 91 / 100\n"
        )
    for year, sem in extra_sef:
        chunks.append(
            f"Supervisor Evaluation of Teaching\nAcademic Year {year}\n{sem}\n"
            f"Overall Evaluation Score: 86 / 100\n"
        )
    records = _periods("\n".join(chunks))
    assert len(records) == 12
    set_count = sum(1 for r in records if r.evaluation_type == "SET")
    sef_count = sum(1 for r in records if r.evaluation_type == "SEF")
    assert set_count == 6
    assert sef_count == 6


def test_fewer_than_six_sections():
    text = """
Student Evaluation of Teaching
Faculty Name: Ana Cruz
Academic Year 2023-2024
2nd Semester
Overall Rating: 77 / 100
"""
    records = _periods(text)
    assert len(records) == 1
    assert records[0].academic_year == "2023-2024"


def test_incomplete_record_flags_partial():
    text = """
Student Evaluation of Teaching
Faculty Name: Ana Cruz
Academic Year 2023-2024
First Semester
"""
    records = _periods(text)
    assert len(records) == 1
    assert records[0].extraction_status == EXTRACTION_PARTIAL
    assert "overall rating" in records[0].missing_fields


def test_ambiguous_dual_kind_single_section():
    """Both SET and SEF phrases in one block without separate section headers."""
    text = """
Combined Teaching Evaluation Report
Covers Student Evaluation of Teaching and Supervisor Evaluation of Faculty on one sheet.
Faculty Name: Ana Cruz
Academic Year 2024-2025
1st Semester
Overall Rating: 80 / 100
"""
    records = _periods(text)
    assert len(records) == 1
    assert records[0].evaluation_type is None
    assert records[0].extraction_status in (EXTRACTION_AMBIGUOUS, EXTRACTION_PARTIAL)
    assert "evaluation type" in records[0].ambiguous_fields or "evaluation type" in records[0].missing_fields


def test_verify_record_indicator_per_row():
    records = _periods(_SEF)
    assert len(records) == 1
    assert verify_record_indicator("kra1-a-supervisor", records[0]) == "MATCH"
    assert verify_record_indicator("kra1-a-student", records[0]) == "POSSIBLE_MISMATCH"


def test_page_marker_in_section_ref():
    text = """
[Page 2]
Student Evaluation of Teaching
Academic Year 2024-2025
1st Semester
Overall Rating: 88 / 100
"""
    records = _periods(text)
    assert len(records) == 1
    assert records[0].source_section_ref
    assert "page:2" in records[0].source_section_ref or "section:1" in records[0].source_section_ref
