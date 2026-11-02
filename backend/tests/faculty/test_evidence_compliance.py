"""Evidence compliance snapshot (no live DB)."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

from faculty.evidence_compliance import evidence_compliance_snapshot


def _profile():
    return SimpleNamespace(id=1, public_id="fac-1")


def test_semester_validated_parent_pdf_pending():
    te = {
        "criterionAWorkspace": {
            "totals": {
                "childValidation": {
                    "total": 12,
                    "validated": 12,
                    "pending": 0,
                    "incomplete": 0,
                    "needsRevision": 0,
                    "rejected": 0,
                }
            }
        },
        "set": {"missingPeriods": []},
        "sef": {"missingPeriods": []},
        "criterionADisplay": {"estimatedPoints": 57.2, "displayLabel": "Estimated"},
    }
    doc = SimpleNamespace(
        criterion_id="kra1-a",
        kra_id="kra1",
        status="pending_review",
        deleted_at=None,
        indicator_id="kra1-a-teaching-evidence",
        extracted_info={},
        ocr_status="completed",
        teaching_evaluations=[],
    )

    with patch("faculty.evidence_compliance.Document") as doc_model:
        doc_model.query.filter_by.return_value.filter.return_value.all.return_value = [doc]
        with patch("faculty.evidence_compliance.set_sef_parent_context") as ctx_fn:
            ctx_fn.return_value = {
                "allChildValidationSummary": {"total": 12, "validated": 12, "pending": 0},
            }
            snap = evidence_compliance_snapshot(_profile(), te)

    assert snap["semesterEvaluations"]["validated"] == 12
    assert snap["documentsPendingReview"] == 1
    assert snap["status"] == "Needs attention"
    assert "Semester Evaluations Validated" in snap["statusLabel"]
    assert snap["criterionAEstimatedPoints"] == 57.2


def test_all_semesters_validated_does_not_imply_requirements_complete_if_periods_missing():
    te = {
        "criterionAWorkspace": {
            "totals": {
                "childValidation": {
                    "total": 12,
                    "validated": 12,
                    "pending": 0,
                    "incomplete": 0,
                    "needsRevision": 0,
                    "rejected": 0,
                }
            }
        },
        "set": {"missingPeriods": ["2022-2023 1st Semester SET"]},
        "sef": {"missingPeriods": []},
    }
    with patch("faculty.evidence_compliance.Document") as doc_model:
        doc_model.query.filter_by.return_value.filter.return_value.all.return_value = []
        snap = evidence_compliance_snapshot(_profile(), te)
    assert snap["requirementsComplete"] is False
    assert snap["semesterEvaluations"]["validated"] == 12


def test_requirements_complete_when_no_missing_periods():
    te = {
        "criterionAWorkspace": {
            "totals": {
                "childValidation": {
                    "total": 6,
                    "validated": 6,
                    "pending": 0,
                    "incomplete": 0,
                    "needsRevision": 0,
                    "rejected": 0,
                }
            }
        },
        "set": {"missingPeriods": []},
        "sef": {"missingPeriods": []},
    }
    with patch("faculty.evidence_compliance.Document") as doc_model:
        doc_model.query.filter_by.return_value.filter.return_value.all.return_value = []
        snap = evidence_compliance_snapshot(_profile(), te)
    assert snap["requirementsComplete"] is True
    assert snap["statusLabel"] == "Requirements Complete"
