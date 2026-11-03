"""Phase C5: configuration resolver, Criterion C cap, publish integrity (unit)."""

from __future__ import annotations

from datetime import date, datetime, timezone
from types import SimpleNamespace

import pytest

from documents.criterion_c_evidence.scoring import aggregate_criterion_c_from_documents
from kra_configuration.publish_integrity import validate_scoring_integrity
from kra_configuration.resolver import (
    effective_window,
    row_is_applicable_on,
    select_best_applicable_row,
)
from kra_configuration.criterion_c_annex import published_criterion_c_max_points, published_points_for_indicator


def _row(*, row_id: int, status: str, eff_from: str, eff_to: str | None = None, published_at: str = "2024-01-01T00:00:00+00:00"):
    pub = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
    return SimpleNamespace(
        id=row_id,
        status=status,
        published_at=pub,
        settings_json={"effectiveFrom": eff_from, "effectiveTo": eff_to, "version": row_id},
        guideline_label="Test",
        rank_weights={},
    )


def test_future_effective_configuration_excluded():
    as_of = date(2024, 6, 1)
    rows = [
        _row(row_id=2, status="published", eff_from="2025-01-01"),
        _row(row_id=1, status="superseded", eff_from="2023-01-01"),
    ]
    chosen = select_best_applicable_row(rows, as_of)
    assert chosen is not None
    assert chosen.id == 1


def test_selects_latest_effective_from_among_applicable():
    as_of = date(2024, 6, 1)
    rows = [
        _row(row_id=1, status="superseded", eff_from="2023-01-01", published_at="2023-06-01T00:00:00+00:00"),
        _row(row_id=2, status="published", eff_from="2024-01-01", published_at="2024-02-01T00:00:00+00:00"),
    ]
    chosen = select_best_applicable_row(rows, as_of)
    assert chosen.id == 2


def test_draft_row_never_applicable():
    row = _row(row_id=9, status="draft", eff_from="2020-01-01")
    row.published_at = None
    assert not row_is_applicable_on(row, date(2024, 1, 1))


def test_criterion_c_dynamic_max_from_settings():
    settings = {"criteria": {"kra1-c": {"maxPoints": 12}}}
    assert published_criterion_c_max_points(settings, allow_annex_fallback=False) == 12.0


def test_criterion_c_no_silent_annex_when_applicable_config():
    settings = {"criteria": {"kra1-c": {"maxPoints": 10}}, "indicators": {}}
    assert published_points_for_indicator("kra1-c-adviser-sp", settings, allow_annex_fallback=False) is None
    assert published_points_for_indicator("kra1-c-adviser-sp", settings, allow_annex_fallback=True) == 3.0


def test_aggregate_criterion_c_uses_published_cap():
    settings = {"criteria": {"kra1-c": {"maxPoints": 8}}, "indicators": {"kra1-c-adviser-ut": {"points": 5}}}
    doc = SimpleNamespace(
        public_id="d1",
        criterion_id="kra1-c",
        indicator_id="kra1-c-adviser-ut",
        extracted_info={},
        deleted_at=None,
        status="approved",
        estimated_points=None,
        verified_points=None,
        reviewer_score=None,
        ocr_status="completed",
    )
    block = aggregate_criterion_c_from_documents([], settings=settings, applicable_config_present=True)
    assert block["maxPoints"] == 8.0


def test_publish_integrity_requires_criterion_c_max():
    settings = {
        "indicators": {"kra1-c-adviser-sp": {"points": 3}},
        "criteria": {},
    }
    checks, errors = validate_scoring_integrity(settings)
    assert "criterion_c_max_missing" in errors
    assert any(c["id"] == "criterion_c_max" and not c["ok"] for c in checks)


def test_publish_integrity_rejects_negative_points():
    settings = {
        "criteria": {"kra1-c": {"maxPoints": 10}},
        "indicators": {"kra1-c-adviser-sp": {"points": -1}},
    }
    _, errors = validate_scoring_integrity(settings)
    assert "indicator_values_invalid" in errors
