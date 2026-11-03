"""Phase 5B: Criterion B rank simulation wiring (isolated; flag off in production)."""

from __future__ import annotations

from types import SimpleNamespace
import pytest

from documents.criterion_b_evidence.bundle import (
    SLOT_STATUS_VERIFIED,
    apply_slot_link,
    build_initial_bundle,
)
from documents.criterion_b_evidence.checklist import SLOT_PRIMARY_MATERIAL, required_slots
from faculty.kra_document_aggregate import aggregate_criterion_documents_from_list
from faculty.rank_simulation_engine import _build_kra1_criteria_scores, _kra1_from_teaching
from kra_configuration.criterion_b_scoring import cap_kra1_instruction_total
from tests.documents.test_criterion_b_simulation_adapter import (
    _primary_doc,
    _scoring_ready_im_bundle,
    _scoring_ready_program_bundle,
    _settings,
    _verify_program_slots,
)
def _legacy_kra1_b_doc(*, points: float = 25.0, public_id: str = "legacy_b"):
    return SimpleNamespace(
        public_id=public_id,
        criterion_id="kra1-b",
        kra_id="kra1",
        indicator_id="kra1-b-textbook-sole",
        extracted_info={},
        deleted_at=None,
        status="approved",
        verified_points=points,
        reviewer_score=None,
        estimated_points=points,
        ocr_status="completed",
    )


def _unverified_with_legacy_points():
    bundle = apply_slot_link(
        build_initial_bundle(
            primary_document_id="doc_p",
            primary_file_hash="hash_unverified",
            indicator_id="kra1-b-textbook-sole",
            material_title="Unverified Book",
        ),
        slot_id="imdc_evaluation_approval",
        supporting_document_id="doc_sup",
        supporting_file_hash="hash_sup",
    )
    doc = _primary_doc(bundle=bundle, indicator_id="kra1-b-textbook-sole", public_id="unv")
    doc.verified_points = 30.0
    doc.estimated_points = 30.0
    return doc


def test_flag_disabled_preserves_legacy_criterion_b_aggregation(monkeypatch):
    monkeypatch.setattr(
        "documents.scoring.criterion_b_simulation_adapter.CRITERION_B_SIMULATION_ADAPTER_ENABLED",
        False,
    )
    docs = [_legacy_kra1_b_doc(points=25.0)]
    block = aggregate_criterion_documents_from_list(
        docs,
        kra_key="kra1",
        criterion_id="kra1-b",
        settings=_settings(),
    )
    assert block["scoringSource"] == "legacy_document_points"
    assert block["estimatedPoints"] == 25.0
    assert block["assessed"] is True


def test_flag_enabled_uses_adapter_for_verified_claim(monkeypatch):
    monkeypatch.setattr(
        "documents.scoring.criterion_b_simulation_adapter.CRITERION_B_SIMULATION_ADAPTER_ENABLED",
        True,
    )
    doc = _primary_doc(
        bundle=_scoring_ready_im_bundle(indicator_id="kra1-b-module-sole"),
        indicator_id="kra1-b-module-sole",
        public_id="ready_mod",
    )
    block = aggregate_criterion_documents_from_list(
        [doc],
        kra_key="kra1",
        criterion_id="kra1-b",
        settings=_settings(),
    )
    assert block["scoringSource"] == "criterion_b_evidence_bundle"
    assert block["aggregationPolicy"] == "provisional_output_deduplication"
    assert block["estimatedPoints"] == 16.0


def test_flag_enabled_unverified_legacy_points_contribute_zero(monkeypatch):
    monkeypatch.setattr(
        "documents.scoring.criterion_b_simulation_adapter.CRITERION_B_SIMULATION_ADAPTER_ENABLED",
        True,
    )
    doc = _unverified_with_legacy_points()
    block = aggregate_criterion_documents_from_list(
        [doc],
        kra_key="kra1",
        criterion_id="kra1-b",
        settings=_settings(),
    )
    assert block["estimatedPoints"] is None
    assert block["assessed"] is False


def test_flag_enabled_co_author_verified_contribution(monkeypatch):
    monkeypatch.setattr(
        "documents.scoring.criterion_b_simulation_adapter.CRITERION_B_SIMULATION_ADAPTER_ENABLED",
        True,
    )
    doc = _primary_doc(
        bundle=_scoring_ready_im_bundle(indicator_id="kra1-b-module-co"),
        indicator_id="kra1-b-module-co",
        public_id="co_mod",
    )
    block = aggregate_criterion_documents_from_list(
        [doc],
        kra_key="kra1",
        criterion_id="kra1-b",
        settings=_settings(),
    )
    assert block["estimatedPoints"] == pytest.approx(6.4)


def test_flag_enabled_duplicate_material_one_credit(monkeypatch):
    monkeypatch.setattr(
        "documents.scoring.criterion_b_simulation_adapter.CRITERION_B_SIMULATION_ADAPTER_ENABLED",
        True,
    )
    low = _scoring_ready_im_bundle(indicator_id="kra1-b-module-co")
    low["contributionPercent"] = 25
    high = _scoring_ready_im_bundle(indicator_id="kra1-b-module-co")
    high["contributionPercent"] = 50
    high["checklist"]["primary_material"]["fileHash"] = low["checklist"]["primary_material"][
        "fileHash"
    ]
    docs = [
        _primary_doc(bundle=low, indicator_id="kra1-b-module-co", public_id="d1"),
        _primary_doc(bundle=high, indicator_id="kra1-b-module-co", public_id="d2"),
    ]
    block = aggregate_criterion_documents_from_list(
        docs,
        kra_key="kra1",
        criterion_id="kra1-b",
        settings=_settings(),
    )
    assert block["estimatedPoints"] == pytest.approx(8.0)


def test_flag_enabled_distinct_outputs_same_indicator_sum_to_cap(monkeypatch):
    monkeypatch.setattr(
        "documents.scoring.criterion_b_simulation_adapter.CRITERION_B_SIMULATION_ADAPTER_ENABLED",
        True,
    )
    def _ready(title: str, fh: str, pid: str) -> SimpleNamespace:
        bundle = build_initial_bundle(
            primary_document_id=pid,
            primary_file_hash=fh,
            indicator_id="kra1-b-module-sole",
            material_title=title,
        )
        for slot in required_slots(bundle["materialType"] or "", authorship="sole"):
            entry = (bundle.get("checklist") or {}).get(slot) or {}
            if not entry.get("documentId"):
                bundle = apply_slot_link(
                    bundle,
                    slot_id=slot,
                    supporting_document_id=f"sup_{slot}_{pid}",
                    supporting_file_hash=f"h_{slot}_{pid}",
                )
        bundle["completeSetDeclared"] = True
        bundle["specializationAligned"] = True
        for slot in list(required_slots("module", authorship="sole")) + [SLOT_PRIMARY_MATERIAL]:
            entry = bundle["checklist"].get(slot)
            if isinstance(entry, dict) and entry.get("documentId"):
                entry["status"] = SLOT_STATUS_VERIFIED
        return _primary_doc(bundle=bundle, indicator_id="kra1-b-module-sole", public_id=pid)

    docs = [
        _ready("Module A", "hash_a", "a"),
        _ready("Module B", "hash_b", "b"),
    ]
    block = aggregate_criterion_documents_from_list(
        docs,
        kra_key="kra1",
        criterion_id="kra1-b",
        settings=_settings(),
    )
    assert block["estimatedPoints"] == 30.0


def test_flag_enabled_program_claim_uses_published_config(monkeypatch):
    monkeypatch.setattr(
        "documents.scoring.criterion_b_simulation_adapter.CRITERION_B_SIMULATION_ADAPTER_ENABLED",
        True,
    )
    doc = _primary_doc(
        bundle=_scoring_ready_program_bundle(),
        indicator_id="kra1-b-program-lead",
        public_id="prog",
    )
    block = aggregate_criterion_documents_from_list(
        [doc],
        kra_key="kra1",
        criterion_id="kra1-b",
        settings=_settings(),
    )
    assert block["estimatedPoints"] == 10.0


def test_kra1_criteria_scores_payload_shape_unchanged_with_flag_off(monkeypatch):
    monkeypatch.setattr(
        "documents.scoring.criterion_b_simulation_adapter.CRITERION_B_SIMULATION_ADAPTER_ENABLED",
        False,
    )
    profile = SimpleNamespace(id=1)
    settings = _settings()
    settings["criteria"]["kra1-a"] = {"maxPoints": 60}
    settings["criteria"]["kra1-c"] = {"maxPoints": 10}

    def _agg(_profile, _kra, cid):
        if cid == "kra1-b":
            return aggregate_criterion_documents_from_list(
                [_legacy_kra1_b_doc()],
                kra_key="kra1",
                criterion_id=cid,
                settings=settings,
            )
        return {
            "criterionId": cid,
            "estimatedPoints": None,
            "maxPoints": 10,
            "assessed": False,
        }

    from unittest.mock import patch

    with patch("faculty.rank_simulation_engine.aggregate_criterion_documents", side_effect=_agg):
        te = {
            "combinedProvisionalPoints": 40.0,
            "criterionMaxPoints": 60,
            "criterionADisplay": {"displayLabel": "Estimated"},
        }
        scores = _build_kra1_criteria_scores(profile, te, settings)
    assert {s["criterionId"] for s in scores} == {"kra1-a", "kra1-b", "kra1-c"}
    b_row = next(s for s in scores if s["criterionId"] == "kra1-b")
    assert b_row["estimatedPoints"] == 25.0
    assert "name" in b_row and "maxPoints" in b_row and "bonus" in b_row


def test_kra1_instruction_cap_helper_unchanged():
    settings = _settings()
    settings["criteria"]["kra1-a"] = {"maxPoints": 60}
    settings["criteria"]["kra1-c"] = {"maxPoints": 10}
    settings["kras"] = {"kra1": {"maxPoints": 100}}
    total, parts = cap_kra1_instruction_total(
        criterion_a_points=60.0,
        criterion_b_points=30.0,
        criterion_c_points=15.0,
        settings=settings,
    )
    assert total == 100.0
    assert parts["kra1-b"] == 30.0


def test_criterion_a_set_sef_path_untouched_when_b_uses_adapter(
):
    from unittest.mock import patch

    mock_settings = _settings()
    entries = [
        {"criterionId": "kra1-a", "maxPoints": 60},
        {"criterionId": "kra1-b", "maxPoints": 30},
        {"criterionId": "kra1-c", "maxPoints": 10},
    ]

    def crit_max(cid, settings=None):
        return {"kra1-a": 60.0, "kra1-b": 30.0, "kra1-c": 10.0}.get(cid)

    def crit_docs(_p, _k, cid):
        return {
            "kra1-b": {
                "criterionId": "kra1-b",
                "estimatedPoints": 16.0,
                "maxPoints": 30.0,
                "assessed": True,
            },
            "kra1-c": {
                "criterionId": "kra1-c",
                "estimatedPoints": None,
                "maxPoints": 10.0,
                "assessed": False,
            },
        }[cid]

    te = {
        "set": {"coverageSummary": {"totalUploads": 1}, "provisionalPoints": 33.0},
        "sef": {"coverageSummary": {"totalUploads": 0}},
        "combinedProvisionalPoints": 33.0,
        "criterionMaxPoints": 60,
        "criterionADisplay": {"estimatedPoints": 33.0, "displayLabel": "Estimated"},
    }
    profile = SimpleNamespace(id=1, current_rank="Instructor I", target_rank="")
    with (
        patch(
            "faculty.rank_simulation_engine._published_settings",
            return_value=(mock_settings, SimpleNamespace(row=SimpleNamespace(id=1), has_applicable_row=True)),
        ),
        patch("faculty.rank_simulation_engine.published_kra_max_points", return_value=100.0),
        patch("faculty.rank_simulation_engine.published_criterion_max_points", side_effect=crit_max),
        patch("faculty.rank_simulation_engine.criteria_entries_for_kra", return_value=entries),
        patch("faculty.rank_simulation_engine.aggregate_criterion_documents", side_effect=crit_docs),
    ):
        block = _kra1_from_teaching(profile, te, 5)
    assert block["estimatedPoints"] == pytest.approx(49.0)
    assert block["criteriaScores"][0]["estimatedPoints"] == 33.0
    assert next(s for s in block["criteriaScores"] if s["criterionId"] == "kra1-b")["estimatedPoints"] == 16.0
