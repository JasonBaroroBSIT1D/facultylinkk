"""KRA II checklist reconciliation from supporting evidence links."""

from __future__ import annotations

from types import SimpleNamespace

from documents.kra2_evidence.bundle import BUNDLE_EXTRACTED_KEY, build_initial_bundle, persist_link
from documents.kra2_evidence.checklist_reconcile import reconcile_kra2_checklist_from_links


def test_reconcile_fills_indexing_slot_from_supporting_link(app):
    primary_id = "doc_primary_test"
    supporting_id = "doc_index_cert"
    bundle = build_initial_bundle(
        primary_document_id=primary_id,
        primary_file_hash="hash_primary",
        indicator_id="kra2-a-journal-sole",
    )
    primary = SimpleNamespace(
        public_id=primary_id,
        faculty_profile_id=1,
        indicator_id="kra2-a-journal-sole",
        extracted_info={BUNDLE_EXTRACTED_KEY: bundle},
        file_hash="hash_primary",
    )
    supporting = SimpleNamespace(
        public_id=supporting_id,
        faculty_profile_id=1,
        file_hash="hash_support",
        extracted_info={},
    )
    persist_link(
        supporting,
        {
            "role": "supporting",
            "primaryDocumentId": primary_id,
            "evidenceSlot": "indexing_certification",
        },
    )

    import documents.kra2_evidence.checklist_reconcile as mod

    class _Query:
        def filter_by(self, **kwargs):
            return self

        def filter(self, *args, **kwargs):
            return self

        def __iter__(self):
            yield supporting

    with app.app_context():
        original = mod.Document.query
        mod.Document.query = _Query()
        try:
            changed = reconcile_kra2_checklist_from_links(primary, bundle)
        finally:
            mod.Document.query = original

    assert changed is True
    entry = bundle["checklist"]["indexing_certification"]
    assert entry["documentId"] == supporting_id
    assert entry["status"] == "present_unverified"
