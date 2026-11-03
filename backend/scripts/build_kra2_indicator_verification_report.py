"""Generate KRA2_INDICATOR_VERIFICATION_REPORT.md from PDF cross-check registry."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kra_configuration.kra2_indicator_pdf_verification import (  # noqa: E402
    KRA2_AGGREGATION_FORMULA,
    all_indicator_verifications,
    verification_summary,
)


def main() -> None:
    rows = all_indicator_verifications()
    summary = verification_summary()
    out = ROOT / "docs" / "KRA2_INDICATOR_VERIFICATION_REPORT.md"
    lines = [
        "# KRA II — Per-indicator PDF verification report",
        "",
        f"**Total indicators:** {summary['total']}",
        f"**Points match annex (VERIFIED_POINTS):** {summary.get('verifiedPointsCount', 0)}",
        f"**PARTIAL (points OK; co-author/indexing eligibility):** {summary.get('partialCount', 0)}",
        f"**MISMATCH:** {summary.get('mismatchCount', 0)}",
        "",
        "## KRA II aggregation (official)",
        "",
        f"- **Status:** {KRA2_AGGREGATION_FORMULA['status']}",
        f"- **Formula:** `{KRA2_AGGREGATION_FORMULA['formula']}`",
        f"- **Per criterion:** `{KRA2_AGGREGATION_FORMULA['criterionFormula']}`",
        "- **PDF evidence:**",
    ]
    for ev in KRA2_AGGREGATION_FORMULA["pdfEvidence"]:
        lines.append(f"  - {ev}")
    lines.extend(["", "## Indicators", ""])
    lines.append("| ID | Status | PDF pages | Points (cat/PDF) | Max | Formula |")
    lines.append("|---|---|---|---:|---:|---|")
    for r in rows:
        lines.append(
            f"| `{r['id']}` | {r['status']} | {r.get('pdfPages')} | "
            f"{r.get('catalogPoints')}/{r.get('pdfBasePoints')} | "
            f"{r.get('catalogMaxPoints')}/{r.get('pdfMaxPoints')} | {r.get('formula')} |"
        )
    partial = [r["id"] for r in rows if r["status"] == "PARTIAL"]
    lines.extend(["", "## PARTIAL indicator IDs (eligibility / co-author)", "", ", ".join(f"`{x}`" for x in partial)])
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
