"""KRA IV QA tag exclusion is database-aware."""

from __future__ import annotations

from types import SimpleNamespace

from documents.kra4_evidence.scoring import is_qa_sandbox_accomplishment


def test_qa_title_excluded_on_production(monkeypatch):
    doc = SimpleNamespace(title="[KRA4-QA] sample")
    monkeypatch.setattr("scripts.qa_db_guard.qa_tag_excluded_from_scoring_totals", lambda: True)
    assert is_qa_sandbox_accomplishment(doc) is True


def test_qa_title_counted_on_facultylink_qa(monkeypatch):
    doc = SimpleNamespace(title="[KRA4-QA] sample")
    monkeypatch.setattr("scripts.qa_db_guard.qa_tag_excluded_from_scoring_totals", lambda: False)
    assert is_qa_sandbox_accomplishment(doc) is False
