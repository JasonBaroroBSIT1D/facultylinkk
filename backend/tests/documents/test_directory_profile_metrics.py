"""Per-faculty evidence metrics (synthetic documents, no DB writes)."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

from documents.directory import profile_evidence_metrics


def _doc(status="pending_review", criterion_id="kra1-a"):
    return SimpleNamespace(
        status=status,
        criterion_id=criterion_id,
        deleted_at=None,
        faculty_profile_id=1,
    )


def test_twelve_validated_semesters_one_pending_pdf():
    doc = _doc(status="pending_review")
    tev_stats = {
        "evaluationRecordsTotal": 12,
        "evaluationRecordsPending": 0,
        "evaluationRecordsValidated": 12,
        "evaluationRecordsNeedsRevision": 0,
        "evaluationRecordsRejected": 0,
        "evaluationRecordsIncomplete": 0,
    }
    with patch("documents.directory.workspace_teaching_evaluation_stats", return_value=tev_stats):
        m = profile_evidence_metrics([doc])
    assert m["sourcePdfTotal"] == 1
    assert m["sourcePdfPendingWorkflow"] == 1
    assert m["evaluationRecordsValidated"] == 12
    assert m["evaluationRecordsPending"] == 0
    assert m["semesterEvaluationsPending"] == 0


def test_legacy_non_set_sef_pending_documents():
    docs = [_doc(status="pending_review", criterion_id="kra2-b"), _doc(status="approved", criterion_id="kra2-b")]
    tev_stats = {
        "evaluationRecordsTotal": 0,
        "evaluationRecordsPending": 0,
        "evaluationRecordsValidated": 0,
        "evaluationRecordsNeedsRevision": 0,
        "evaluationRecordsRejected": 0,
        "evaluationRecordsIncomplete": 0,
    }
    with patch("documents.directory.workspace_teaching_evaluation_stats", return_value=tev_stats):
        m = profile_evidence_metrics(docs)
    assert m["sourcePdfTotal"] == 2
    assert m["sourcePdfPendingWorkflow"] == 1
