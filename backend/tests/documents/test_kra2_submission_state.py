"""KRA II draft vs submitted accomplishment visibility."""

from __future__ import annotations

from types import SimpleNamespace

from documents.kra2_evidence.bundle import build_initial_bundle, persist_bundle
from documents.kra2_evidence.submission_state import (
    accomplishment_submitted,
    is_kra2_unsubmitted_draft,
)
from documents.service import queue_for_reviewer
from documents.status_map import is_legacy_uploaded_draft


def test_accomplishment_submitted_requires_bundle_timestamp():
    bundle = build_initial_bundle(
        primary_document_id="d1",
        primary_file_hash="h",
        indicator_id="kra2-a-journal-sole",
    )
    assert not accomplishment_submitted(bundle)
    bundle["submittedForReviewAt"] = "2025-08-15T00:00:00+00:00"
    assert accomplishment_submitted(bundle)


def test_kra2_unsubmitted_draft_not_legacy_queue_candidate():
    bundle = build_initial_bundle(
        primary_document_id="d1",
        primary_file_hash="h",
        indicator_id="kra2-a-journal-sole",
    )
    doc = SimpleNamespace(
        deleted_at=None,
        status="draft",
        file_path="files/x.pdf",
        criterion_id="kra2-a",
        indicator_id="kra2-a-journal-sole",
        extracted_info={},
        public_id="d1",
        faculty_profile_id=1,
    )
    persist_bundle(doc, bundle)
    assert is_kra2_unsubmitted_draft(doc)
    assert not is_legacy_uploaded_draft(doc)


def test_kra2_submitted_not_unsubmitted_draft():
    bundle = build_initial_bundle(
        primary_document_id="d2",
        primary_file_hash="h2",
        indicator_id="kra2-a-journal-sole",
    )
    bundle["submittedForReviewAt"] = "2025-08-15T00:00:00+00:00"
    doc = SimpleNamespace(
        deleted_at=None,
        status="pending_review",
        file_path="files/y.pdf",
        criterion_id="kra2-a",
        indicator_id="kra2-a-journal-sole",
        extracted_info={},
        public_id="d2",
        faculty_profile_id=1,
    )
    persist_bundle(doc, bundle)
    assert not is_kra2_unsubmitted_draft(doc)


def test_queue_for_reviewer_skips_unsubmitted_kra2(monkeypatch):
    draft = SimpleNamespace(
        deleted_at=None,
        status="pending_review",
        file_path="files/z.pdf",
        criterion_id="kra2-a",
        indicator_id="kra2-a-journal-sole",
        extracted_info={},
        public_id="draft-doc",
        faculty_profile_id=1,
    )
    bundle = build_initial_bundle(
        primary_document_id="draft-doc",
        primary_file_hash="hz",
        indicator_id="kra2-a-journal-sole",
    )
    persist_bundle(draft, bundle)

    submitted = SimpleNamespace(
        deleted_at=None,
        status="pending_review",
        file_path="files/s.pdf",
        criterion_id="kra2-a",
        indicator_id="kra2-a-journal-sole",
        extracted_info={},
        public_id="sub-doc",
        faculty_profile_id=1,
    )
    bundle2 = build_initial_bundle(
        primary_document_id="sub-doc",
        primary_file_hash="hs",
        indicator_id="kra2-a-journal-sole",
    )
    bundle2["submittedForReviewAt"] = "2025-08-16T00:00:00+00:00"
    persist_bundle(submitted, bundle2)

    reviewer = SimpleNamespace(id=99)

    monkeypatch.setattr(
        "documents.service.list_reviewer_documents",
        lambda _r: [draft, submitted],
    )
    monkeypatch.setattr("documents.service.db.session.commit", lambda: None)

    queue = queue_for_reviewer(reviewer)
    ids = {d.public_id for d in queue}
    assert "draft-doc" not in ids
    assert "sub-doc" in ids
