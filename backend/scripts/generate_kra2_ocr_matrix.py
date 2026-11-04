"""Write docs/KRA2_OCR_COVERAGE_MATRIX.md from the indicator registry."""

from __future__ import annotations

import sys
from pathlib import Path

_BACKEND = Path(__file__).resolve().parents[1]
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from documents.kra2_evidence.ocr_extraction import OCR_EXTRACTION_VERSION
from documents.kra2_evidence.ocr_profiles import coverage_rows

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "KRA2_OCR_COVERAGE_MATRIX.md"


def main() -> None:
    rows = coverage_rows()
    lines = [
        "# KRA II OCR coverage matrix (54 indicators)",
        "",
        f"OCR extraction version: **{OCR_EXTRACTION_VERSION}**.",
        "",
        "| Indicator | Criterion | Family | Parser | Metadata fields | OCR keys | Automated |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in sorted(rows, key=lambda x: x["indicatorId"]):
        lines.append(
            f"| {r['indicatorId']} | {r['criterionId']} | {r['workflowFamily']} | {r['parser']} | "
            f"{r['metadataFields']} | {r['ocrKeys']} | routing + family snippet |"
        )
    lines.extend(
        [
            "",
            "## Status legend",
            "",
            "- **IMPLEMENTED**: Family parser + `ocr_profiles` row + `extract_fields_for_indicator` routing.",
            "- **TESTED (automated)**: `test_kra2_ocr_indicator_coverage` (218 parametrized cases) + layout fixtures.",
            "- **PARTIAL**: Real-world PDF layouts vary; only representative snippets per family, not 54 unique PDFs.",
            "- **NOT TESTED (E2E)**: Full Faculty Mobile upload → draft → submit → Reviewer Web on device/browser.",
            "",
        ]
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT} ({len(rows)} indicators)")


if __name__ == "__main__":
    main()
