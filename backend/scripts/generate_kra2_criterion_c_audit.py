"""Write docs/KRA2_CRITERION_C_OFFICIAL_AUDIT.md."""

from __future__ import annotations

import sys
from pathlib import Path

_BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_BACKEND))

from documents.kra2_evidence.kra2_c_evidence_slots import criterion_c_required_slots
from kra_configuration.kra2_indicator_pdf_verification import indicator_verification_status
from kra_configuration.kra2_indicator_registry import indicators_for_criterion

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "KRA2_CRITERION_C_OFFICIAL_AUDIT.md"


def main() -> None:
    ids = [r["id"] for r in indicators_for_criterion("kra2-c")]
    lines = [
        "# KRA II Criterion C (Creative Works) — official rules audit",
        "",
        "Source: DBM–CHED Joint Circular No. 01, s. 2026 — **Sections 25–27**, Annex A pp. **84–92**.",
        "",
        "Point values cross-check `kra2_indicator_pdf_verification.py`. Evidence slot IDs: ",
        "`backend/documents/kra2_evidence/kra2_c_evidence_slots.py` (aligned to catalog `evidenceHints`).",
        "",
        "## Policy rules (Sections 25–27)",
        "",
        "| Rule | PDF reference | Implementation |",
        "|---|---|---|",
        "| Criterion C maximum **100** points | Sec. 25, p. 24; Annex p. 84 | `published_kra2_criterion_max_points('kra2-c')` |",
        "| KRA II total = A + B + C capped at **100** | Annex p. 78 | `aggregate_kra2_kra_from_documents` |",
        "| Co-creator points = base × declared % (Annex I) | Sec. 26 / Annex I | `estimated_points_for_bundle` + contribution certificate slot |",
        "| Multiple accomplishments sum to criterion cap | Annex “per output” rows | `aggregate_kra2_criterion_from_documents` |",
        "| Verified points only after reviewer approval | General KRA II workflow | `score_accomplishment_document` |",
        "",
        "## Scoring matrix (25 indicators)",
        "",
        "| Indicator | Official base | Output max | Configured | PDF status | Annex ref | Required evidence slots |",
        "|---|---:|---:|---:|---|---|---|",
    ]
    mismatches = []
    for iid in ids:
        v = indicator_verification_status(iid)
        status = v.get("status")
        if status == "MISMATCH":
            mismatches.append(iid)
        slots = ", ".join(criterion_c_required_slots(iid))
        lines.append(
            f"| `{iid}` | {v.get('pdfBasePoints')} | {v.get('pdfMaxPoints')} | "
            f"{v.get('catalogPoints')} / {v.get('catalogMaxPoints')} | {status} | "
            f"{v.get('annexRef') or '—'} | `{slots}` |"
        )
    lines.extend(
        [
            "",
            "## Points vs Maximum (Admin UI)",
            "",
            "- **Points** — official **base points per qualifying output** (Annex A “Points” column).",
            "- **Maximum** — for Criterion C indicators, equals **per-accomplishment cap** (same as base for fixed rows; ",
            "co-authored rows use base × verified contribution %, capped by this maximum).",
            "- **Criterion C `maxPoints` (100)** — **aggregate cap** for all approved Criterion C accomplishments in the evaluation period.",
            "- **Not** a separate “group max” tier for creative works (unlike translation or commercialization in Criteria A/B).",
            "",
            "## Discrepancies",
            "",
        ]
    )
    if mismatches:
        lines.append("**MISMATCH indicators:** " + ", ".join(f"`{m}`" for m in mismatches))
    else:
        lines.append("**None** — catalog, `rules.js`, and PDF verification map agree on base/max for all 25 indicators.")
    lines.append("")
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
