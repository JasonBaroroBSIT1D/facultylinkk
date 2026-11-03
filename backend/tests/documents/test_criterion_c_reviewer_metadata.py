"""Reviewer-entered research metadata clears validation blockers."""

from __future__ import annotations

from types import SimpleNamespace

from documents.criterion_c_evidence.bundle import build_initial_bundle
from documents.criterion_c_evidence.service import reviewer_update_criterion_c
from documents.criterion_c_evidence.validation import validate_criterion_c_bundle


def _research_bundle_missing_students() -> dict:
    bundle = build_initial_bundle(
        primary_document_id="doc_primary",
        primary_file_hash="hash1",
        indicator_id="kra1-c-adviser-ut",
        project_title="Sample Thesis Title",
    )
    bundle["studentNames"] = ""
    bundle["completionDate"] = "2025-05-01"
    bundle["checklist"]["approval_sheet"] = {
        "documentId": "doc_primary",
        "status": "verified",
        "fileHash": "hash1",
    }
    bundle["checklist"]["rrpa_copc"] = {
        "documentId": "sup_rrpa",
        "status": "verified",
        "fileHash": "h2",
    }
    return bundle


def test_reviewer_student_names_clears_blocker(monkeypatch):
    bundle = _research_bundle_missing_students()
    doc = SimpleNamespace(
        public_id="doc_primary",
        faculty_profile_id=1,
        indicator_id="kra1-c-adviser-ut",
        extracted_info={"criterionCEvidenceBundle": bundle},
    )
    reviewer = SimpleNamespace(id=9, full_name="Reviewer One")

    pre = validate_criterion_c_bundle(bundle)
    assert "student_names_missing" in pre.get("flags", [])
    assert any("Student name" in b for b in pre.get("blockers", []))

    monkeypatch.setattr(
        "documents.criterion_c_evidence.service._peer_bundles",
        lambda *_a, **_k: [],
    )
    monkeypatch.setattr(
        "documents.criterion_c_evidence.service.get_document",
        lambda _pid: doc,
    )
    monkeypatch.setattr(
        "documents.service.reviewer_can_access",
        lambda _u, _d: True,
    )
    monkeypatch.setattr(
        "documents.criterion_c_evidence.service.persist_bundle",
        lambda _doc, b: doc.extracted_info.__setitem__("criterionCEvidenceBundle", b),
    )
    monkeypatch.setattr("documents.criterion_c_evidence.service.db.session.commit", lambda: None)
    monkeypatch.setattr("documents.criterion_c_evidence.service.db.session.add", lambda _x: None)

    _doc, validation = reviewer_update_criterion_c(
        reviewer,
        "doc_primary",
        slot_id=None,
        status=None,
        metadata={"studentNames": "Juan Dela Cruz, Ana Reyes"},
    )
    assert validation.get("readyForReviewer") is True
    assert "student_names_missing" not in validation.get("flags", [])
    stored = doc.extracted_info["criterionCEvidenceBundle"]
    assert stored["studentNames"] == "Juan Dela Cruz, Ana Reyes"
