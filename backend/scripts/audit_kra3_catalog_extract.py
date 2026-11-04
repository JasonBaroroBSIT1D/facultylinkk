"""Read-only extract of KRA III indicators from rules.js (no DB writes)."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RULES = ROOT / "web" / "js" / "rules.js"


def main() -> None:
    text = RULES.read_text(encoding="utf-8")
    start = text.index('id: "kra3"')
    end = text.index('id: "kra4"', start)
    block = text[start:end]
    # crude parse indicator blocks
    ids = re.findall(r'id: "(kra3-[^"]+)"', block)
    rows = []
    for iid in ids:
        # slice per-indicator block for fields
        pos = block.index(f'id: "{iid}"')
        nxt = block.find('id: "kra3-', pos + 5)
        ch = block[pos:nxt if nxt > 0 else len(block)]
        name = re.search(r'name: "([^"]+)"', ch)
        pts = re.search(r"points: (\d+)", ch)
        mx = re.search(r"maxPoints: (\d+)", ch)
        formula = "formula" in ch and "rating" in ch
        group = re.search(r'group: "(kra3[^"]+)"', ch)
        gmax = re.search(r"max: (\d+)", ch)
        rows.append(
            {
                "id": iid,
                "name": name.group(1) if name else "",
                "points": None if formula else (int(pts.group(1)) if pts else None),
                "maxPoints": int(mx.group(1)) if mx else None,
                "formulaRating": formula,
                "groupMax": int(gmax.group(1)) if group and gmax else None,
                "group": group.group(1) if group else None,
            }
        )
    by_crit: dict[str, list] = {}
    for r in rows:
        crit = "-".join(r["id"].split("-")[:2])
        by_crit.setdefault(crit, []).append(r)
    print(json.dumps({"total": len(rows), "byCriterion": {k: len(v) for k, v in sorted(by_crit.items())}}, indent=2))
    for r in rows:
        print(r["id"], r.get("points"), r.get("maxPoints"))


if __name__ == "__main__":
    main()
