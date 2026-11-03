"""Preserve Criterion C bundle metadata across OCR (faculty-confirmed fields)."""

from __future__ import annotations

from typing import Any

from documents.criterion_c_evidence.ocr_research import (
    OCR_EXTRACTION_KEY,
    preserve_criterion_c_bundle_fields,
    snapshot_criterion_c_bundle,
)

BUNDLE_EXTRACTED_KEY = "criterionCEvidenceBundle"


def snapshot_criterion_c_extracted_fields(info: dict | None) -> dict[str, Any]:
    if not isinstance(info, dict):
        return {}
    snap: dict[str, Any] = {}
    bundle = snapshot_criterion_c_bundle(info)
    if bundle:
        snap[BUNDLE_EXTRACTED_KEY] = bundle
    if OCR_EXTRACTION_KEY in info:
        snap[OCR_EXTRACTION_KEY] = info[OCR_EXTRACTION_KEY]
    return snap


def preserve_criterion_c_extracted_info(*, before: dict, after: dict) -> dict:
    return preserve_criterion_c_bundle_fields(before, after)
