"""Generate backend/docs/KRA2_OFFICIAL_RULES_MATRIX.md from web/js/rules.js (JC 01 s. 2026 catalog)."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RULES_JS = ROOT / "web" / "js" / "rules.js"
OUT = ROOT / "backend" / "docs" / "KRA2_OFFICIAL_RULES_MATRIX.md"
PDF = ROOT / "backend" / "docs" / "2026-DBM-CHED-JC-01-Enhanced-Implementing-Guidelines-of-JC3-series-of-2022 (1).pdf"


def _extract_kra2_block(text: str) -> str:
    start = text.find('id: "kra2"')
    if start < 0:
        raise SystemExit("kra2 block not found in rules.js")
    end = text.find('id: "kra3"', start)
    return text[start:end] if end > start else text[start:]


def _parse_indicators(block: str) -> list[dict]:
    """Lightweight parse of indicator objects in the kra2 block."""
    rows: list[dict] = []
    chunks = re.split(r"\{\s*\n\s*id: \"(kra2-[^\"]+)\"", block)
    # chunks[0] is preamble; then alternating id, body
    i = 1
    while i + 1 < len(chunks):
        ind_id = chunks[i]
        body = chunks[i + 1]
        i += 2
        if ind_id in ("kra2-a", "kra2-b", "kra2-c"):
            continue
        name_m = re.search(r'name: "([^"]+)"', body)
        pts_m = re.search(r"points: (\d+(?:\.\d+)?)", body)
        max_m = re.search(r"maxPoints: (\d+(?:\.\d+)?)", body)
        contrib_m = re.search(r'contribution: "([^"]+)"', body)
        crit = ind_id.split("-")[0] + "-" + ind_id.split("-")[1]  # kra2-a
        rows.append(
            {
                "criterionId": crit,
                "indicatorId": ind_id,
                "name": name_m.group(1) if name_m else ind_id,
                "basePoints": float(pts_m.group(1)) if pts_m else None,
                "indicatorMax": float(max_m.group(1)) if max_m else None,
                "contribution": contrib_m.group(1) if contrib_m else "unknown",
            }
        )
    return rows


def _implementation_status() -> dict[str, str]:
    """Honest repo audit snapshot (manual labels; update as modules land)."""
    return {
        "admin_scoring_config": "PARTIAL — KRA II in rules.js + publish JSON; no JC-enforced validation",
        "backend_evidence_bundles": "NOT STARTED — no kra2_evidence module (generic Document rows only)",
        "backend_scoring_engine": "PARTIAL — aggregate_documents_for_kra + document-stored points",
        "faculty_mobile": "PARTIAL — KRA explorer + generic upload; no KRA II accomplishment wizard",
        "reviewer_web": "PARTIAL — generic document review; no Criterion A/B/C accomplishment workspaces",
        "rank_simulation": "PARTIAL — kra2 slot uses document aggregates, not full criterion adapters",
        "ocr": "PARTIAL — generic OCR; no KRA II structured metadata extractors",
    }


def main() -> None:
    text = RULES_JS.read_text(encoding="utf-8")
    block = _extract_kra2_block(text)
    indicators = _parse_indicators(block)
    by_crit: dict[str, list] = {}
    for row in indicators:
        by_crit.setdefault(row["criterionId"], []).append(row)

    pdf_note = (
        f"Official PDF present at `{PDF.relative_to(ROOT)}` (130 pages). "
        "Automated text extraction returned empty on sampled pages (likely scanned). "
        "Matrix values below are taken from the repository’s JC-aligned catalog in "
        "`web/js/rules.js` and `mobile/assets/kra_catalog.json` until PDF text is OCR’d for cross-check."
    )
    status = _implementation_status()

    lines = [
        "# KRA II — Official Rules Matrix (Implementation Reference)",
        "",
        "**Source:** DBM–CHED Joint Circular No. 01, s. 2026 (Enhanced Implementing Guidelines).",
        "",
        pdf_note,
        "",
        "## KRA II totals (catalog)",
        "",
        "| Field | Official value (catalog) |",
        "|---|---|",
        "| KRA ID | `kra2` |",
        "| Title | Research, Innovation and/or Creative Work |",
        "| KRA maximum | 100 points (alternative categories — not sum of 300) |",
        "| Criterion A max | 100 |",
        "| Criterion B max | 100 |",
        "| Criterion C max | 100 |",
        "",
        "## Implementation status snapshot",
        "",
    ]
    for k, v in status.items():
        lines.append(f"- **{k.replace('_', ' ').title()}:** {v}")
    lines.append("")
    lines.append("## Indicators by criterion")
    lines.append("")

    crit_names = {
        "kra2-a": "Criterion A — Research Outputs Published",
        "kra2-b": "Criterion B — Inventions",
        "kra2-c": "Criterion C — Citations and Research Impact",
    }
    for crit_id in ("kra2-a", "kra2-b", "kra2-c"):
        lines.append(f"### {crit_names.get(crit_id, crit_id)}")
        lines.append("")
        lines.append(
            "| Indicator ID | Name | Base pts | Ind. max | Contribution | Evidence (see rules.js) | Backend bundle |"
        )
        lines.append("|---|---|---:|---:|---|---|---|")
        for row in sorted(by_crit.get(crit_id, []), key=lambda r: r["indicatorId"]):
            bp = row["basePoints"]
            im = row["indicatorMax"]
            lines.append(
                f"| `{row['indicatorId']}` | {row['name']} | {bp if bp is not None else '—'} | "
                f"{im if im is not None else '—'} | {row['contribution']} | Annex D–G as applicable | NOT STARTED |"
            )
        lines.append("")

    lines.append("## Scoring rules (all criteria)")
    lines.append("")
    lines.append("- Use **published** Admin configuration for base points and caps (`kra_settings` JSON).")
    lines.append("- **Co-authored / declared contribution:** points = base × declared % (Annex D/F/G forms).")
    lines.append("- **Group caps:** translation (70), citations (60), commercialization sub-groups — see `groupMax` in rules.js.")
    lines.append("- **Patent stages:** credit highest stage only within evaluation period (Criterion B).")
    lines.append("- **KRA II total:** min(sum of credited accomplishments, 100); criteria are alternative categories.")
    lines.append("- **Estimated vs verified:** faculty estimates from published indicator points; reviewer-assessed points on approval.")
    lines.append("")
    lines.append(f"_Generated {len(indicators)} indicators from rules.js._")
    lines.append("")

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"output": str(OUT), "indicatorCount": len(indicators)}, indent=2))


if __name__ == "__main__":
    main()
