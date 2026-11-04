"""Criterion B evidence slots: backend vs reviewer web catalog."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from documents.kra2_evidence.kra2_b_evidence_slots import criterion_b_required_slots
from documents.kra2_evidence.slots import primary_evidence_slot

ROOT = Path(__file__).resolve().parents[3]
WEB_UI = ROOT / "web" / "js" / "kra2-a-workspace-ui.js"

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


def _web_criterion_b_slots() -> dict[str, list[str]]:
    text = WEB_UI.read_text(encoding="utf-8")
    start = text.index("CRITERION_B_REQUIRED_SLOTS:")
    block = text[start : text.index("CRITERION_B_SLOT_LABELS:", start)]
    # Convert JS object to JSON (double-quoted keys already).
    jsonish = block.split(":", 1)[1].strip().rstrip(",").strip()
    return json.loads(jsonish)


@pytest.mark.parametrize("indicator_id", CRITERION_B_IDS)
def test_web_slots_match_backend(indicator_id: str):
    web = _web_criterion_b_slots()
    assert list(criterion_b_required_slots(indicator_id)) == web[indicator_id]


def test_co_software_includes_full_sole_checklist_plus_annex_g():
    co = criterion_b_required_slots("kra2-b-sw-new-co")
    sole = criterion_b_required_slots("kra2-b-sw-new-sole")
    assert co == sole + ("contribution_certificate",)


def test_co_variety_uses_deposit_not_primary_only():
    assert criterion_b_required_slots("kra2-b-variety-co") == (
        "registration_deposit_evidence",
        "contribution_certificate",
    )


def test_primary_upload_maps_to_first_required_slot_when_no_primary_output():
    assert primary_evidence_slot(indicator_id="kra2-b-comm-local") == "product_photo"
    assert primary_evidence_slot(indicator_id="kra2-b-variety-co") == "registration_deposit_evidence"
