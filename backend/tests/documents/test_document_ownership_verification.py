"""Document ownership verification (synthetic, no database)."""

from __future__ import annotations

from types import SimpleNamespace

from documents.document_ownership_verification import (
    STATUS_MATCHED,
    STATUS_MISMATCH,
    STATUS_NOT_DETECTED,
    document_scoring_eligible,
    names_match_flexible,
    verify_document_ownership,
)
from documents.scoring.set_sef_aggregate import aggregate_indicator


def _doc(info: dict):
    return SimpleNamespace(
        public_id="doc_test",
        extracted_info=info,
        faculty_profile=SimpleNamespace(
            public_id="fac_x",
            user=SimpleNamespace(full_name="Jason Baroro"),
        ),
    )


def test_name_match_flexible_lastname_firstname():
    assert names_match_flexible("Neri, Lutche", "Lutche Neri")
    assert names_match_flexible("Jason Baroro", "JASON BARORO")


def test_name_mismatch():
    doc = _doc(
        {
            "Faculty name on document": "Neri, Lutche",
            "Faculty name extraction status": "detected",
        }
    )
    result = verify_document_ownership(doc)
    assert result["status"] == STATUS_MISMATCH
    assert result["scoringEligible"] is False


def test_name_matched():
    doc = _doc(
        {
            "Faculty name on document": "Jason Baroro",
            "Faculty name extraction status": "detected",
        }
    )
    result = verify_document_ownership(doc)
    assert result["status"] == STATUS_MATCHED
    assert result["scoringEligible"] is True


def test_name_not_detected():
    doc = _doc({"Faculty name extraction status": "not_detected"})
    result = verify_document_ownership(doc)
    assert result["status"] == STATUS_NOT_DETECTED
    assert result["scoringEligible"] is False


def test_legacy_document_without_ownership_fields_remains_scoring_eligible():
    doc = SimpleNamespace(
        extracted_info={"Academic year": "2024-2025", "Extracted rating": "90"},
    )
    assert document_scoring_eligible(doc) is True
    result = verify_document_ownership(doc)
    assert result["status"] == STATUS_NOT_DETECTED


def test_mismatch_excluded_from_scoring(monkeypatch):
    monkeypatch.setattr(
        "documents.scoring.set_sef_aggregate.indicator_scoring_config",
        lambda _ind: {
            "complete": True,
            "maxPoints": 36.0,
            "multiplier": 36.0,
            "ratingScale": 100.0,
            "aggregationMethod": "circular_jc_2026_semester_average",
            "roundingRule": "two_decimals",
            "evaluationCoverage": {"standardRequiredSemesters": 1},
        },
    )
    monkeypatch.setattr("documents.scoring.set_sef_aggregate.published_settings_root", lambda: {})
    doc = SimpleNamespace(
        public_id="d1",
        file_name="m.pdf",
        indicator_id="kra1-a-student",
        status="approved",
        ocr_status="completed",
        submitted_at=None,
        extracted_info={
            "Faculty name on document": "Other Person",
            "Faculty name extraction status": "detected",
        },
        faculty_profile=SimpleNamespace(user=SimpleNamespace(full_name="Jason Baroro")),
        teaching_evaluations=[
            SimpleNamespace(
                public_id="t1",
                indicator_id="kra1-a-student",
                evaluation_type="SET",
                academic_year="2024-2025",
                semester="1st Semester",
                rating_raw="90/100",
                rating_scale=100.0,
                rating_percent=90.0,
                reviewer_validation_status="approved",
                ocr_verification_status="match",
                extracted_metadata={},
                source_section_ref="p1",
            )
        ],
    )
    block = aggregate_indicator([doc], "kra1-a-student")
    assert block["provisionalPoints"] is None or block["coverageSummary"]["evidencedRatings"] == 0
