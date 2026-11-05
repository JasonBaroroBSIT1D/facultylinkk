"""Export KRA IV indicators from web/js/rules.js into kra_configuration/data/kra4_indicators.json."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RULES = ROOT / "web" / "js" / "rules.js"
OUT = ROOT / "backend" / "kra_configuration" / "data" / "kra4_indicators.json"


def _extract_kra4_block(text: str) -> str:
    start = text.find('id: "kra4"')
    if start < 0:
        raise RuntimeError("kra4 block not found in rules.js")
    end = text.find('id: "kra5"', start)
    if end < 0:
        end = text.find("\n  ];", start)
    return text[start:end]


def main() -> None:
    text = RULES.read_text(encoding="utf-8")
    block = _extract_kra4_block(text)
    indicators: list[dict] = []
    crit_re = re.compile(r'id:\s*"(kra4-[a-d])"')
    ind_re = re.compile(
        r'id:\s*"(kra4-[^"]+)"[\s\S]*?name:\s*"([^"]+)"[\s\S]*?points:\s*([0-9.]+)[\s\S]*?maxPoints:\s*([0-9.]+)',
        re.MULTILINE,
    )
    criterion_ids = crit_re.findall(block)
    for m in ind_re.finditer(block):
        iid, name, pts, mx = m.group(1), m.group(2), float(m.group(3)), float(m.group(4))
        if iid in ("kra4-a", "kra4-b", "kra4-c", "kra4-d"):
            continue
        cid = "-".join(iid.split("-")[:2])
        group = None
        group_max = None
        gm = re.search(
            rf'id:\s*"{re.escape(iid)}"[\s\S]*?groupMax:\s*\{{\s*group:\s*"([^"]+)"\s*,\s*max:\s*([0-9.]+)',
            block,
        )
        if gm:
            group = gm.group(1)
            group_max = float(gm.group(2))
        ev_match = re.search(
            rf'id:\s*"{re.escape(iid)}"[\s\S]*?evidence:\s*\[(.*?)\]',
            block,
            re.DOTALL,
        )
        evidence_hints: list[str] = []
        if ev_match:
            for em in re.finditer(r'"([^"]+)"', ev_match.group(1)):
                evidence_hints.append(em.group(1))
        indicators.append(
            {
                "id": iid,
                "criterionId": cid,
                "name": name,
                "points": pts,
                "maxPoints": mx,
                "contribution": "not-applicable",
                "group": group,
                "groupMax": group_max,
                "perYearRate": iid.startswith("kra4-d-"),
                "evidenceHints": evidence_hints,
            }
        )
    payload = {
        "version": "1.0",
        "source": "web/js/rules.js",
        "pdfVerified": False,
        "indicatorCount": len(indicators),
        "criteriaPresent": sorted(set(criterion_ids)),
        "indicators": indicators,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(indicators)} indicators to {OUT}")


if __name__ == "__main__":
    main()
