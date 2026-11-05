"""Extract KRA IV (Professional Development) text from official JC PDF and compare to catalog."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
PDF = ROOT / "docs" / "2026-DBM-CHED-JC-01-Enhanced-Implementing-Guidelines-of-JC3-series-of-2022 (1).pdf"
CATALOG = ROOT / "kra_configuration" / "data" / "kra4_indicators.json"
OUT = REPO / "docs" / "KRA4_PDF_AUDIT_RESULTS.json"


def _load_pdf_text() -> str:
    import pymupdf

    if not PDF.is_file():
        raise FileNotFoundError(str(PDF))
    parts: list[str] = []
    with pymupdf.open(PDF) as doc:
        for page in doc:
            parts.append(page.get_text() or "")
    return "\n".join(parts)


def _extract_points_near(text: str, needle: str) -> list[str]:
    hits: list[str] = []
    for m in re.finditer(re.escape(needle[:40]), text, re.I):
        start = max(0, m.start() - 120)
        end = min(len(text), m.end() + 120)
        hits.append(text[start:end].replace("\n", " "))
    return hits[:3]


def main() -> int:
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    indicators = catalog.get("indicators") or []
    try:
        pdf_text = _load_pdf_text()
    except FileNotFoundError as exc:
        payload = {"status": "BLOCKED", "error": str(exc)}
        OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(json.dumps(payload, indent=2))
        return 2

    if len(pdf_text.strip()) < 50:
        payload = {
            "status": "BLOCKED",
            "pdfPath": str(PDF),
            "reason": "pdf_image_only_no_extractable_text",
            "hint": "Official JC PDF appears scanned; verify Sections 37–44 and Annex A manually or OCR the PDF offline.",
            "indicatorCount": len(indicators),
        }
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(json.dumps(payload, indent=2))
        return 3

    section_hits = {
        "section_37": "37" in pdf_text and "Professional Development" in pdf_text,
        "annex_a": "Annex A" in pdf_text or "ANNEX A" in pdf_text,
    }
    rows = []
    for row in indicators:
        iid = row.get("id") or ""
        name = (row.get("name") or "").strip()
        pts = row.get("points")
        name_found = name[:30].lower() in pdf_text.lower() if len(name) >= 10 else False
        pt_pattern = re.search(rf"\b{re.escape(str(int(pts)))}\b", pdf_text) if pts is not None else None
        rows.append(
            {
                "indicatorId": iid,
                "catalogName": name,
                "catalogPoints": pts,
                "nameFragmentInPdf": name_found,
                "pointsValueSomewhereInPdf": bool(pt_pattern),
                "pdfContextSample": _extract_points_near(pdf_text, name.split()[0] if name else iid),
                "implementationStatus": "needs_manual_pdf_row_match"
                if not (name_found or pt_pattern)
                else "likely_match_fragment_only",
            }
        )

    matched = sum(1 for r in rows if r["nameFragmentInPdf"] or r["pointsValueSomewhereInPdf"])
    payload = {
        "status": "PARTIAL" if matched < len(rows) else "PASS",
        "pdfPath": str(PDF),
        "indicatorCount": len(rows),
        "fragmentMatches": matched,
        "sectionSignals": section_hits,
        "disclaimer": "Automated fragment search only; human must verify Annex A table rows against JC 01 s. 2026.",
        "indicators": rows,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps({"status": payload["status"], "fragmentMatches": matched, "total": len(rows)}, indent=2))
    return 0 if matched >= len(rows) * 0.5 else 1


if __name__ == "__main__":
    raise SystemExit(main())
