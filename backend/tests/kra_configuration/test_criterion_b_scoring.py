"""KRA I Criterion B annex mapping and scoring (no PostgreSQL)."""

from __future__ import annotations

import pytest

from kra_configuration.criterion_b_annex import (
    ANNEX_ROWS,
    CRITERION_B_INDICATOR_IDS,
    annex_row_for_indicator,
    indicator_requires_contribution_percent,
    is_criterion_b_indicator,
)
from kra_configuration.criterion_b_scoring import (
    aggregate_criterion_b_from_results,
    cap_criterion_b_total,
    cap_kra1_instruction_total,
    compute_criterion_b_indicator_points,
    published_base_points_for_annex_row,
    validate_contribution_percent,
)


def _criterion_b_settings() -> dict:
    return {
        "kras": {"kra1": {"maxPoints": 100}},
        "criteria": {
            "kra1-a": {"maxPoints": 60},
            "kra1-b": {"maxPoints": 30},
            "kra1-c": {"maxPoints": 10},
        },
        "indicators": {
            "kra1-b-textbook-sole": {"points": 30, "maxPoints": 30},
            "kra1-b-module-sole": {"points": 16, "maxPoints": 16},
            "kra1-b-manual-sole": {"points": 16, "maxPoints": 16},
            "kra1-b-multimedia-sole": {"points": 16, "maxPoints": 16},
            "kra1-b-program-lead": {"points": 10, "maxPoints": 10},
            "kra1-b-program-contributor": {"points": 5, "maxPoints": 5},
        },
    }


def test_all_ten_indicators_mapped_to_six_annex_rows():
    assert len(CRITERION_B_INDICATOR_IDS) == 10
    assert len(ANNEX_ROWS) == 6
    for ind in CRITERION_B_INDICATOR_IDS:
        assert is_criterion_b_indicator(ind)
        row = annex_row_for_indicator(ind)
        assert row is not None
        assert ind in row.indicator_ids


def test_co_indicators_require_contribution():
    assert indicator_requires_contribution_percent("kra1-b-textbook-co") is True
    assert indicator_requires_contribution_percent("kra1-b-textbook-sole") is False
    assert indicator_requires_contribution_percent("kra1-b-program-lead") is False


def test_co_uses_sole_base_from_published_config():
    settings = _criterion_b_settings()
    assert published_base_points_for_annex_row("kra1-b-textbook-co", settings) == 30.0
    assert published_base_points_for_annex_row("kra1-b-module-co", settings) == 16.0


def test_unverified_evidence_never_scores():
    settings = _criterion_b_settings()
    res = compute_criterion_b_indicator_points(
        "kra1-b-textbook-sole",
        evidence_verified=False,
        settings=settings,
    )
    assert res.points is None
    assert "evidence_not_verified" in res.reasons


def test_automated_estimate_before_verification():
    from kra_configuration.criterion_b_scoring import compute_criterion_b_indicator_automated_estimate

    settings = _criterion_b_settings()
    assert compute_criterion_b_indicator_automated_estimate(
        "kra1-b-textbook-sole",
        settings=settings,
    ) == 30.0
    assert compute_criterion_b_indicator_automated_estimate(
        "kra1-b-textbook-co",
        contribution_percent=50,
        settings=settings,
    ) == 15.0


def test_sole_textbook_full_base_when_verified():
    settings = _criterion_b_settings()
    res = compute_criterion_b_indicator_points(
        "kra1-b-textbook-sole",
        evidence_verified=True,
        settings=settings,
    )
    assert res.eligible is True
    assert res.points == 30.0
    assert res.annex_row_id == "textbook"


def test_co_author_percentage():
    settings = _criterion_b_settings()
    res = compute_criterion_b_indicator_points(
        "kra1-b-textbook-co",
        contribution_percent=60,
        evidence_verified=True,
        settings=settings,
    )
    assert res.points == 18.0

    res40 = compute_criterion_b_indicator_points(
        "kra1-b-textbook-co",
        contribution_percent=40,
        evidence_verified=True,
        settings=settings,
    )
    assert res40.points == 12.0


def test_co_missing_contribution():
    settings = _criterion_b_settings()
    res = compute_criterion_b_indicator_points(
        "kra1-b-module-co",
        evidence_verified=True,
        settings=settings,
    )
    assert res.points is None
    assert "contribution_percent_required" in res.reasons


@pytest.mark.parametrize("bad", [-1, 101, 150])
def test_contribution_out_of_range(bad):
    pct, err = validate_contribution_percent(bad)
    assert pct is None
    assert err == "contribution_percent_out_of_range"


def test_program_lead_and_contributor():
    settings = _criterion_b_settings()
    lead = compute_criterion_b_indicator_points(
        "kra1-b-program-lead",
        evidence_verified=True,
        settings=settings,
    )
    assert lead.points == 10.0
    contrib = compute_criterion_b_indicator_points(
        "kra1-b-program-contributor",
        evidence_verified=True,
        settings=settings,
    )
    assert contrib.points == 5.0


def test_criterion_b_cap_at_30():
    capped, raw = cap_criterion_b_total([30.0, 16.0], _criterion_b_settings())
    assert raw == 46.0
    assert capped == 30.0


def test_kra1_cap_at_100():
    total, parts = cap_kra1_instruction_total(
        criterion_a_points=60.0,
        criterion_b_points=30.0,
        criterion_c_points=10.0,
        settings=_criterion_b_settings(),
    )
    assert total == 100.0
    assert parts["kra1-b"] == 30.0

    over, _ = cap_kra1_instruction_total(
        criterion_a_points=60.0,
        criterion_b_points=30.0,
        criterion_c_points=15.0,
        settings=_criterion_b_settings(),
    )
    assert over == 100.0


def test_aggregate_best_per_indicator_then_cap():
    settings = _criterion_b_settings()
    low = compute_criterion_b_indicator_points(
        "kra1-b-textbook-co",
        contribution_percent=40,
        evidence_verified=True,
        settings=settings,
    )
    high = compute_criterion_b_indicator_points(
        "kra1-b-textbook-co",
        contribution_percent=60,
        evidence_verified=True,
        settings=settings,
    )
    capped, raw = aggregate_criterion_b_from_results([low, high], settings)
    assert raw == 18.0
    assert capped == 18.0
