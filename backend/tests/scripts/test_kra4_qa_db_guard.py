"""QA database guard must block production facultylink."""

from __future__ import annotations

import os

import pytest


def test_qa_guard_rejects_production_database(monkeypatch):
    monkeypatch.delenv("FACULTYLINK_QA_DATABASE_URL", raising=False)
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://u:p@127.0.0.1:5432/facultylink")
    monkeypatch.delenv("FACULTYLINK_QA_DATABASE_ALLOWED", raising=False)
    from scripts import qa_db_guard

    with pytest.raises(SystemExit) as exc:
        qa_db_guard.require_qa_test_database()
    assert exc.value.code == 3


def test_qa_guard_accepts_facultylink_qa(monkeypatch):
    monkeypatch.setenv(
        "FACULTYLINK_QA_DATABASE_URL",
        "postgresql+psycopg://u:p@127.0.0.1:5432/facultylink_qa",
    )
    monkeypatch.setenv("FACULTYLINK_QA_DATABASE_ALLOWED", "1")
    from scripts import qa_db_guard

    name = qa_db_guard.require_qa_test_database()
    assert name == "facultylink_qa"
