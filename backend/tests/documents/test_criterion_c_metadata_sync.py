"""Criterion C bundle metadata persistence and reviewer-facing payloads."""

from __future__ import annotations

from types import SimpleNamespace

from documents.criterion_c_evidence.bundle import build_initial_bundle, persist_bundle
from documents.criterion_c_evidence.research_metadata import is_unreliable_research_title
def test_unreliable_title_detector():
    assert is_unreliable_research_title("01 Signed Approval Sheet SAMPLE") is True
    assert is_unreliable_research_title("Real Thesis About Water Quality") is False


def test_persist_bundle_keeps_confirmed_metadata_on_document():
    doc = SimpleNamespace(public_id="doc_c1", extracted_info={})
    bundle = build_initial_bundle(
        primary_document_id="doc_c1",
        primary_file_hash="h1",
        indicator_id="kra1-c-adviser-ut",
        project_title="Faculty Confirmed Thesis Title",
    )
    bundle["studentNames"] = "Student A, Student B"
    bundle["metadataConfirmed"] = {"projectTitle": True, "studentNames": True}
    persist_bundle(doc, bundle)
    stored = doc.extracted_info["criterionCEvidenceBundle"]
    assert stored["projectTitle"] == "Faculty Confirmed Thesis Title"
    assert stored["studentNames"] == "Student A, Student B"
