"""Criterion C research approval-sheet OCR extraction and merge behavior."""

from __future__ import annotations

from types import SimpleNamespace

from documents.criterion_c_evidence.bundle import build_initial_bundle
from documents.criterion_c_evidence.metadata_merge import (
    preserve_criterion_c_extracted_info,
    snapshot_criterion_c_extracted_fields,
)
from documents.criterion_c_evidence.ocr_research import (
    OCR_EXTRACTION_KEY,
    OCR_EXTRACTION_VERSION,
    apply_criterion_c_research_ocr,
    ensure_research_ocr_extraction,
    link_primary_document_as_approval_sheet,
    parse_research_approval_ocr,
)
from documents.criterion_c_evidence.validation import validate_criterion_c_bundle


def test_parse_research_approval_ocr_extracts_core_fields():
    text = """
    UNIVERSITY APPROVAL SHEET
    Title of Thesis: Smart Campus IoT Monitoring System
    Researchers: Juan Dela Cruz, Maria Santos
    A.Y. 2024-2025
    Date of Approval: 2024-06-15
    """
    parsed = parse_research_approval_ocr(text)
    fields = parsed["fields"]
    assert fields["projectTitle"]["value"] == "Smart Campus IoT Monitoring System"
    assert "Juan Dela Cruz" in fields["studentNames"]["value"]
    assert fields["academicYear"]["value"] == "2024-2025"
    assert fields["completionDate"]["value"] == "2024-06-15"
    assert parsed["advisoryOnly"] is True


def test_parse_does_not_fabricate_group_or_missing_fields():
    parsed = parse_research_approval_ocr("Approval sheet with no structured labels.")
    fields = parsed["fields"]
    assert fields["studentGroupLabel"]["status"] == "missing"
    assert fields["studentNames"]["value"] == ""


def test_apply_ocr_merges_into_research_bundle():
    doc = SimpleNamespace(
        public_id="doc_primary",
        file_hash="hash1",
        criterion_id="kra1-c",
        extracted_info={},
    )
    bundle = build_initial_bundle(
        primary_document_id="doc_primary",
        primary_file_hash="hash1",
        indicator_id="kra1-c-adviser-ut",
        project_title="",
    )
    bundle = link_primary_document_as_approval_sheet(doc, bundle)
    doc.extracted_info = {"criterionCEvidenceBundle": bundle}

    apply_criterion_c_research_ocr(
        doc,
        text="Project Title: Automated Grading Assistant\nStudent Names: Ana Reyes\nDate of Approval: 2025-01-10",
    )
    merged = doc.extracted_info["criterionCEvidenceBundle"]
    assert merged["projectTitle"] == "Automated Grading Assistant"
    assert merged["studentNames"] == "Ana Reyes"
    assert merged["completionDate"] == "2025-01-10"
    assert OCR_EXTRACTION_KEY in doc.extracted_info


def test_confirmed_metadata_survives_reocr_merge():
    before_bundle = build_initial_bundle(
        primary_document_id="doc_primary",
        primary_file_hash="hash1",
        indicator_id="kra1-c-adviser-ut",
        project_title="Faculty Corrected Title",
    )
    before_bundle["studentNames"] = "Correct Student"
    before_bundle["metadataConfirmed"] = {
        "projectTitle": True,
        "studentNames": True,
    }
    before = {
        "criterionCEvidenceBundle": before_bundle,
        OCR_EXTRACTION_KEY: {"fields": {}},
    }
    after = {
        "criterionCEvidenceBundle": {
            **before_bundle,
            "projectTitle": "OCR Wrong Title",
            "studentNames": "OCR Wrong Student",
        },
        OCR_EXTRACTION_KEY: {
            "fields": {
                "projectTitle": {"value": "OCR Wrong Title"},
                "studentNames": {"value": "OCR Wrong Student"},
            }
        },
    }
    merged = preserve_criterion_c_extracted_info(before=before, after=after)
    bundle = merged["criterionCEvidenceBundle"]
    assert bundle["projectTitle"] == "Faculty Corrected Title"
    assert bundle["studentNames"] == "Correct Student"


def test_incomplete_ocr_leaves_validation_blockers():
    bundle = build_initial_bundle(
        primary_document_id="doc_primary",
        primary_file_hash="hash1",
        indicator_id="kra1-c-adviser-ut",
        project_title="",
    )
    bundle = link_primary_document_as_approval_sheet(
        SimpleNamespace(public_id="doc_primary", file_hash="hash1"),
        bundle,
    )
    validation = validate_criterion_c_bundle(bundle)
    assert validation["validationStatus"] == "incomplete"
    assert "project_title_missing" in validation["flags"]


def test_rejects_filename_and_heading_as_title():
    parsed = parse_research_approval_ocr(
        "01 Signed Approval Sheet SAMPLE\nA.Y. 2025-2026\n"
        "Title of Thesis: Adaptive Learning Platform for Engineering Students\n"
        "Prepared by: Lee, Kim and Santos, Ana\n"
        "Approval Date: March 15, 2025"
    )
    fields = parsed["fields"]
    assert fields["projectTitle"]["value"] == "Adaptive Learning Platform for Engineering Students"
    assert "Lee" in fields["studentNames"]["value"]
    assert fields["academicYear"]["value"] == "2025-2026"
    assert fields["completionDate"]["value"] == "2025-03-15"
    assert fields["studentGroupLabel"]["value"] == ""


def test_apply_ocr_replaces_unreliable_filename_title_in_bundle():
    doc = SimpleNamespace(
        public_id="doc_primary",
        file_hash="hash1",
        criterion_id="kra1-c",
        extracted_info={},
    )
    bundle = build_initial_bundle(
        primary_document_id="doc_primary",
        primary_file_hash="hash1",
        indicator_id="kra1-c-adviser-ut",
        project_title="01 Signed Approval Sheet SAMPLE",
    )
    bundle = link_primary_document_as_approval_sheet(doc, bundle)
    doc.extracted_info = {"criterionCEvidenceBundle": bundle}
    apply_criterion_c_research_ocr(
        doc,
        text="Research Title: Blockchain-Based Transcript Verification\nStudent(s): Cruz, Juan\nDate Approved: 2025-04-01",
    )
    merged = doc.extracted_info["criterionCEvidenceBundle"]
    assert merged["projectTitle"] == "Blockchain-Based Transcript Verification"
    assert merged["studentNames"] == "Cruz, Juan"


def test_facultylink_fictional_approval_sheet_student_label_on_next_line():
    """Stored OCR for doc AI-Assisted Campus Help Desk uses label-only Student(s) line."""
    text = """
    FACULTYLINK • FICTIONAL UNIVERSITY TEST RECORD
    Research Approval Sheet — TEST SAMPLE
    Faculty
    Jason Baroro
    Research category
    Special Project / Capstone Project
    Faculty role
    Adviser
    Research title
    AI-Assisted Campus Help Desk
    Student(s)
    Alex Rivera; Sam Cruz
    Academic year
    2025–2026
    Defense date
    March 18, 2026
    """
    parsed = parse_research_approval_ocr(text)
    students = parsed["structured"]["students"]
    assert any("Alex" in s and "Rivera" in s for s in students)
    assert any("Sam" in s and "Cruz" in s for s in students)
    assert not any("Baroro" in s for s in students)
    assert parsed["fields"]["projectTitle"]["value"] == "AI-Assisted Campus Help Desk"
    assert parsed["fields"]["studentNames"]["value"]
    assert "Rivera" in parsed["fields"]["studentNames"]["value"]


def test_ai_assisted_campus_help_desk_excludes_adviser_and_panel():
    text = """
    APPROVAL SHEET
    Title of Thesis: AI-Assisted Campus Help Desk
    Names of Students: Santos, Maria / Cruz, Juan
    Group No.: Team Alpha
    Thesis Adviser: Jason Baroro, Ph.D.
    Panel Members: Lee, Kim; Reyes, Ana
    Date of Approval: 2025-03-10
    """
    parsed = parse_research_approval_ocr(text)
    assert parsed["version"] == OCR_EXTRACTION_VERSION
    structured = parsed["structured"]
    students = structured["students"]
    assert any("Maria" in s or "Santos" in s for s in students)
    assert any("Cruz" in s or "Juan" in s for s in students)
    assert not any("Baroro" in s for s in students)
    assert not any("Lee" in s for s in students)
    assert parsed["fields"]["studentGroupLabel"]["value"] == "Team Alpha"
    assert parsed["fields"]["projectTitle"]["value"] == "AI-Assisted Campus Help Desk"


def test_ensure_research_ocr_reparse_from_stored_text():
    doc = SimpleNamespace(
        public_id="doc_primary",
        file_hash="hash1",
        criterion_id="kra1-c",
        extracted_text=(
            "Title of Thesis: AI-Assisted Campus Help Desk\n"
            "Student Names: Cruz, Juan\n"
            "Date of Approval: 2025-03-10"
        ),
        ocr_status="completed",
        extracted_info={
            "criterionCEvidenceBundle": build_initial_bundle(
                primary_document_id="doc_primary",
                primary_file_hash="hash1",
                indicator_id="kra1-c-adviser-sp",
                project_title="",
            )
        },
    )
    extraction = ensure_research_ocr_extraction(doc)
    assert extraction is not None
    assert "Cruz" in extraction["fields"]["studentNames"]["value"]
    bundle = doc.extracted_info["criterionCEvidenceBundle"]
    assert "Cruz" in bundle["studentNames"]


def test_snapshot_roundtrip_for_ocr_hook():
    info = {
        "criterionCEvidenceBundle": {"projectTitle": "X"},
        OCR_EXTRACTION_KEY: {"version": "1.0"},
    }
    snap = snapshot_criterion_c_extracted_fields(info)
    assert snap["criterionCEvidenceBundle"]["projectTitle"] == "X"
    assert snap[OCR_EXTRACTION_KEY]["version"] == "1.0"
