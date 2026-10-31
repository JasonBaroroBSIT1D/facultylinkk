"""Parent PDF vs child SET/SEF validation status (synthetic, no DB)."""

from __future__ import annotations

from types import SimpleNamespace

from documents.set_sef_parent_context import (
    set_sef_parent_context,
    summary_line,
    workspace_teaching_evaluation_stats,
)
def _doc(**kwargs):
    defaults = {
        "public_id": "doc_test",
        "title": "SET upload",
        "file_name": "06_SET_AY2025-2026_Sem2.pdf",
        "faculty_profile_id": 1,
        "kra_id": "kra1",
        "criterion_id": "kra1-a",
        "indicator_id": "kra1-a-student",
        "status": "approved",
        "ocr_status": "completed",
        "extracted_info": {
            "Document evaluation composition": "SET only",
            "Detected evaluation section count": "2",
            "Approval decision source": "system_auto_approval",
        },
        "extracted_text": "Student Evaluation of Teaching",
        "file_path": "/tmp/x.pdf",
        "verified_points": 0,
        "estimated_points": 0,
        "teaching_evaluations": [],
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def _tev(**kwargs):
    defaults = {
        "public_id": "tev_1",
        "indicator_id": "kra1-a-student",
        "evaluation_type": "SET",
        "academic_year": "2025-2026",
        "semester": "2nd Semester",
        "rating_raw": "85/100",
        "reviewer_validation_status": None,
        "extracted_metadata": {"extractionStatus": "complete"},
        "source_section_ref": "section:1",
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


class _Rel:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return self._rows


def test_parent_pending_when_children_unreviewed():
    doc = _doc(teaching_evaluations=_Rel([_tev(), _tev(public_id="tev_2")]))
    ctx = set_sef_parent_context(doc)
    assert ctx is not None
    assert ctx["listDisplayStatus"] == "pending-review"
    assert ctx["childValidationSummary"]["pending"] == 2
    assert "simulation" in (ctx["estimatedPointsExplanation"] or "").lower()


def test_summary_line_includes_counts():
    line = summary_line("SET only", {"total": 6, "validated": 2, "pending": 4})
    assert "SET only" in line
    assert "6 evaluation" in line
    assert "2 validated" in line
    assert "4 pending" in line


def test_workspace_stats_count_evaluations_not_pdfs():
    doc = _doc(teaching_evaluations=_Rel([_tev(), _tev(public_id="tev_2")]))
    stats = workspace_teaching_evaluation_stats([doc])
    assert stats["evaluationRecordsTotal"] == 2
    assert stats["evaluationRecordsPending"] == 2
    assert stats["evaluationRecordsValidated"] == 0


def test_list_display_status_differs_from_parent_workflow():
    doc = _doc(teaching_evaluations=_Rel([_tev()]))
    ctx = set_sef_parent_context(doc)
    assert doc.status == "approved"
    assert ctx["listDisplayStatus"] == "pending-review"
    assert ctx["parentWorkflowApproved"] is True
