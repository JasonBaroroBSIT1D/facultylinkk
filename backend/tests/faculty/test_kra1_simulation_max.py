"""KRA I simulation uses summed criterion maximums (synthetic profile)."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

from faculty.rank_simulation_engine import _kra1_from_teaching


def _profile():
    return SimpleNamespace(id=1, current_rank="Instructor I", target_rank="")


@patch("faculty.rank_simulation_engine.aggregate_criterion_documents")
@patch("faculty.rank_simulation_engine._published_settings")
@patch("faculty.rank_simulation_engine.published_kra_max_points", return_value=100.0)
@patch("faculty.rank_simulation_engine.published_criterion_max_points")
@patch("faculty.rank_simulation_engine.criteria_entries_for_kra")
def test_kra1_block_uses_100_max(
    mock_entries,
    mock_crit_max,
    mock_kra_max,
    mock_settings,
    mock_crit_docs,
):
    settings = {
        "criteria": {
            "kra1-a": {"maxPoints": 60},
            "kra1-b": {"maxPoints": 30},
            "kra1-c": {"maxPoints": 10},
        }
    }
    mock_settings.return_value = (settings, SimpleNamespace(row=SimpleNamespace(id=1), has_applicable_row=True))
    mock_entries.return_value = [
        {"criterionId": "kra1-a", "maxPoints": 60},
        {"criterionId": "kra1-b", "maxPoints": 30},
        {"criterionId": "kra1-c", "maxPoints": 10},
    ]

    def crit_max(cid, settings=None):
        return {"kra1-a": 60.0, "kra1-b": 30.0, "kra1-c": 10.0}.get(cid)

    mock_crit_max.side_effect = crit_max
    mock_crit_docs.return_value = {"estimatedPoints": None, "maxPoints": 30, "assessed": False}

    te = {
        "set": {"coverageSummary": {"totalUploads": 1}, "provisionalPoints": 33.13},
        "sef": {"coverageSummary": {"totalUploads": 1}, "provisionalPoints": 22.09},
        "combinedProvisionalPoints": 55.22,
        "criterionMaxPoints": 60,
        "criterionADisplay": {"estimatedPoints": 55.22, "displayLabel": "Estimated"},
    }
    block = _kra1_from_teaching(_profile(), te, 12)
    assert block["maxPoints"] == 100.0
    assert block["targetPoints"] == 100
    assert block["estimatedPoints"] == 55.22
    assert len(block["criteriaScores"]) == 3
    assert block["criteriaScores"][0]["estimatedPoints"] == 55.22
