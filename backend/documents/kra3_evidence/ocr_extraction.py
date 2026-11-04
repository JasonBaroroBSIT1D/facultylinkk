"""Advisory OCR hints for KRA III evidence (never auto-approves)."""

from __future__ import annotations

import re
from typing import Any

OCR_EXTRACTION_KEY = "kra3OcrExtraction"

_UI_JUNK = re.compile(
    r"(upload|please enter|check your|send for review|facultylink|certificate of participation)",
    re.I,
)


def is_metadata_label_value(value: str, *, field_id: str = "") -> bool:
    text = (value or "").strip()
    if len(text) < 3:
        return True
    if _UI_JUNK.search(text):
        return True
    if text.lower() == field_id.replace("_", " ").lower():
        return True
    return False


def _is_placeholder_title(bundle: dict[str, Any], val: str) -> bool:
    _ = bundle
    return val.strip().lower() in ("untitled", "n/a", "test")


def ensure_kra3_ocr_extraction(doc: Any) -> dict[str, Any] | None:
    """Reuse document-level OCR text when present; indicator-specific parsing is advisory."""
    info = dict(getattr(doc, "extracted_info", None) or {})
    existing = info.get(OCR_EXTRACTION_KEY)
    if isinstance(existing, dict):
        return existing
    raw = getattr(doc, "ocr_text", None) or info.get("ocrText") or ""
    if not isinstance(raw, str) or not raw.strip():
        return None
    hints = _extract_hints(raw)
    if not hints:
        return None
    payload = {"version": "1.0", "hints": hints, "advisoryOnly": True}
    info[OCR_EXTRACTION_KEY] = payload
    doc.extracted_info = info
    return payload


def _extract_hints(text: str) -> dict[str, str]:
    hints: dict[str, str] = {}
    amount = re.search(r"(?:₱|PHP|P)\s*([\d,]+(?:\.\d{2})?)", text, re.I)
    if amount:
        hints["grossIncomeAmount"] = amount.group(1).replace(",", "")
    rating = re.search(r"(?:CSR|rating|satisfaction)\s*[:\-]?\s*(\d{1,3}(?:\.\d+)?)", text, re.I)
    if rating:
        hints["csrOverallRating"] = rating.group(1)
    date = re.search(r"\b(20\d{2}[-/]\d{1,2}[-/]\d{1,2})\b", text)
    if date:
        hints["activityDate"] = date.group(1)
    hours = re.search(r"(\d+(?:\.\d+)?)\s*(?:hours|hrs)\b", text, re.I)
    if hours:
        hints["deliveryHours"] = hours.group(1)
    return hints


def merge_ocr_into_bundle(bundle: dict[str, Any], extraction: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(extraction, dict):
        return bundle
    hints = extraction.get("hints")
    if not isinstance(hints, dict):
        return bundle
    confirmed = bundle.get("metadataConfirmed") if isinstance(bundle.get("metadataConfirmed"), dict) else {}
    for key, val in hints.items():
        if confirmed.get(key):
            continue
        if (bundle.get(key) or "").strip():
            continue
        if is_metadata_label_value(str(val), field_id=key):
            continue
        bundle[key] = str(val).strip()
        if key == "activityTitle" and not (bundle.get("outputTitle") or "").strip():
            bundle["outputTitle"] = str(val).strip()
    return bundle


def ocr_review_flags_for_document(doc: Any, bundle: dict[str, Any] | None) -> list[str]:
    _ = doc, bundle
    return []
