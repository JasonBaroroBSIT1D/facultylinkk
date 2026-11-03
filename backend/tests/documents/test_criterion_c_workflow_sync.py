"""Criterion C accomplishment decisions sync linked Document.status."""

from __future__ import annotations

from documents.criterion_c_evidence.bundle import build_initial_bundle
from documents.criterion_c_evidence.workflow_sync import linked_document_public_ids


def test_linked_document_public_ids_includes_checklist_and_supporting():
    bundle = build_initial_bundle(
        primary_document_id="doc_primary",
        primary_file_hash="h1",
        indicator_id="kra1-c-adviser-sp",
        project_title="AI-Assisted Campus Help Desk",
    )
    bundle["checklist"]["approval_sheet"]["documentId"] = "doc_primary"
    bundle["checklist"]["rrpa_copc"]["documentId"] = "doc_rrpa"
    bundle["supportingDocumentIds"] = ["doc_primary", "doc_rrpa"]
    ids = linked_document_public_ids(bundle, "doc_primary")
    assert ids == {"doc_primary", "doc_rrpa"}
