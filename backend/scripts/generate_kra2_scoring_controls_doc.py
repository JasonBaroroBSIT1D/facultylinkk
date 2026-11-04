"""Generate docs/KRA2_REVIEWER_SCORING_CONTROLS.md."""

from __future__ import annotations

import sys
from pathlib import Path

_BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_BACKEND))

from documents.kra2_evidence.reviewer_assessment import reviewer_scoring_controls
from kra_configuration.kra2_indicator_registry import all_indicators, reviewer_adjustment_governing_rule

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "KRA2_REVIEWER_SCORING_CONTROLS.md"


def main() -> None:
    lines = [
        "# KRA II reviewer scoring controls (54 indicators)",
        "",
        "Admin-published points and formulas are unchanged. Reviewers verify evidence and assess within these rules.",
        "",
        "| Indicator | Method | Partial adjustment allowed | Official max (catalog) | Governing rule |",
        "|---|---|---:|---:|---|",
    ]
    for row in all_indicators():
        iid = row["id"]
        ctrl = reviewer_scoring_controls(iid)
        mx = max(float(row.get("points") or 0), float(row.get("maxPoints") or row.get("points") or 0))
        rule = reviewer_adjustment_governing_rule(iid).replace("|", "/")
        partial = "Yes" if ctrl["allowsPointAdjustment"] else "No"
        lines.append(
            f"| {iid} | {ctrl['scoringMethodLabel']} | {partial} | {mx:g} | {rule} |"
        )
    lines.extend(
        [
            "",
            "## Field meanings (Reviewer Web)",
            "",
            "- **Official maximum** — Published Admin cap for this indicator row (per accomplishment).",
            "- **System-calculated eligible points** — Base points × verified contribution % when applicable.",
            "- **Your assessed points** — Reviewer decision stored as `assessedPoints` / `approvedPoints` on approval.",
            "- **Estimated points** (faculty/simulation) — Advisory until review is approved.",
            "",
        ]
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
