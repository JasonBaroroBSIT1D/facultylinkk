"""Write docs/KRA2_CRITERION_B_OFFICIAL_AUDIT.md."""

from __future__ import annotations

import sys
from pathlib import Path

_BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_BACKEND))

from documents.kra2_evidence.kra2_b_evidence_slots import criterion_b_required_slots
from kra_configuration.kra2_indicator_pdf_verification import indicator_verification_status

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "KRA2_CRITERION_B_OFFICIAL_AUDIT.md"

CRITERION_B_IDS = [
    "kra2-b-patent-a-sole",
    "kra2-b-patent-a-co",
    "kra2-b-patent-p-sole",
    "kra2-b-patent-p-co",
    "kra2-b-patent-g-sole",
    "kra2-b-patent-g-co",
    "kra2-b-comm-local",
    "kra2-b-comm-intl",
    "kra2-b-um-sole",
    "kra2-b-um-co",
    "kra2-b-id-sole",
    "kra2-b-id-co",
    "kra2-b-sw-new-sole",
    "kra2-b-sw-new-co",
    "kra2-b-sw-upd-sole",
    "kra2-b-sw-upd-co",
    "kra2-b-variety-sole",
    "kra2-b-variety-co",
]


def main() -> None:
    lines = [
        "# KRA II Criterion B (Inventions) — official rules audit",
        "",
        "Source: DBM–CHED Joint Circular No. 01, s. 2026 — **Sections 22–24**, Annex A pp. **81–84** (PDF).",
        "",
        "Text extraction from the scanned PDF is unavailable; point values and annex references cross-check ",
        "`kra2_indicator_pdf_verification.py` (visual annex verification). Evidence slot IDs are implemented in ",
        "`backend/documents/kra2_evidence/kra2_b_evidence_slots.py` and aligned to catalog `evidenceHints`.",
        "",
        "## Policy rules (Sections 22–24)",
        "",
        "| Rule | PDF reference | Implementation |",
        "|---|---|---|",
        "| Criterion B maximum 100 points | p. 17, 81 | `aggregate_kra2_criterion_from_documents` |",
        "| Patent acceptance 10 / publication 20 / grant 80 | p. 81 | Published Admin indicator points |",
        "| **Highest patent stage only** (same invention) | **Sec. 23.1.f, p. 18** | `patent_deduplication.apply_patent_highest_stage_only` |",
        "| Patent + commercialization may both credit (same period) | p. 20 | Separate indicators; no cross-family dedup |",
        "| Co-inventor / co-developer contribution (Annex F/G/H) | pp. 18–19 | `declaredContributionPercent` + contribution certificate slot |",
        "| Commercialization sub-caps (local 20, international 30) | p. 82 | `groupMax` on `kra2-b-comm-local` / `kra2-b-comm-intl` |",
        "| OCR advisory only; reviewer verifies | Sec. 23 (general) | Bundle validation + slot verification statuses |",
        "",
        "## Scoring matrix (18 indicators)",
        "",
        "| Indicator | Official base | Group / output cap | Configured | PDF status | Annex ref | Required evidence slots |",
        "|---|---:|---:|---:|---|---|---|",
    ]
    mismatches = []
    for iid in CRITERION_B_IDS:
        v = indicator_verification_status(iid)
        status = v.get("status")
        if status == "MISMATCH":
            mismatches.append(iid)
        slots = ", ".join(criterion_b_required_slots(iid))
        pdf = v.get("pdfBasePoints")
        gmax = v.get("catalogMaxPoints")
        annex = v.get("annexRef") or "—"
        lines.append(
            f"| `{iid}` | {pdf} | {gmax} | {v.get('catalogPoints')} / {v.get('catalogMaxPoints')} "
            f"| {status} | {annex} | `{slots}` |"
        )
    lines.extend(
        [
            "",
            "## Discrepancies vs pre-audit implementation",
            "",
            "| Area | Before | After |",
            "|---|---|---|",
            "| Evidence checklist | `primary_output` (+ Annex D cert for co only) | Annex A multi-slot checklists per indicator family |",
            "| Faculty mobile slot list | Generic primary + contribution | Matches backend `criterion_b_required_slots` |",
            "| Reviewer web slot list | Generic primary + contribution | Uses API `requiredEvidenceSlots` + B catalog fallback |",
            "| `kra2-b-variety-sole` catalog hints | Corrupted placeholder | Restored from Annex B.2.2 |",
            "",
            "## Unverified / reviewer-gated (not machine-scored)",
            "",
            "- Whether commercialization proof meets “reputable” or ITSO policy thresholds.",
            "- Substantial functionality test for updated software (qualitative).",
            "- International commercialization jurisdiction details.",
            "",
            "## Configuration versioning",
            "",
            "No published scoring version overwrite. Existing approved bundles retain locked configuration; ",
            "new submissions expand checklist slots non-destructively via `ensure_checklist_slots`.",
            "",
        ]
    )
    if mismatches:
        lines.append("**Point mismatches:** " + ", ".join(mismatches))
    else:
        lines.append("**Point values:** Catalog matches annex base points for all 18 Criterion B indicators.")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT}; mismatches={len(mismatches)}")


if __name__ == "__main__":
    main()
