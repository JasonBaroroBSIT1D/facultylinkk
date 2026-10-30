"""Teaching evaluation sync plan tests (pure logic, no database)."""

from __future__ import annotations

from documents.ocr.set_sef_metadata import (
    EXTRACTION_COMPLETE,
    SetSefEvaluationRecord,
    parse_set_sef_metadata_multi,
)
from documents.teaching_evaluation_sync import (
    ExistingEvalSnapshot,
    build_sync_plan,
    dedupe_parsed_drafts,
    is_reviewer_protected,
    sync_key,
)


def _record(**kwargs) -> SetSefEvaluationRecord:
    base = SetSefEvaluationRecord(
        evaluation_type="SET",
        academic_year="2024-2025",
        semester="1st Semester",
        overall_rating="90 / 100",
        rating_scale="100",
        extraction_status=EXTRACTION_COMPLETE,
        source_section_ref="section:1:line1",
    )
    for key, value in kwargs.items():
        setattr(base, key, value)
    return base


def test_sync_key_period_vs_section():
    assert sync_key(
        evaluation_type="SET",
        academic_year="2024-2025",
        semester="1st Semester",
        source_section_ref="section:1",
    ) == ("period", "SET", "2024-2025", "1st Semester")


def test_reviewer_protected_when_correction_history():
    snap = ExistingEvalSnapshot(
        id=1,
        evaluation_type="SET",
        academic_year="2024-2025",
        semester="1st Semester",
        source_section_ref=None,
        extraction_source="ocr",
        correction_history=[{"field": "rating"}],
    )
    assert is_reviewer_protected(snap)


def test_build_plan_creates_twelve_from_consolidated_text():
    chunks = []
    for year, sem in [
        ("2020-2021", "1st Semester"),
        ("2020-2021", "2nd Semester"),
        ("2021-2022", "1st Semester"),
        ("2021-2022", "2nd Semester"),
        ("2022-2023", "1st Semester"),
        ("2022-2023", "2nd Semester"),
    ]:
        chunks.append(
            f"Student Evaluation of Teaching\nAcademic Year {year}\n{sem}\nOverall Rating: 90 / 100\n"
        )
        chunks.append(
            f"Supervisor Evaluation of Teaching\nAcademic Year {year}\n{sem}\n"
            f"Overall Evaluation Score: 85 / 100\n"
        )
    parsed = parse_set_sef_metadata_multi("\n".join(chunks))
    plan = build_sync_plan(parsed, [], upload_indicator_id="kra1-a-student")
    assert len(plan.creates) == 12
    assert plan.skipped_ambiguous_type == 0
    set_rows = [c for c in plan.creates if c["evaluation_type"] == "SET"]
    sef_rows = [c for c in plan.creates if c["evaluation_type"] == "SEF"]
    assert len(set_rows) == 6
    assert len(sef_rows) == 6


def test_idempotent_plan_no_duplicate_creates():
    parsed = parse_set_sef_metadata_multi(
        "Student Evaluation of Teaching\nAcademic Year 2024-2025\n1st Semester\nOverall Rating: 88 / 100\n"
    )
    existing = [
        ExistingEvalSnapshot(
            id=10,
            evaluation_type="SET",
            academic_year="2024-2025",
            semester="1st Semester",
            source_section_ref="section:1",
            extraction_source="ocr",
        )
    ]
    plan = build_sync_plan(parsed, existing, upload_indicator_id="kra1-a-student")
    assert plan.creates == []
    assert len(plan.updates) == 1
    assert plan.updates[0]["id"] == 10


def test_protected_row_not_updated():
    parsed = [_record(overall_rating="95 / 100")]
    existing = [
        ExistingEvalSnapshot(
            id=3,
            evaluation_type="SET",
            academic_year="2024-2025",
            semester="1st Semester",
            source_section_ref="section:1:line1",
            extraction_source="ocr",
            reviewer_validation_status="approved",
        )
    ]
    plan = build_sync_plan(parsed, existing, upload_indicator_id="kra1-a-student")
    assert plan.updates == []
    assert plan.skipped_protected == 1


def test_orphan_ocr_row_scheduled_for_removal():
    parsed = [_record(academic_year="2025-2026", semester="2nd Semester")]
    existing = [
        ExistingEvalSnapshot(
            id=7,
            evaluation_type="SET",
            academic_year="2024-2025",
            semester="1st Semester",
            source_section_ref="section:1:line1",
            extraction_source="ocr",
        )
    ]
    plan = build_sync_plan(parsed, existing, upload_indicator_id="kra1-a-student")
    assert 7 in plan.delete_ids


def test_ambiguous_type_skipped_not_created():
    parsed = [_record(evaluation_type=None, extraction_status="ambiguous")]
    plan = build_sync_plan(parsed, [], upload_indicator_id="kra1-a-student")
    assert plan.creates == []
    assert plan.skipped_ambiguous_type == 1


def test_dedupe_parsed_drafts():
    drafts = [
        {"key": ("period", "SET", "2024-2025", "1st Semester"), "evaluation_type": "SET"},
        {"key": ("period", "SET", "2024-2025", "1st Semester"), "evaluation_type": "SET"},
    ]
    assert len(dedupe_parsed_drafts(drafts)) == 1
