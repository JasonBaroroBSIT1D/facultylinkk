"""Table 2.2 normalization, Table 3.1 brackets, and rank ladder increments."""

from types import SimpleNamespace

import pytest

from faculty.rank_hierarchy import apply_subrank_increment
from faculty.rank_simulation_engine import (
    TABLE_31_DEFAULTS,
    _kra_weighted_contribution,
    _score_bracket_and_increment,
    _weighted_estimated_total,
)


def test_weighted_contribution_normalizes_by_kra_max():
    weights = {"kra1": 60, "kra2": 10, "kra3": 20, "kra4": 10}
    kra_points = {
        "kra1": {"assessed": True, "estimatedPoints": 42.0, "maxPoints": 60.0},
        "kra2": {"assessed": True, "estimatedPoints": 0.0, "maxPoints": 100.0},
        "kra3": {"assessed": True, "estimatedPoints": 10.333, "maxPoints": 100.0},
        "kra4": {"assessed": True, "estimatedPoints": 41.0, "maxPoints": 100.0},
    }
    c1 = _kra_weighted_contribution(kra_points["kra1"], weights["kra1"], points=42.0)
    assert c1 == pytest.approx(42.0)  # (42/60)*60
    total = _weighted_estimated_total(kra_points, weights)
    assert total == pytest.approx(42.0 + 0.0 + 2.06666 + 4.1, rel=1e-3)


def test_table_31_brackets():
    assert _score_bracket_and_increment(40.9, TABLE_31_DEFAULTS) == (None, 0)
    assert _score_bracket_and_increment(41.0, TABLE_31_DEFAULTS) == ("41–50", 1)
    assert _score_bracket_and_increment(50.0, TABLE_31_DEFAULTS) == ("41–50", 1)
    assert _score_bracket_and_increment(51.0, TABLE_31_DEFAULTS) == ("51–60", 2)
    assert _score_bracket_and_increment(100.0, TABLE_31_DEFAULTS) == ("91–100", 6)


def test_rank_increment_instructor_i_plus_one():
    result = apply_subrank_increment("Instructor I", 1)
    assert result.possible_rank == "Instructor II"
    assert result.subrank_increment_applied == 1
    assert not result.rank_transition_blocked


def test_rank_increment_category_ceiling_without_transition_rules():
    result = apply_subrank_increment("Instructor I", 3)
    assert result.possible_rank == "Instructor III"
    assert result.subrank_increment_applied == 2
    assert result.rank_transition_blocked


def test_assistant_professor_alias():
    result = apply_subrank_increment("Asst. Professor I", 1)
    assert result.possible_rank == "Assistant Professor II"
