"""KRA II scoring integrity — patent stages, KRA aggregation, legacy overlap."""

from __future__ import annotations

from types import SimpleNamespace

from documents.kra2_evidence.bundle import REVIEW_APPROVED, SLOT_STATUS_VERIFIED, build_initial_bundle
from documents.kra2_evidence.patent_deduplication import apply_patent_highest_stage_only
from documents.kra2_evidence.reviewer_assessment import apply_reviewer_accomplishment_decision
from documents.kra2_evidence.scoring import aggregate_kra2_criterion_from_documents, aggregate_kra2_kra_from_documents
from faculty.kra_document_aggregate import aggregate_criterion_documents_from_list


def _settings() -> dict:
    ind = {
        "kra2-b-patent-a-sole": {"points": 10, "maxPoints": 10},
        "kra2-b-patent-p-sole": {"points": 20, "maxPoints": 20},
        "kra2-b-patent-g-sole": {"points": 80, "maxPoints": 80},
        "kra2-a-journal-sole": {"points": 50, "maxPoints": 50},
        "kra2-a-cite": {"points": 10, "maxPoints": 60, "group": "kra2-a-cite", "groupMax": 60},
        "kra2-b-comm-local": {"points": 5, "maxPoints": 20, "group": "kra2-b-comm-local", "groupMax": 20},
    }
    return {
        "kras": {"kra2": {"maxPoints": 100}},
        "criteria": {"kra2-a": {"maxPoints": 100}, "kra2-b": {"maxPoints": 100}, "kra2-c": {"maxPoints": 100}},
        "indicators": ind,
    }


def _approved_journal_doc(*, public_id: str) -> SimpleNamespace:
    bundle = build_initial_bundle(
        primary_document_id=public_id,
        primary_file_hash=f"hash-{public_id}",
        indicator_id="kra2-a-journal-sole",
    )
    bundle["outputTitle"] = "Sample Article"
    bundle["outputVenue"] = "Journal of Examples"
    bundle["journalTitle"] = "Journal of Examples"
    bundle["authorsLine"] = "Faculty A"
    bundle["publicationDate"] = "2025-06-01"
    bundle["metadataConfirmed"] = {
        "outputTitle": True,
        "outputVenue": True,
        "journalTitle": True,
        "authorsLine": True,
        "publicationDate": True,
    }
    bundle["submittedForReviewAt"] = "2025-06-01T00:00:00+00:00"
    bundle["checklist"]["primary_output"]["status"] = SLOT_STATUS_VERIFIED
    apply_reviewer_accomplishment_decision(
        bundle,
        review_status=REVIEW_APPROVED,
        reviewer_user_id=1,
        reviewer_display_name="Reviewer",
        remarks="Verified journal article for scoring integrity test.",
        indicator_id="kra2-a-journal-sole",
        settings=_settings(),
    )
    return SimpleNamespace(
        public_id=public_id,
        criterion_id="kra2-a",
        indicator_id="kra2-a-journal-sole",
        extracted_info={"kra2EvidenceBundle": bundle},
        deleted_at=None,
        status="approved",
    )


def _approved_patent_doc(*, public_id: str, indicator_id: str, reg: str) -> SimpleNamespace:
    bundle = build_initial_bundle(
        primary_document_id=public_id,
        primary_file_hash=f"hash-{public_id}",
        indicator_id=indicator_id,
    )
    bundle["outputTitle"] = "Solar desalination device"
    bundle["registrationNumber"] = reg
    bundle["registrationDate"] = "2025-01-01"
    bundle["authorsLine"] = "Faculty A"
    bundle["metadataConfirmed"] = {
        "outputTitle": True,
        "registrationNumber": True,
        "registrationDate": True,
        "authorsLine": True,
    }
    bundle["submittedForReviewAt"] = "2025-06-01T00:00:00+00:00"
    bundle["checklist"]["primary_output"]["status"] = SLOT_STATUS_VERIFIED
    apply_reviewer_accomplishment_decision(
        bundle,
        review_status=REVIEW_APPROVED,
        reviewer_user_id=1,
        reviewer_display_name="Reviewer",
        remarks="Verified patent evidence for scoring integrity test.",
        indicator_id=indicator_id,
        settings=_settings(),
    )
    return SimpleNamespace(
        public_id=public_id,
        criterion_id="kra2-b",
        indicator_id=indicator_id,
        extracted_info={"kra2EvidenceBundle": bundle},
        deleted_at=None,
        status="approved",
    )


def test_patent_highest_stage_only_counts_grant():
    docs = [
        _approved_patent_doc(public_id="d-a", indicator_id="kra2-b-patent-a-sole", reg="PH-123"),
        _approved_patent_doc(public_id="d-p", indicator_id="kra2-b-patent-p-sole", reg="PH-123"),
        _approved_patent_doc(public_id="d-g", indicator_id="kra2-b-patent-g-sole", reg="PH-123"),
    ]
    block = aggregate_kra2_criterion_from_documents(
        docs,
        criterion_id="kra2-b",
        settings=_settings(),
        applicable_config_present=True,
    )
    assert block["validatedPoints"] == 80.0


def test_kra_total_sums_criteria_and_caps_at_100():
    journal = _approved_journal_doc(public_id="j1")
    grant = _approved_patent_doc(public_id="g1", indicator_id="kra2-b-patent-g-sole", reg="PH-999")
    block = aggregate_kra2_kra_from_documents(
        [journal, grant],
        settings=_settings(),
        applicable_config_present=True,
    )
    assert block["estimatedPoints"] == 100.0
    assert block["validatedPoints"] == 100.0
    assert block["aggregationPolicy"] == "criteria_sum_cap_at_kra_max"


def test_legacy_document_ignored_when_bundle_exists_for_indicator():
    bundle_doc = _approved_journal_doc(public_id="b1")
    legacy = SimpleNamespace(
        public_id="legacy1",
        criterion_id="kra2-a",
        indicator_id="kra2-a-journal-sole",
        extracted_info={"estimatedPoints": 999.0},
        deleted_at=None,
        status="approved",
    )
    block = aggregate_kra2_criterion_from_documents(
        [bundle_doc, legacy],
        criterion_id="kra2-a",
        settings=_settings(),
        applicable_config_present=True,
    )
    assert block["validatedPoints"] == 50.0
    assert block.get("legacyCompanionPoints") in (None, 0.0)


def test_rank_simulation_kra2_uses_criteria_adapter():
    doc = _approved_patent_doc(public_id="g2", indicator_id="kra2-b-patent-g-sole", reg="PH-555")
    block = aggregate_criterion_documents_from_list(
        [doc],
        kra_key="kra2",
        criterion_id="kra2-b",
        settings=_settings(),
    )
    assert block.get("simulationAdapterEnabled") is True
    assert block.get("validatedPoints") == 80.0


def test_patent_different_registration_numbers_both_count():
    d1 = _approved_patent_doc(public_id="p1", indicator_id="kra2-b-patent-g-sole", reg="PH-AAA")
    d2 = _approved_patent_doc(public_id="p2", indicator_id="kra2-b-patent-g-sole", reg="PH-BBB")
    block = aggregate_kra2_criterion_from_documents(
        [d1, d2],
        criterion_id="kra2-b",
        settings=_settings(),
        applicable_config_present=True,
    )
    assert block["validatedPoints"] == 100.0


def test_patent_similar_titles_different_reg_both_count_before_cap():
    d1 = _approved_patent_doc(public_id="t1", indicator_id="kra2-b-patent-g-sole", reg="PH-111")
    d1.extracted_info["kra2EvidenceBundle"]["outputTitle"] = "Solar Water Purifier"
    d2 = _approved_patent_doc(public_id="t2", indicator_id="kra2-b-patent-g-sole", reg="PH-222")
    d2.extracted_info["kra2EvidenceBundle"]["outputTitle"] = "Solar Water Purifier"
    block = aggregate_kra2_criterion_from_documents(
        [d1, d2],
        criterion_id="kra2-b",
        settings=_settings(),
        applicable_config_present=True,
    )
    assert block["validatedPoints"] == 100.0


def test_patent_grant_plus_commercialization_same_period():
    grant = _approved_patent_doc(public_id="g", indicator_id="kra2-b-patent-g-sole", reg="PH-COMBO")
    comm = build_initial_bundle(
        primary_document_id="c1",
        primary_file_hash="hc",
        indicator_id="kra2-b-comm-local",
    )
    comm["outputTitle"] = "Product X"
    comm["outputVenue"] = "Local market"
    comm["publicationDate"] = "2025-06-01"
    comm["authorsLine"] = "Faculty A"
    comm["registrationNumber"] = "PH-COMBO"
    comm["metadataConfirmed"] = {
        "outputTitle": True,
        "outputVenue": True,
        "publicationDate": True,
        "authorsLine": True,
    }
    comm["submittedForReviewAt"] = "2025-06-01T00:00:00+00:00"
    comm["checklist"]["primary_output"]["status"] = SLOT_STATUS_VERIFIED
    apply_reviewer_accomplishment_decision(
        comm,
        review_status=REVIEW_APPROVED,
        reviewer_user_id=1,
        reviewer_display_name="Reviewer",
        remarks="Verified local commercialization evidence for scoring integrity test.",
        indicator_id="kra2-b-comm-local",
        settings=_settings(),
    )
    comm_doc = SimpleNamespace(
        public_id="c1",
        criterion_id="kra2-b",
        indicator_id="kra2-b-comm-local",
        extracted_info={"kra2EvidenceBundle": comm},
        deleted_at=None,
        status="approved",
    )
    block = aggregate_kra2_criterion_from_documents(
        [grant, comm_doc],
        criterion_id="kra2-b",
        settings=_settings(),
        applicable_config_present=True,
    )
    assert block["validatedPoints"] == 85.0


def test_apply_patent_highest_stage_only_unit():
    bundle_by_key = {
        "a": {"registrationNumber": "PH-1", "outputTitle": "X"},
        "p": {"registrationNumber": "PH-1", "outputTitle": "X"},
        "g": {"registrationNumber": "PH-1", "outputTitle": "X"},
    }
    indicator_by_key = {
        "a": "kra2-b-patent-a-sole",
        "p": "kra2-b-patent-p-sole",
        "g": "kra2-b-patent-g-sole",
    }
    points = {"a": 10.0, "p": 20.0, "g": 80.0}
    out = apply_patent_highest_stage_only(
        points,
        bundle_by_key=bundle_by_key,
        indicator_by_key=indicator_by_key,
    )
    assert out["g"] == 80.0
    assert out["a"] == 0.0
    assert out["p"] == 0.0
