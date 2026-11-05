"""Advisory OCR hints for KRA IV evidence (never auto-approves)."""

from __future__ import annotations

import re
from typing import Any

from kra_configuration.kra4_indicator_registry import workflow_family

OCR_EXTRACTION_KEY = "kra4OcrExtraction"

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


def ensure_kra4_ocr_extraction(doc: Any) -> dict[str, Any] | None:
    """Reuse document-level OCR text when present; indicator-specific parsing is advisory."""
    info = dict(getattr(doc, "extracted_info", None) or {})
    existing = info.get(OCR_EXTRACTION_KEY)
    if isinstance(existing, dict):
        return existing
    raw = (
        getattr(doc, "extracted_text", None)
        or getattr(doc, "ocr_text", None)
        or info.get("ocrText")
        or ""
    )
    if not isinstance(raw, str) or not raw.strip():
        return None
    indicator_id = (getattr(doc, "indicator_id", None) or info.get("indicatorId") or "").strip()
    bundle = info.get("kra4EvidenceBundle")
    if isinstance(bundle, dict) and not indicator_id:
        indicator_id = (bundle.get("indicatorId") or "").strip()
    hints = _extract_hints_for_indicator(raw, indicator_id)
    if not hints:
        return None
    payload = {
        "version": "1.0",
        "indicatorId": indicator_id or None,
        "workflowFamily": workflow_family(indicator_id) if indicator_id else None,
        "hints": hints,
        "advisoryOnly": True,
    }
    info[OCR_EXTRACTION_KEY] = payload
    doc.extracted_info = info
    return payload


def _extract_hints_for_indicator(text: str, indicator_id: str) -> dict[str, str]:
    fam = workflow_family(indicator_id) if indicator_id else "generic"
    hints: dict[str, str] = {}
    if fam == "organization":
        _merge(hints, _org_membership_hints(text))
    elif fam == "education":
        _merge(hints, _education_hints(text))
    elif fam == "capacity_building":
        _merge(hints, _training_hints(text))
    elif fam == "paper_presentation":
        _merge(hints, _paper_hints(text))
    elif fam == "award":
        _merge(hints, _award_hints(text))
    elif fam == "prior_experience":
        _merge(hints, _employment_hints(text))
    else:
        _merge(hints, _generic_hints(text))
    return hints


def _merge(target: dict[str, str], extra: dict[str, str]) -> None:
    for key, val in extra.items():
        if key not in target and val:
            target[key] = val


def _generic_hints(text: str) -> dict[str, str]:
    hints: dict[str, str] = {}
    date = _first_date(text)
    if date:
        hints["activityDate"] = date
    org = _organization_line(text)
    if org:
        hints["organizationName"] = org
    return hints


def _org_membership_hints(text: str) -> dict[str, str]:
    hints = _generic_hints(text)
    role = re.search(
        r"(?:position|role|designation)\s*[:\-]?\s*([A-Za-z0-9][^\n]{2,60})",
        text,
        re.I,
    )
    if role:
        hints["facultyRole"] = role.group(1).strip()
    member = re.search(r"(?:member(?:ship)?|member\s+of)\s*[:\-]?\s*([^\n]{4,80})", text, re.I)
    if member and "organizationName" not in hints:
        hints["organizationName"] = member.group(1).strip()
    start, end = _service_dates(text)
    if start:
        hints["serviceStartDate"] = start
    if end:
        hints["serviceEndDate"] = end
    title = re.search(r"(?:certificate of membership|membership certificate)\s*[:\-]?\s*([^\n]{4,120})", text, re.I)
    if title:
        hints["activityTitle"] = title.group(1).strip()
    return hints


def _education_hints(text: str) -> dict[str, str]:
    hints: dict[str, str] = {}
    degree = re.search(
        r"(?:degree|program|qualification|diploma|doctorate|master(?:'?s)?)\s*[:\-]?\s*([^\n]{4,120})",
        text,
        re.I,
    )
    if degree:
        hints["degreeTitle"] = degree.group(1).strip()
    inst = re.search(
        r"(?:university|college|institution|school)\s*[:\-]?\s*([^\n]{4,120})",
        text,
        re.I,
    )
    if inst:
        hints["institutionName"] = inst.group(1).strip()
    date = _first_date(text)
    if date:
        hints["activityDate"] = date
    return hints


def _training_hints(text: str) -> dict[str, str]:
    hints = _generic_hints(text)
    event = re.search(
        r"(?:training|seminar|workshop|conference|symposium|webinar)\s*(?:title|name)?\s*[:\-]?\s*([^\n]{4,120})",
        text,
        re.I,
    )
    if event:
        hints["eventTitle"] = event.group(1).strip()
    hours = re.search(r"(\d+(?:\.\d+)?)\s*(?:hours|hrs|hour)\b", text, re.I)
    if hours:
        hints["eventDurationHours"] = hours.group(1)
    scope = _scope_hint(text)
    if scope:
        hints["eventScope"] = scope
    return hints


def _paper_hints(text: str) -> dict[str, str]:
    hints = _training_hints(text)
    paper = re.search(
        r"(?:paper|presentation|abstract)\s*(?:title|entitled)?\s*[:\-]?\s*([^\n]{4,160})",
        text,
        re.I,
    )
    if paper:
        hints["paperTitle"] = paper.group(1).strip()
    scope = _scope_hint(text)
    if scope:
        hints["eventScope"] = scope
    return hints


def _award_hints(text: str) -> dict[str, str]:
    hints = _generic_hints(text)
    award = re.search(
        r"(?:award|recognition|prize|medal)\s*(?:name|title)?\s*[:\-]?\s*([^\n]{4,120})",
        text,
        re.I,
    )
    if award:
        hints["awardTitle"] = award.group(1).strip()
    level = re.search(
        r"(?:level|category)\s*[:\-]?\s*(institutional|local|regional|national|international)",
        text,
        re.I,
    )
    if level:
        hints["awardLevel"] = level.group(1).capitalize()
    elif re.search(r"\binternational\b", text, re.I):
        hints["awardLevel"] = "International"
    elif re.search(r"\bnational\b", text, re.I):
        hints["awardLevel"] = "National"
    elif re.search(r"\blocal\b", text, re.I):
        hints["awardLevel"] = "Local"
    elif re.search(r"\binstitutional\b", text, re.I):
        hints["awardLevel"] = "Institutional"
    return hints


def _employment_hints(text: str) -> dict[str, str]:
    hints: dict[str, str] = {}
    employer = re.search(
        r"(?:employer|company|organization|institution)\s*[:\-]?\s*([^\n]{4,120})",
        text,
        re.I,
    )
    if employer:
        hints["employerName"] = employer.group(1).strip()
    position = re.search(
        r"(?:position|designation|title|role)\s*[:\-]?\s*([^\n]{4,80})",
        text,
        re.I,
    )
    if position:
        hints["positionTitle"] = position.group(1).strip()
    start, end = _service_dates(text)
    if start:
        hints["serviceStartDate"] = start
    if end:
        hints["serviceEndDate"] = end
    years = re.search(
        r"(\d+(?:\.\d+)?)\s*(?:years?|yrs)\s*(?:of\s*)?(?:experience|service)?",
        text,
        re.I,
    )
    if years:
        hints["experienceYears"] = years.group(1)
    return hints


def _first_date(text: str) -> str | None:
    m = re.search(r"\b((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+20\d{2})\b", text, re.I)
    if m:
        return m.group(1)
    m = re.search(r"\b(20\d{2}[-/]\d{1,2}[-/]\d{1,2})\b", text)
    if m:
        return m.group(1)
    m = re.search(r"\b(\d{1,2}[-/]\d{1,2}[-/]20\d{2})\b", text)
    if m:
        return m.group(1)
    return None


def _service_dates(text: str) -> tuple[str | None, str | None]:
    period = re.search(
        r"(?:from|period|tenure)\s*[:\-]?\s*(\d{1,2}[-/]\d{1,2}[-/]20\d{2}|\w+\s+\d{1,2},?\s+20\d{2})\s*(?:to|–|-|—)\s*(\d{1,2}[-/]\d{1,2}[-/]20\d{2}|\w+\s+\d{1,2},?\s+20\d{2})",
        text,
        re.I,
    )
    if period:
        return period.group(1).strip(), period.group(2).strip()
    return None, None


def _organization_line(text: str) -> str | None:
    m = re.search(r"(?:organization|association|society|council)\s*[:\-]?\s*([^\n]{4,100})", text, re.I)
    if m:
        return m.group(1).strip()
    return None


def _scope_hint(text: str) -> str | None:
    if re.search(r"\binternational\b", text, re.I):
        return "international"
    if re.search(r"\blocal\b", text, re.I):
        return "local"
    return None


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
        if key == "activityTitle" and _is_placeholder_title(bundle, str(val)):
            continue
        bundle[key] = str(val).strip()
        if key == "activityTitle" and not (bundle.get("outputTitle") or "").strip():
            bundle["outputTitle"] = str(val).strip()
    return bundle


def ocr_review_flags_for_document(doc: Any, bundle: dict[str, Any] | None) -> list[str]:
    _ = doc, bundle
    return []
