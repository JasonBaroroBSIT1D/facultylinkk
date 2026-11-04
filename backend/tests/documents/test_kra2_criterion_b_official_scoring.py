"""Criterion B official scoring and evidence slots (JC 01 s. 2026 Annex A pp. 81–84)."""

from __future__ import annotations

import pytest

from documents.kra2_evidence.kra2_b_evidence_slots import (
    criterion_b_required_slots,
    is_criterion_b_indicator,
)
from documents.kra2_evidence.patent_deduplication import patent_stage_rank
from documents.kra2_evidence.slots import required_slots
from kra_configuration.kra2_annex import published_kra2_indicator_base_points
from kra_configuration.kra2_indicator_pdf_verification import indicator_verification_status

CRITERION_B_IDS = [
    "kra2-b-patent-a-sole",
    "kra2-b-patent-a-co",
    "kra2-b-patent-p-sole",
    "kra2-b-patent-p-co",
    "kra2-b-patent-g-sole",
    "kra2-b-patent-g-co",
    "kra2-b-comm-local",
    "kra2-b-comm-intl",
    "kra2-b-um-sole",
    "kra2-b-um-co",
    "kra2-b-id-sole",
    "kra2-b-id-co",
    "kra2-b-sw-new-sole",
    "kra2-b-sw-new-co",
    "kra2-b-sw-upd-sole",
    "kra2-b-sw-upd-co",
    "kra2-b-variety-sole",
    "kra2-b-variety-co",
]

OFFICIAL_BASE = {
    "kra2-b-patent-a-sole": 10,
    "kra2-b-patent-p-sole": 20,
    "kra2-b-patent-g-sole": 80,
    "kra2-b-comm-local": 5,
    "kra2-b-comm-intl": 10,
    "kra2-b-um-sole": 10,
    "kra2-b-id-sole": 5,
    "kra2-b-sw-new-sole": 10,
    "kra2-b-sw-upd-sole": 4,
    "kra2-b-variety-sole": 10,
}


def _settings() -> dict:
    ind = {}
    for iid in CRITERION_B_IDS:
        v = indicator_verification_status(iid)
        ind[iid] = {
            "points": v["catalogPoints"],
            "maxPoints": v["catalogMaxPoints"],
        }
        if iid in ("kra2-b-comm-local", "kra2-b-comm-intl"):
            ind[iid]["group"] = iid
            ind[iid]["groupMax"] = v["catalogMaxPoints"]
    return {
        "version": "criterion-b-audit-test",
        "kras": {"kra2": {"maxPoints": 100}},
        "criteria": {"kra2-b": {"maxPoints": 100}},
        "indicators": ind,
    }


@pytest.mark.parametrize("indicator_id", CRITERION_B_IDS)
def test_criterion_b_catalog_points_match_annex(indicator_id: str):
    v = indicator_verification_status(indicator_id)
    assert v["status"] != "MISMATCH", v


@pytest.mark.parametrize("indicator_id,base", list(OFFICIAL_BASE.items()))
def test_published_base_points(indicator_id: str, base: float):
    settings = _settings()
    got = published_kra2_indicator_base_points(indicator_id, settings, allow_annex_fallback=False)
    assert got == base


def test_patent_sole_requires_photo_and_special_order():
    slots = criterion_b_required_slots("kra2-b-patent-g-sole")
    assert "primary_output" in slots
    assert "invention_photo" in slots
    assert "president_special_order" in slots


def test_commercialization_requires_five_slot_bundle():
    slots = criterion_b_required_slots("kra2-b-comm-local")
    assert len(slots) == 5
    assert "patent_certificate" in slots
    assert "commercialization_proof" in slots


def test_required_slots_router_uses_criterion_b():
    assert is_criterion_b_indicator("kra2-b-patent-a-sole")
    assert len(required_slots(indicator_id="kra2-b-sw-new-sole")) >= 4


def test_patent_stage_rank_ordering():
    assert patent_stage_rank("kra2-b-patent-a-sole") < patent_stage_rank("kra2-b-patent-p-sole")
    assert patent_stage_rank("kra2-b-patent-p-sole") < patent_stage_rank("kra2-b-patent-g-sole")


def test_coauthored_patent_um_id_use_ip_doc_plus_annex_f_only():
    for iid in ("kra2-b-patent-g-co", "kra2-b-um-co", "kra2-b-id-co"):
        slots = criterion_b_required_slots(iid)
        assert slots == ("primary_output", "contribution_certificate")


def test_coauthored_software_extends_sole_slots_with_annex_g():
    sole = criterion_b_required_slots("kra2-b-sw-upd-sole")
    co = criterion_b_required_slots("kra2-b-sw-upd-co")
    assert co == sole + ("contribution_certificate",)
    assert len(co) == 6
