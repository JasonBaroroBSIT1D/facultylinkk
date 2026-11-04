"""Criterion A official scoring (JC 01 s. 2026 Annex A pp. 78–81)."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from documents.kra2_evidence.bundle import REVIEW_APPROVED, SLOT_STATUS_VERIFIED, build_initial_bundle
from documents.kra2_evidence.group_caps import apply_group_caps
from documents.kra2_evidence.kra2_a_evidence_slots import criterion_a_required_slots
from documents.kra2_evidence.reviewer_assessment import apply_reviewer_accomplishment_decision
from documents.kra2_evidence.scoring import (
    aggregate_kra2_criterion_from_documents,
    aggregate_kra2_kra_from_documents,
    estimated_points_for_bundle,
)
from documents.kra2_evidence.slots import required_slots
from kra_configuration.kra2_annex import (
    CRITERION_A_ID,
    published_kra2_criterion_max_points,
    published_kra2_indicator_base_points,
)
from kra_configuration.kra2_indicator_pdf_verification import indicator_verification_status

CRITERION_A_IDS = [
    "kra2-a-book-sole",
    "kra2-a-book-co",
    "kra2-a-chapter-sole",
    "kra2-a-chapter-co",
    "kra2-a-journal-sole",
    "kra2-a-journal-co",
    "kra2-a-monograph-sole",
    "kra2-a-monograph-co",
    "kra2-a-translation-sole",
    "kra2-a-translation-co",
    "kra2-a-cite",
]

# User-verified Annex A base points (DBM–CHED JC 01 s. 2026).
OFFICIAL_BASE: dict[str, float] = {
    "kra2-a-book-sole": 100,
    "kra2-a-book-co": 100,
    "kra2-a-chapter-sole": 35,
    "kra2-a-chapter-co": 35,
    "kra2-a-journal-sole": 50,
    "kra2-a-journal-co": 50,
    "kra2-a-monograph-sole": 100,
    "kra2-a-monograph-co": 100,
    "kra2-a-translation-sole": 35,
    "kra2-a-translation-co": 35,
    "kra2-a-cite": 10,
}

OFFICIAL_GROUP_MAX: dict[str, float] = {
    "kra2-a-translation-sole": 70,
    "kra2-a-translation-co": 70,
    "kra2-a-cite": 60,
}


def _settings() -> dict:
    ind = {}
    for iid in CRITERION_A_IDS:
        row = OFFICIAL_BASE[iid]
        gm = OFFICIAL_GROUP_MAX.get(iid)
        ind[iid] = {
            "points": row,
            "maxPoints": gm if gm else row,
            **({"groupMax": gm} if gm else {}),
        }
    return {
        "version": "criterion-a-audit-test",
        "kras": {"kra2": {"maxPoints": 100}},
        "criteria": {"kra2-a": {"maxPoints": 100}, "kra2-b": {"maxPoints": 100}, "kra2-c": {"maxPoints": 100}},
        "indicators": ind,
    }


def _verify_all_slots(bundle: dict, indicator_id: str) -> None:
    for slot in required_slots(indicator_id=indicator_id):
        bundle.setdefault("checklist", {})[slot] = {
            "status": SLOT_STATUS_VERIFIED,
            "documentId": f"doc_{slot}",
        }


@pytest.mark.parametrize("indicator_id", CRITERION_A_IDS)
def test_catalog_matches_official_annex_base_points(indicator_id: str):
    settings = _settings()
    base = published_kra2_indicator_base_points(indicator_id, settings, allow_annex_fallback=False)
    assert base == OFFICIAL_BASE[indicator_id]
    pdf = indicator_verification_status(indicator_id)
    assert pdf["status"] != "MISMATCH", pdf


@pytest.mark.parametrize("indicator_id", CRITERION_A_IDS)
def test_criterion_a_evidence_slots_annex_driven(indicator_id: str):
    slots = criterion_a_required_slots(indicator_id)
    assert "primary_output" in slots
    assert len(slots) >= 2


@pytest.mark.parametrize(
    "indicator_id,pct,expected",
    [
        ("kra2-a-book-co", 40, 40.0),
        ("kra2-a-chapter-co", 50, 17.5),
        ("kra2-a-journal-co", 25, 12.5),
    ],
)
def test_contribution_uses_declared_percent_not_author_order(indicator_id: str, pct: int, expected: float):
    bundle = build_initial_bundle(
        primary_document_id="doc_co",
        primary_file_hash="h",
        indicator_id=indicator_id,
    )
    bundle["declaredContributionPercent"] = pct
    est = estimated_points_for_bundle(bundle, indicator_id=indicator_id, settings=_settings(), applicable_config_present=True)
    assert est == expected


def test_translation_group_cap_seventy():
    pts = {"a1": 35.0, "a2": 35.0, "a3": 35.0}
    ind = {"a1": "kra2-a-translation-sole", "a2": "kra2-a-translation-sole", "a3": "kra2-a-translation-sole"}
    capped = apply_group_caps(pts, indicator_by_accomplishment=ind)
    assert sum(capped.values()) == pytest.approx(70.0, abs=0.02)


def test_citation_group_cap_sixty():
    pts = {f"c{i}": 10.0 for i in range(8)}
    ind = {k: "kra2-a-cite" for k in pts}
    capped = apply_group_caps(pts, indicator_by_accomplishment=ind)
    assert sum(capped.values()) == pytest.approx(60.0, abs=0.02)


def test_criterion_a_subtotal_capped_at_100():
    docs = []
    for i, iid in enumerate(("kra2-a-book-sole", "kra2-a-journal-sole")):
        bundle = build_initial_bundle(
            primary_document_id=f"doc_{i}",
            primary_file_hash=f"h{i}",
            indicator_id=iid,
        )
        bundle["outputTitle"] = "T"
        bundle["outputVenue"] = "V"
        bundle["authorsLine"] = "A"
        bundle["publicationDate"] = "2025-01-01"
        bundle["metadataConfirmed"] = {
            "outputTitle": True,
            "outputVenue": True,
            "authorsLine": True,
            "publicationDate": True,
        }
        bundle["submittedForReviewAt"] = "2025-06-01T00:00:00+00:00"
        _verify_all_slots(bundle, iid)
        apply_reviewer_accomplishment_decision(
            bundle,
            review_status=REVIEW_APPROVED,
            reviewer_user_id=1,
            reviewer_display_name="Reviewer",
            remarks="Verified for criterion A cap test.",
            indicator_id=iid,
            settings=_settings(),
        )
        docs.append(
            SimpleNamespace(
                public_id=f"doc_{i}",
                criterion_id=CRITERION_A_ID,
                indicator_id=iid,
                extracted_info={"kra2EvidenceBundle": bundle},
                deleted_at=None,
                status="approved",
            )
        )
    block = aggregate_kra2_criterion_from_documents(
        docs,
        criterion_id=CRITERION_A_ID,
        settings=_settings(),
        applicable_config_present=True,
    )
    assert block["validatedPoints"] == 100.0
    kra = aggregate_kra2_kra_from_documents(docs, settings=_settings(), applicable_config_present=True)
    assert kra["validatedPoints"] == 100.0


def test_criterion_a_max_from_published_config():
    cap = published_kra2_criterion_max_points(CRITERION_A_ID, _settings(), allow_annex_fallback=False)
    assert cap == 100.0


def test_reviewer_assessed_persisted_separate_from_estimate():
    bundle = build_initial_bundle(
        primary_document_id="doc_j",
        primary_file_hash="h",
        indicator_id="kra2-a-journal-sole",
    )
    bundle["submittedForReviewAt"] = "2025-01-01T00:00:00+00:00"
    _verify_all_slots(bundle, "kra2-a-journal-sole")
    apply_reviewer_accomplishment_decision(
        bundle,
        review_status=REVIEW_APPROVED,
        reviewer_user_id=1,
        reviewer_display_name="R",
        remarks="Approved with indexing adjustment.",
        assessed_points=30.0,
        score_adjustment_reason="Journal tier below full Scopus eligibility per RD certification.",
        indicator_id="kra2-a-journal-sole",
        settings=_settings(),
    )
    est = estimated_points_for_bundle(bundle, indicator_id="kra2-a-journal-sole", settings=_settings())
    assert est == 50.0
    assert bundle["reviewerAssessment"]["assessedPoints"] == 30.0
    assert bundle["reviewerAssessment"]["approvedPoints"] == 30.0
