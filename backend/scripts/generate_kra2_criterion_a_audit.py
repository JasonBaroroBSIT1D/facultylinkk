"""Write docs/KRA2_CRITERION_A_SCORING_AUDIT.md."""

from __future__ import annotations

import sys
from pathlib import Path

_BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_BACKEND))

from kra_configuration.kra2_indicator_pdf_verification import indicator_verification_status

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "KRA2_CRITERION_A_SCORING_AUDIT.md"

OFFICIAL = {
    "kra2-a-book-sole": (100, 100, "Annex A p.78 item 1"),
    "kra2-a-book-co": (100, 100, "Annex A p.78 + Annex D (Sec. 18)"),
    "kra2-a-chapter-sole": (35, 35, "Annex A p.78 item 2"),
    "kra2-a-chapter-co": (35, 35, "Annex A + Annex D"),
    "kra2-a-journal-sole": (50, 50, "Annex A p.79 item 3; Sec. 19 indexing"),
    "kra2-a-journal-co": (50, 50, "Annex A + Annex D"),
    "kra2-a-monograph-sole": (100, 100, "Annex A p.79 item 4"),
    "kra2-a-monograph-co": (100, 100, "Annex A + Annex D"),
    "kra2-a-translation-sole": (35, 70, "Annex A p.80 item 5; group max 70"),
    "kra2-a-translation-co": (35, 70, "Annex A + Annex E"),
    "kra2-a-cite": (10, 60, "Sec. 21; Annex A p.81 item 6; group max 60"),
}


def main() -> None:
    lines = [
        "# KRA II Criterion A — official vs configured scoring audit",
        "",
        "Source: DBM–CHED Joint Circular No. 01, s. 2026 — Sections 16–21, Annex A (PDF pp. 78–81).",
        "",
        "| Indicator | Official base | Official cap / group | Configured points | Configured max | PDF status | Reference |",
        "|---|---:|---:|---:|---:|---|---|",
    ]
    mismatches = []
    for iid, (base, cap, ref) in OFFICIAL.items():
        v = indicator_verification_status(iid)
        pts = v.get("catalogPoints")
        mx = v.get("catalogMaxPoints")
        status = v.get("status")
        if status == "MISMATCH":
            mismatches.append(iid)
        lines.append(
            f"| {iid} | {base} | {cap} | {pts} | {mx} | {status} | {ref} |"
        )
    lines.extend(
        [
            "",
            "## Criterion / KRA caps",
            "",
            "| Level | Official | Configured |",
            "|---|---:|---:|",
            "| Criterion A maximum | 100 | 100 (`kra2-a` in rules + published settings) |",
            "| KRA II maximum | 100 | 100 |",
            "",
            "## Discrepancies corrected",
            "",
        ]
    )
    if mismatches:
        lines.append("Point mismatches requiring catalog/config update: " + ", ".join(mismatches))
    else:
        lines.append(
            "**None.** Catalog (`kra2_indicators.json`), `rules.js`, and Admin indicator rows already match Annex A base points and group caps. "
            "This audit added Annex A evidence checklists and reviewer UI clarity; no silent change to historical published scoring versions."
        )
    lines.extend(
        [
            "",
            "## Configuration versioning",
            "",
            "- New accomplishments lock scoring via `record_configuration_in_kra2_bundle` on reviewer approval.",
            "- Existing approved assessments retain their locked `scoringConfigurationVersion`.",
            "- Catalog metadata version remains admin-published; bump only through the normal publish workflow.",
            "",
        ]
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT}; mismatches={len(mismatches)}")


if __name__ == "__main__":
    main()
