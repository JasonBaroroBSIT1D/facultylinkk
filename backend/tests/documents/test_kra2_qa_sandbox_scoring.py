"""QA-tagged accomplishments must not affect rank simulation totals."""

from __future__ import annotations

from types import SimpleNamespace

from documents.kra2_evidence.scoring import is_qa_sandbox_accomplishment, score_accomplishment_document


def test_qa_title_detected():
    doc = SimpleNamespace(title="[KRA2-B-QA] patent test", public_id="doc_x")
    assert is_qa_sandbox_accomplishment(doc)


def test_qa_sandbox_excluded_from_scoring():
    bundle = {
        "accomplishmentId": "a1",
        "reviewStatus": "approved",
        "reviewerAssessment": {"assessedPoints": 80},
    }
    doc = SimpleNamespace(
        title="[KRA2-B-QA] grant",
        public_id="doc_qa",
        criterion_id="kra2-b",
        indicator_id="kra2-b-patent-g-sole",
        extracted_info={"kra2EvidenceBundle": bundle},
    )
    row = score_accomplishment_document(doc, settings={"indicators": {}}, applicable_config_present=True)
    assert row is not None
    assert row.included is False
    assert "qa_sandbox_excluded" in row.reasons
