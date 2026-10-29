"""Document review status mapping (no database)."""

from __future__ import annotations

from types import SimpleNamespace

from documents.status_map import (
    document_status_to_web,
    is_awaiting_review,
    is_legacy_uploaded_draft,
)


def _doc(**kwargs):
    defaults = dict(status="draft", file_path=None, deleted_at=None)
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def test_legacy_uploaded_draft_maps_to_pending_review():
    doc = _doc(status="draft", file_path="uploads/x.pdf")
    assert is_legacy_uploaded_draft(doc)
    assert document_status_to_web(doc) == "pending-review"
    assert is_awaiting_review(doc)


def test_empty_draft_stays_draft():
    doc = _doc(status="draft", file_path=None)
    assert not is_legacy_uploaded_draft(doc)
    assert document_status_to_web(doc) == "draft"
    assert not is_awaiting_review(doc)


def test_new_upload_status_pending_review():
    doc = _doc(status="pending_review", file_path="uploads/y.pdf")
    assert document_status_to_web(doc) == "pending-review"
    assert is_awaiting_review(doc)
