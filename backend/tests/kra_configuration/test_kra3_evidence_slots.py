"""All 46 catalog indicators resolve to non-empty evidence slots."""

from __future__ import annotations

import json
from pathlib import Path

from documents.kra3_evidence.slots import required_slots

DATA = Path(__file__).resolve().parents[2] / "kra_configuration" / "data" / "kra3_indicators.json"


def test_all_catalog_indicators_have_slots():
    payload = json.loads(DATA.read_text(encoding="utf-8"))
    ids = [row["id"] for row in payload["indicators"]]
    assert len(ids) == 46
    for iid in ids:
        slots = required_slots(indicator_id=iid)
        assert len(slots) >= 1, iid
