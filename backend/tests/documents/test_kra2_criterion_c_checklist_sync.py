"""Criterion C evidence slots: backend vs reviewer web catalog."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from documents.kra2_evidence.kra2_c_evidence_slots import criterion_c_required_slots
from documents.kra2_evidence.slots import primary_evidence_slot
from kra_configuration.kra2_indicator_registry import indicators_for_criterion

ROOT = Path(__file__).resolve().parents[3]
WEB_UI = ROOT / "web" / "js" / "kra2-a-workspace-ui.js"
MOBILE_CATALOG = ROOT / "mobile" / "lib" / "data" / "kra2_catalog.dart"

CRITERION_C_IDS = [r["id"] for r in indicators_for_criterion("kra2-c")]


def _web_criterion_c_slots() -> dict[str, list[str]]:
    text = WEB_UI.read_text(encoding="utf-8")
    start = text.index("CRITERION_C_REQUIRED_SLOTS:")
    end = text.index("CRITERION_B_SLOT_LABELS:", start)
    block = text[start:end]
    jsonish = block.split(":", 1)[1].strip().rstrip(",").strip()
    return json.loads(jsonish)


def _mobile_criterion_c_slots() -> dict[str, list[str]]:
    text = MOBILE_CATALOG.read_text(encoding="utf-8")
    start = text.index("const criterionCSlots = {")
    block = text[start : text.index("};", start)]
    out: dict[str, list[str]] = {}
    for m in re.finditer(r"'(kra2-c-[^']+)':\s*\[([^\]]*)\]", block):
        ind = m.group(1)
        inner = m.group(2)
        slots = [s.strip().strip("'") for s in inner.split(",") if s.strip()]
        out[ind] = slots
    return out


@pytest.mark.parametrize("indicator_id", CRITERION_C_IDS)
def test_web_slots_match_backend(indicator_id: str):
    web = _web_criterion_c_slots()
    assert list(criterion_c_required_slots(indicator_id)) == web[indicator_id]


@pytest.mark.parametrize("indicator_id", CRITERION_C_IDS)
def test_mobile_slots_match_backend(indicator_id: str):
    mobile = _mobile_criterion_c_slots()
    assert list(criterion_c_required_slots(indicator_id)) == mobile[indicator_id]


def test_co_indicators_include_annex_i_certificate():
    co = criterion_c_required_slots("kra2-c-novel-co")
    assert co == ("primary_output", "contribution_certificate")


def test_primary_evidence_slot_is_primary_output():
    assert primary_evidence_slot(indicator_id="kra2-c-music-comp-sole") == "primary_output"
