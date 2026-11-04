"""Export KRA III indicator catalog from web/js/rules.js."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RULES_JS = ROOT / "web" / "js" / "rules.js"
OUT = ROOT / "backend" / "kra_configuration" / "data" / "kra3_indicators.json"
MOBILE_OUT = ROOT / "mobile" / "assets" / "kra3_indicators.json"


def main() -> None:
    text = RULES_JS.read_text(encoding="utf-8")
    start = text.find('id: "kra3"')
    end = text.find('id: "kra4"', start)
    block = text[start:end] if end > start else text[start:]
    chunks = re.split(r'\{\s*\n\s*id: "(kra3-[^"]+)"', block)
    rows: list[dict] = []
    i = 1
    while i + 1 < len(chunks):
        iid = chunks[i]
        body = chunks[i + 1]
        i += 2
        if iid in ("kra3-a", "kra3-b", "kra3-c", "kra3-d"):
            continue

        def grab(pattern: str, default=None):
            m = re.search(pattern, body)
            return m.group(1) if m else default

        pts = grab(r"points: (\d+(?:\.\d+)?)")
        mx = grab(r"maxPoints: (\d+(?:\.\d+)?)")
        formula = "formula" in body and "rating" in body
        grp = grab(r'group: "([^"]+)"')
        gmax_m = re.search(r"groupMax:\s*\{\s*group:\s*\"[^\"]+\",\s*max:\s*(\d+(?:\.\d+)?)", body)
        gmax = gmax_m.group(1) if gmax_m else None
        evidence: list[str] = []
        if "evidence:" in body:
            ev_block = body.split("evidence:")[1]
            if "conditions:" in ev_block:
                ev_block = ev_block.split("conditions:")[0]
            evidence = re.findall(r'"([^"]{6,})"', ev_block)[:8]

        row = {
            "id": iid,
            "criterionId": "-".join(iid.split("-")[:2]),
            "name": grab(r'name: "([^"]+)"', iid),
            "points": None if formula else (float(pts) if pts else None),
            "maxPoints": float(mx) if mx else None,
            "contribution": grab(r'contribution: "([^"]+)"', "not-applicable"),
            "group": grp,
            "groupMax": float(gmax) if gmax else None,
            "formulaRating": formula,
            "evidenceHints": evidence,
        }
        if formula:
            mult = grab(r"multiplier: (\d+(?:\.\d+)?)")
            if mult:
                row["formulaMultiplier"] = float(mult)
        rows.append(row)

    payload = {
        "version": "1.0",
        "source": "web/js/rules.js",
        "pdfVerified": False,
        "indicatorCount": len(rows),
        "indicators": rows,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    MOBILE_OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(rows)} indicators to {OUT} and {MOBILE_OUT}")


if __name__ == "__main__":
    main()
