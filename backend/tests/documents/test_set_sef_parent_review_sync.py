"""SET/SEF parent PDF completion after child validation (synthetic, no live DB)."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from documents.set_sef_parent_review_sync import (
    assess_parent_document_review_completion,
    try_sync_parent_document_review,
)


class _Rel:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return self._rows


def _doc(**kwargs):
    defaults = {
        "id": 1,
        "public_id": "doc_parent",
        "faculty_profile_id": 10,
        "indicator_id": "kra1-a-student",
        "criterion_id": "kra1-a",
        "status": "pending_review",
        "ocr_status": "completed",
        "file_path": "/tmp/x.pdf",
        "file_hash": "hash_a",
        "extracted_info": {
            "SET/SEF extraction status": "complete",
            "Faculty name extraction status": "matched",
            "Faculty name": "Jane Faculty",
        },
        "faculty_profile": SimpleNamespace(
            user=SimpleNamespace(full_name="Jane Faculty"),
        ),
        "teaching_evaluations": _Rel([]),
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def _tev(**kwargs):
    defaults = {
        "id": 100,
        "public_id": "tev_1",
        "document_id": 1,
        "evaluation_type": "SET",
        "academic_year": "2025-2026",
        "semester": "1st Semester",
        "indicator_id": "kra1-a-student",
        "reviewer_validation_status": "approved",
        "extracted_metadata": {"extractionStatus": "complete"},
        "correction_history_json": [{"reviewerId": "rev_1"}],
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


@patch("documents.set_sef_parent_review_sync.resolve_path", return_value="/tmp/x.pdf")
@patch("documents.set_sef_parent_review_sync.verify_document_ownership")
@patch("documents.set_sef_parent_review_sync._duplicate_file_hash", return_value=None)
@patch("documents.set_sef_parent_review_sync._duplicate_tev_period_across_faculty", return_value=None)
def test_twelve_children_validated_marks_ready(mock_dup, mock_file, mock_own, mock_path):
    mock_own.return_value = {"scoringEligible": True, "message": "ok"}
    tevs = [_tev(public_id=f"tev_{i}", id=100 + i) for i in range(12)]
    doc = _doc(teaching_evaluations=_Rel(tevs))
    result = assess_parent_document_review_completion(doc)
    assert result.ready is True
    assert result.blockers == []


@patch("documents.set_sef_parent_review_sync.resolve_path", return_value="/tmp/x.pdf")
@patch("documents.set_sef_parent_review_sync.verify_document_ownership")
@patch("documents.set_sef_parent_review_sync._duplicate_file_hash", return_value=None)
@patch("documents.set_sef_parent_review_sync._duplicate_tev_period_across_faculty", return_value=None)
def test_partial_children_not_ready(mock_dup, mock_tev, mock_own, mock_path):
    mock_own.return_value = {"scoringEligible": True}
    doc = _doc(
        teaching_evaluations=_Rel(
            [
                _tev(reviewer_validation_status="approved"),
                _tev(public_id="tev_2", id=101, reviewer_validation_status=None),
            ]
        )
    )
    result = assess_parent_document_review_completion(doc)
    assert result.ready is False
    assert any("still require review" in b for b in result.blockers)


@patch("documents.set_sef_parent_review_sync.resolve_path", return_value="/tmp/x.pdf")
@patch("documents.set_sef_parent_review_sync.verify_document_ownership")
@patch("documents.set_sef_parent_review_sync._duplicate_file_hash", return_value=None)
@patch("documents.set_sef_parent_review_sync._duplicate_tev_period_across_faculty", return_value=None)
def test_name_mismatch_blocks(mock_dup, mock_tev, mock_own, mock_path):
    mock_own.return_value = {
        "scoringEligible": False,
        "message": "Faculty name mismatch.",
    }
    doc = _doc(teaching_evaluations=_Rel([_tev()]))
    result = assess_parent_document_review_completion(doc)
    assert result.ready is False
    assert any("mismatch" in b.lower() for b in result.blockers)


@patch("documents.set_sef_parent_review_sync.db")
@patch("documents.set_sef_parent_review_sync.resolve_path", return_value="/tmp/x.pdf")
@patch("documents.set_sef_parent_review_sync.verify_document_ownership")
@patch("documents.set_sef_parent_review_sync._duplicate_file_hash", return_value=None)
@patch("documents.set_sef_parent_review_sync._duplicate_tev_period_across_faculty", return_value=None)
def test_sync_approves_parent(mock_dup, mock_file, mock_own, mock_path, mock_db):
    mock_own.return_value = {"scoringEligible": True}
    reviewer = SimpleNamespace(id=5, public_id="rev_1", full_name="Reviewer One")
    doc = _doc(teaching_evaluations=_Rel([_tev()]))
    with patch("documents.set_sef_parent_review_sync.User") as user_q:
        user_q.query.filter_by.return_value.first.return_value = reviewer
        changed = try_sync_parent_document_review(doc, reviewer, trigger="test")
    assert changed is True
    assert doc.status == "approved"
    mock_db.session.commit.assert_called()
