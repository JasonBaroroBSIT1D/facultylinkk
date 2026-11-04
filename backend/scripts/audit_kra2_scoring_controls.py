"""Print reviewer scoring control audit for all KRA II indicators."""

from __future__ import annotations

import sys
from pathlib import Path

_BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_BACKEND))

from documents.kra2_evidence.reviewer_assessment import (
    allows_reviewer_point_adjustment,
    reviewer_scoring_controls,
    reviewer_scoring_method,
    reviewer_scoring_method_label,
)
from kra_configuration.kra2_indicator_registry import all_indicators, reviewer_adjustment_governing_rule


def main() -> None:
    for row in all_indicators():
        iid = row["id"]
        meth = reviewer_scoring_method(iid)
        adj = allows_reviewer_point_adjustment(indicator_id=iid)
        ctrl = reviewer_scoring_controls(iid)
        print(
            f"{iid}\t{reviewer_scoring_method_label(meth)}\tpartial_adj={adj}\t"
            f"pts={row.get('points')}\tmax={row.get('maxPoints')}\tcontrib={row.get('contribution')}\t"
            f"rule={reviewer_adjustment_governing_rule(iid)[:60]}..."
        )


if __name__ == "__main__":
    main()
