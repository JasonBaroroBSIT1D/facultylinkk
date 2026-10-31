"""Generalized combined SET/SEF semester table parsing (synthetic fixtures only)."""

from __future__ import annotations

from pathlib import Path

import pytest

from documents.ocr import set_sef_metadata as parser_module
from documents.ocr.set_sef_metadata import (
    EXTRACTION_AMBIGUOUS,
    EXTRACTION_COMPLETE,
    classify_document_composition,
    parse_set_sef_metadata_multi,
)


def _table_header_block() -> str:
    return """
Semester / School Year
Students Rating
Students x 60%
Supervisor Rating
Supervisor x 40%
Semester Average
"""


def _table_row(sem_sy: str, set_raw: float, sef_raw: float) -> str:
    set_w = round(set_raw * 0.6, 2)
    sef_w = round(sef_raw * 0.4, 2)
    avg = round(set_raw * 0.6 + sef_raw * 0.4, 2)
    return f"{sem_sy}\n{set_raw:.2f}\n{set_w:.2f}\n{sef_raw:.2f}\n{sef_w:.2f}\n{avg:.2f}\n"


def build_combined_table_text(
    *,
    faculty: str,
    rows: list[tuple[str, float, float]],
    title: str = "Summary of Individual Faculty Rating",
) -> str:
    """Build synthetic OCR text for a combined SET/SEF table (any faculty, any row count)."""
    body = "".join(_table_row(sem_sy, s, f) for sem_sy, s, f in rows)
    return f"""
{title}
Faculty: {faculty}
Department: __________________
{_table_header_block()}
{body}
OVERALL AVERAGE
88.00
Semester average = (Students rating x 0.60) + (Supervisor rating x 0.40).
"""


def _record_tuples(records):
    return sorted(
        (r.evaluation_type, r.academic_year, r.semester, r.overall_rating)
        for r in records
    )


def test_summary_title_with_faculty_rating_phrase_does_not_steal_name():
    text = build_combined_table_text(
        faculty="Diego Ramos",
        rows=[("1st Sem., SY 2021-2022", 91.0, 92.0)],
        title="Summary of Individual Faculty Rating",
    )
    records = parse_set_sef_metadata_multi(text)
    assert records
    assert all(r.faculty_name == "Diego Ramos" for r in records)


def test_parser_module_contains_no_faculty_specific_hardcoding():
    source = Path(parser_module.__file__).read_text(encoding="utf-8")
    for forbidden in ("Jason Baroro", "Jason_Baroro", "Baroro_6", "faculty_profile_id"):
        assert forbidden not in source


def test_two_semesters_arbitrary_faculty():
    text = build_combined_table_text(
        faculty="Maria Elena Santos",
        rows=[
            ("1st Sem., SY 2020-2021", 88.0, 86.0),
            ("2nd Sem., SY 2020-2021", 90.0, 89.0),
        ],
    )
    records = parse_set_sef_metadata_multi(text)
    assert len(records) == 4
    assert classify_document_composition(records) == "Mixed SET and SEF"
    assert all(r.faculty_name == "Maria Elena Santos" for r in records)
    assert _record_tuples(records) == sorted(
        [
            ("SET", "2020-2021", "1st Semester", "88.00 / 100"),
            ("SEF", "2020-2021", "1st Semester", "86.00 / 100"),
            ("SET", "2020-2021", "2nd Semester", "90.00 / 100"),
            ("SEF", "2020-2021", "2nd Semester", "89.00 / 100"),
        ]
    )


def test_six_semesters_fixture_via_builder_not_hardcoded_parser():
    text = build_combined_table_text(
        faculty="Faculty Member A",
        rows=[
            ("1st Sem., SY 2023-2024", 92.0, 94.0),
            ("2nd Sem., SY 2023-2024", 96.0, 97.0),
            ("1st Sem., SY 2024-2025", 93.0, 94.0),
            ("2nd Sem., SY 2024-2025", 97.0, 98.0),
            ("1st Sem., SY 2025-2026", 94.0, 93.0),
            ("2nd Sem., SY 2025-2026", 98.0, 99.0),
        ],
    )
    records = parse_set_sef_metadata_multi(text)
    assert len(records) == 12
    assert sum(1 for r in records if r.evaluation_type == "SET") == 6
    assert sum(1 for r in records if r.evaluation_type == "SEF") == 6
    assert "95.33" not in {r.overall_rating for r in records}


def test_three_semesters_different_academic_years():
    text = build_combined_table_text(
        faculty="Renato Cruz Jr.",
        rows=[
            ("1st Sem., SY 2019-2020", 81.0, 80.0),
            ("2nd Sem., SY 2019-2020", 82.0, 83.0),
            ("1st Sem., SY 2020-2021", 84.0, 85.0),
        ],
    )
    records = parse_set_sef_metadata_multi(text)
    assert len(records) == 6
    years = {r.academic_year for r in records}
    assert years == {"2019-2020", "2020-2021"}


def test_reordered_numeric_columns_still_finds_raw_ratings():
    """SEF raw appears before SET raw in the row tail (column order swap)."""
    text = build_combined_table_text(
        faculty="Patricia Lim",
        rows=[("1st Sem., SY 2022-2023", 91.0, 87.0)],
    )
    # Replace first row numbers with swapped column order: SEF, sef_w, SET, set_w, avg
    set_raw, sef_raw = 91.0, 87.0
    swapped = (
        f"1st Sem., SY 2022-2023\n"
        f"{sef_raw:.2f}\n{sef_raw * 0.4:.2f}\n{set_raw:.2f}\n{set_raw * 0.6:.2f}\n"
        f"{set_raw * 0.6 + sef_raw * 0.4:.2f}\n"
    )
    text = text.replace(_table_row("1st Sem., SY 2022-2023", 91.0, 87.0), swapped)
    records = parse_set_sef_metadata_multi(text)
    assert len(records) == 2
    by_type = {r.evaluation_type: r for r in records}
    assert by_type["SET"].overall_rating == "91.00 / 100"
    assert by_type["SEF"].overall_rating == "87.00 / 100"


def test_ay_first_row_format():
    text = f"""
Faculty Name: Diego Ramos
Students Rating
Supervisor Rating
Semester Average
AY 2021-2022, 2nd Sem
90.00
54.00
88.00
35.20
89.20
"""
    records = parse_set_sef_metadata_multi(text)
    assert len(records) == 2
    assert records[0].academic_year == "2021-2022"
    assert records[0].semester == "2nd Semester"


def test_parsed_faculty_names_do_not_cross_between_documents():
    text_a = build_combined_table_text(
        faculty="Alice One",
        rows=[("1st Sem., SY 2023-2024", 90.0, 91.0)],
    )
    text_b = build_combined_table_text(
        faculty="Bob Two",
        rows=[("1st Sem., SY 2023-2024", 85.0, 86.0)],
    )
    rec_a = parse_set_sef_metadata_multi(text_a)
    rec_b = parse_set_sef_metadata_multi(text_b)
    assert all(r.faculty_name == "Alice One" for r in rec_a)
    assert all(r.faculty_name == "Bob Two" for r in rec_b)


def test_set_only_single_section_not_treated_as_combined_table():
    text = """
Student Evaluation of Teaching
Faculty Name: Ana Reyes
Academic Year 2024-2025
First Semester
Overall Rating: 90.0 / 100
"""
    records = parse_set_sef_metadata_multi(text)
    assert len(records) == 1
    assert records[0].evaluation_type == "SET"
    assert classify_document_composition(records) == "SET only"


def test_separate_sections_mixed_still_work():
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
    assert len(records) == 2
    assert classify_document_composition(records) == "Mixed SET and SEF"


def test_uncertain_document_no_invented_rows():
    records = parse_set_sef_metadata_multi("Faculty handbook appendix — no evaluation tables.")
    assert records == [] or classify_document_composition(records) in (
        "Uncertain evaluation content",
        "No evaluation sections detected",
    )


def test_ambiguous_row_without_weight_fingerprint_not_guessed():
    text = """
Faculty: Casey Ng
Students Rating
Supervisor Rating
Semester Average
1st Sem., SY 2023-2024
90.00
88.00
91.00
2nd Sem., SY 2023-2024
90.00
88.00
91.00
"""
    records = parse_set_sef_metadata_multi(text)
    assert records == [] or not any(r.overall_rating for r in records)


_UPLOAD_PDF = (
    Path(__file__).resolve().parents[2]
    / "uploads"
    / "faculty"
    / "1"
    / "f0ced164b6124c89b0a7865307bd0c4e.pdf"
)


@pytest.mark.skipif(not _UPLOAD_PDF.is_file(), reason="Optional local six-semester PDF fixture")
def test_optional_local_pdf_fixture_row_count():
    pymupdf = pytest.importorskip("pymupdf")
    doc = pymupdf.open(_UPLOAD_PDF)
    try:
        text = doc[0].get_text("text")
    finally:
        doc.close()
    records = parse_set_sef_metadata_multi(text)
    assert len(records) == 12
    assert sum(1 for r in records if r.evaluation_type == "SET") == 6
    assert sum(1 for r in records if r.evaluation_type == "SEF") == 6
