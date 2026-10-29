"""SET/SEF simulation auto-accept (unit tests, no facultylink DB writes)."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from documents.review_display import review_display_status
from documents.scoring.set_sef_aggregate import _review_bucket
from documents.set_sef_auto_approval.assess import assess_document
from documents.set_sef_auto_approval.policy import (
    is_auto_approval_active,
    set_admin_policy_enabled,
)


@pytest.fixture(autouse=True)
def _assess_isolation(monkeypatch):
    chain = MagicMock()
    chain.filter_by.return_value.filter.return_value.first.return_value = None
    chain.filter.return_value.filter.return_value.all.return_value = []
    chain.filter.return_value.all.return_value = []
    monkeypatch.setattr("documents.service._active_docs_query", lambda: chain)
    monkeypatch.setattr(
        "documents.set_sef_auto_approval.assess.resolve_path",
        lambda path: SimpleNamespace(is_file=lambda: True) if path else None,
    )
    monkeypatch.setattr(
        "documents.set_sef_auto_approval.assess._find_period_conflicts",
        lambda doc, info: None,
    )


def _doc(**overrides):
    user = SimpleNamespace(full_name=overrides.pop("profile_name", "Jason Baroro"))
    profile = SimpleNamespace(public_id="fac_test", user=user)
    base = dict(
        id=1,
        public_id="doc_test",
        faculty_profile_id=1,
        faculty_profile=profile,
        indicator_id="kra1-a-supervisor",
        status="pending_review",
        ocr_status="completed",
        ocr_confidence=88.0,
        file_path="uploads/x.pdf",
        file_hash="abc123",
        extracted_info={},
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def _complete_sef_info(**extra):
    info = {
        "Indicator verification status": "MATCH",
        "Detected evaluation kind": "SEF",
        "Faculty name": "Jason Baroro",
        "Evaluation type": "Supervisor Evaluation of Teaching",
        "Academic year": "2024-2025",
        "Semester": "1st Semester",
        "Extracted rating": "95 / 100",
        "Rating scale": "100",
        "SET/SEF extraction status": "complete",
    }
    info.update(extra)
    return info


def test_eligible_document_passes_all_checks():
    doc = _doc(extracted_info=_complete_sef_info())
    result = assess_document(doc)
    assert result.eligible is True
    assert not result.withheld_reasons
    assert result.checks["metadata_validation"].ok
    assert result.checks["evaluation_period_eligibility"].ok
    assert result.checks["ocr_extraction_quality"].ok


def test_match_but_faculty_mismatch():
    doc = _doc(
        profile_name="Maria Santos",
        extracted_info=_complete_sef_info(**{"Faculty name": "Jason Baroro"}),
    )
    result = assess_document(doc)
    assert result.eligible is False
    assert any("faculty" in r.lower() for r in result.withheld_reasons)
    assert not result.checks["metadata_validation"].ok


def test_match_but_invalid_rating():
    doc = _doc(extracted_info=_complete_sef_info(**{"Extracted rating": "not-a-rating"}))
    result = assess_document(doc)
    assert result.eligible is False
    assert any("rating" in r.lower() for r in result.withheld_reasons)


def test_period_conflict_blocks(monkeypatch):
    monkeypatch.setattr(
        "documents.set_sef_auto_approval.assess._find_period_conflicts",
        lambda doc, info: "Another document already covers 2024-2025 · 1st Semester.",
    )
    doc = _doc(extracted_info=_complete_sef_info())
    result = assess_document(doc)
    assert result.eligible is False
    assert not result.checks["evaluation_period_eligibility"].ok


def test_low_ocr_confidence_still_eligible_when_fields_valid():
    doc = _doc(ocr_confidence=40.0, extracted_info=_complete_sef_info())
    result = assess_document(doc)
    assert result.eligible is True
    assert result.checks["ocr_extraction_quality"].ok
    assert "low" in result.checks["ocr_extraction_quality"].message.lower()


def test_null_ocr_confidence_eligible_with_complete_extraction():
    doc = _doc(ocr_confidence=None, extracted_info=_complete_sef_info())
    result = assess_document(doc)
    assert result.eligible is True
    assert result.checks["ocr_extraction_quality"].ok


def test_ambiguous_extraction_fields_block():
    doc = _doc(
        extracted_info=_complete_sef_info(**{"Ambiguous extraction fields": "Semester"}),
    )
    result = assess_document(doc)
    assert result.eligible is False
    assert not result.checks["ocr_extraction_quality"].ok
    assert any("manual review" in r.lower() for r in result.withheld_reasons)


def test_ambiguous_rating_blocks():
    doc = _doc(
        extracted_info=_complete_sef_info(
            **{"Ambiguous extraction fields": "Extracted rating", "Extracted rating": "95 / 100"}
        ),
    )
    result = assess_document(doc)
    assert result.eligible is False
    assert not result.checks["metadata_validation"].ok


def test_incomplete_extraction_blocks():
    doc = _doc(extracted_info=_complete_sef_info(**{"SET/SEF extraction status": "partial"}))
    result = assess_document(doc)
    assert result.eligible is False
    assert not result.checks["ocr_extraction_quality"].ok


def test_ocr_warnings_block():
    doc = _doc(extracted_info=_complete_sef_info(**{"OCR warnings": "Unreadable header"}))
    result = assess_document(doc)
    assert result.eligible is False


def test_missing_academic_year():
    info = _complete_sef_info()
    del info["Academic year"]
    doc = _doc(extracted_info=info)
    result = assess_document(doc)
    assert result.eligible is False
    assert any("incomplete" in r.lower() or "metadata" in r.lower() for r in result.withheld_reasons)


def test_ocr_failure_status():
    doc = _doc(ocr_status="failed", extracted_info=_complete_sef_info())
    result = assess_document(doc)
    assert result.eligible is False


def test_previously_rejected():
    doc = _doc(status="rejected", extracted_info=_complete_sef_info())
    result = assess_document(doc)
    assert result.eligible is False


def test_manual_reviewer_history_blocks():
    info = _complete_sef_info(
        reviewHistory=[
            {
                "action": "reject",
                "actorId": "usr_reviewer",
                "actorName": "Reviewer",
            }
        ]
    )
    doc = _doc(extracted_info=info)
    result = assess_document(doc)
    assert result.eligible is False
    assert any("manual review" in r.lower() for r in result.withheld_reasons)


def test_non_set_sef_unaffected():
    doc = _doc(indicator_id="kra2-a-research", extracted_info={})
    result = assess_document(doc)
    assert result.eligible is False
    assert "SET/SEF" in result.withheld_reasons[0]


@patch("documents.set_sef_auto_approval.policy._policy_path")
def test_policy_disabled_by_default(mock_path, tmp_path):
    path = tmp_path / "policy.json"
    path.write_text('{"enabled": false}', encoding="utf-8")
    mock_path.return_value = path
    with patch("documents.set_sef_auto_approval.policy.env_forces_enabled", return_value=False):
        assert is_auto_approval_active() is False


@patch("documents.set_sef_auto_approval.policy._policy_path")
def test_unauthorized_enable_without_allow_toggle(mock_path, tmp_path):
    path = tmp_path / "policy.json"
    path.write_text("{}", encoding="utf-8")
    mock_path.return_value = path
    with patch("documents.set_sef_auto_approval.policy.env_forces_enabled", return_value=False):
        with patch("documents.set_sef_auto_approval.policy.admin_may_toggle_policy", return_value=False):
            with pytest.raises(ValueError, match="policy_toggle_not_allowed"):
                set_admin_policy_enabled(enabled=True, admin_public_id="usr_admin")


@patch("documents.set_sef_auto_approval.apply.is_auto_approval_active", return_value=True)
@patch("documents.set_sef_auto_approval.apply.record_auto_approval_audit")
@patch("documents.set_sef_auto_approval.apply.db")
def test_apply_creates_audit_and_approval(mock_db, mock_audit, _active):
    from documents.set_sef_auto_approval.apply import maybe_auto_approve_after_ocr

    doc = _doc(extracted_info=_complete_sef_info())
    locked = doc
    mock_db.session.get.return_value = locked
    job = SimpleNamespace(id=99)
    with patch("documents.set_sef_auto_approval.apply.assess_document") as mock_assess:
        mock_assess.return_value = SimpleNamespace(
            eligible=True,
            to_dict=lambda: {"eligible": True, "checks": {}},
            withheld_reasons=[],
            policy_version="1.1.0",
        )
        maybe_auto_approve_after_ocr(doc, job)
    assert doc.status == "approved"
    mock_audit.assert_called_once()
    assert "simulation" in (doc.reviewer_remarks or "").lower()


@patch("documents.set_sef_auto_approval.apply.is_auto_approval_active", return_value=False)
@patch("documents.set_sef_auto_approval.apply.db")
def test_apply_skips_when_policy_off(mock_db, _active):
    from documents.set_sef_auto_approval.apply import maybe_auto_approve_after_ocr

    doc = _doc(extracted_info=_complete_sef_info())
    mock_db.session.get.return_value = doc
    job = SimpleNamespace(id=1)
    with patch("documents.set_sef_auto_approval.apply.assess_document") as mock_assess:
        mock_assess.return_value = SimpleNamespace(
            eligible=True,
            to_dict=lambda: {"eligible": True},
            withheld_reasons=[],
        )
        maybe_auto_approve_after_ocr(doc, job)
    assert doc.status == "pending_review"


@patch("documents.set_sef_auto_approval.apply.is_auto_approval_active", return_value=True)
@patch("documents.set_sef_auto_approval.apply.db")
def test_withheld_reassessed_when_policy_active(mock_db, _active):
    from documents.set_sef_auto_approval.apply import maybe_auto_approve_after_ocr

    info = _complete_sef_info()
    info["autoValidation"] = {"ocrJobId": 5, "decisionSource": "withheld", "eligible": True}
    doc = _doc(extracted_info=info)
    mock_db.session.get.return_value = doc
    job = SimpleNamespace(id=5)
    maybe_auto_approve_after_ocr(doc, job)
    assert doc.status == "approved"


@patch("documents.set_sef_auto_approval.apply.is_auto_approval_active", return_value=False)
@patch("documents.set_sef_auto_approval.apply.db")
def test_withheld_skips_reassess_when_policy_off(mock_db, _active):
    from documents.set_sef_auto_approval.apply import maybe_auto_approve_after_ocr

    info = _complete_sef_info()
    info["autoValidation"] = {"ocrJobId": 5, "decisionSource": "withheld"}
    doc = _doc(extracted_info=info)
    mock_db.session.get.return_value = doc
    job = SimpleNamespace(id=5)
    maybe_auto_approve_after_ocr(doc, job)
    assert doc.status == "pending_review"


def test_review_display_auto_vs_reviewer():
    auto_doc = _doc(
        status="approved",
        extracted_info=_complete_sef_info(
            **{
                "Approval decision source": "system_auto_approval",
                "autoValidation": {"decisionSource": "system_auto_approval"},
            }
        ),
    )
    assert review_display_status(auto_doc) == "simulation-auto-accepted"
    manual_doc = _doc(
        status="approved",
        extracted_info=_complete_sef_info(**{"Approval decision source": "reviewer_manual"}),
    )
    assert review_display_status(manual_doc) == "simulation-reviewer-validated"


def test_validated_scoring_accepts_auto_approved_status():
    assert _review_bucket("approved") == "accepted"
