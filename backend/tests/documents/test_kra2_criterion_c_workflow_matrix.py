"""All 25 Criterion C indicators — workflow subfamily, metadata, OCR routing."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from documents.kra2_evidence.kra2_c_evidence_slots import criterion_c_required_slots
from documents.kra2_evidence.ocr_profiles import coverage_rows
from kra_configuration.kra2_c_workflow import (
    criterion_c_metadata_label,
    criterion_c_ocr_parser_id,
    criterion_c_subfamily,
    coverage_row,
)
from kra_configuration.kra2_indicator_registry import indicators_for_criterion, metadata_field_ids

ROOT = Path(__file__).resolve().parents[3]
MOBILE_CATALOG = ROOT / "mobile" / "lib" / "data" / "kra2_catalog.dart"
WEB_UI = ROOT / "web" / "js" / "kra2-a-workspace-ui.js"

CRITERION_C_IDS = [r["id"] for r in indicators_for_criterion("kra2-c")]


def _mobile_label(indicator_id: str, field_id: str) -> str:
    text = MOBILE_CATALOG.read_text(encoding="utf-8")
    sub = criterion_c_subfamily(indicator_id)
    m = re.search(
        rf"'{re.escape(sub)}':\s*\{{([^}}]+)\}}",
        text,
        re.S,
    )
    assert m, f"mobile profile missing for subfamily {sub}"
    block = m.group(1)
    fm = re.search(rf"'{field_id}':\s*'([^']+)'", block)
    assert fm, f"mobile label missing {field_id} for {sub}"
    return fm.group(1)


def _web_label(indicator_id: str, field_id: str) -> str:
    sub = criterion_c_subfamily(indicator_id)
    text = WEB_UI.read_text(encoding="utf-8")
    m = re.search(rf"{sub}:\s*\{{([^}}]+)\}}", text, re.S)
    assert m, f"web profile missing for subfamily {sub}"
    block = m.group(1)
    fm = re.search(rf"{field_id}:\s*\"([^\"]+)\"", block)
    assert fm, f"web label missing {field_id} for {sub}"
    return fm.group(1)


@pytest.mark.parametrize("indicator_id", CRITERION_C_IDS)
def test_coverage_row_has_twenty_five_indicators(indicator_id: str):
    row = coverage_row(indicator_id)
    assert row["indicatorId"] == indicator_id
    assert row["subfamily"] == criterion_c_subfamily(indicator_id)
    assert row["ocrParser"] == criterion_c_ocr_parser_id(indicator_id)
    assert row["evidenceSlots"] == ",".join(criterion_c_required_slots(indicator_id))


@pytest.mark.parametrize("indicator_id", CRITERION_C_IDS)
def test_metadata_labels_sync_python_mobile_web(indicator_id: str):
    for field_id in ("outputTitle", "authorsLine", "outputVenue", "publicationDate"):
        py = criterion_c_metadata_label(field_id, indicator_id)
        mob = _mobile_label(indicator_id, field_id)
        web = _web_label(indicator_id, field_id)
        assert py == mob == web, (indicator_id, field_id, py, mob, web)


@pytest.mark.parametrize("indicator_id", CRITERION_C_IDS)
def test_metadata_fields_exclude_publication_reference(indicator_id: str):
    fields = metadata_field_ids(indicator_id)
    assert "publicationReference" not in fields


@pytest.mark.parametrize("indicator_id", CRITERION_C_IDS)
def test_ocr_coverage_lists_criterion_c_parser(indicator_id: str):
    by_id = {r["indicatorId"]: r for r in coverage_rows()}
    assert by_id[indicator_id]["parser"] == criterion_c_ocr_parser_id(indicator_id)


def test_exactly_twenty_five_c_indicators():
    assert len(CRITERION_C_IDS) == 25


def test_subfamily_map_json_snapshot():
    payload = {iid: criterion_c_subfamily(iid) for iid in CRITERION_C_IDS}
    assert len(set(payload.values())) >= 8
