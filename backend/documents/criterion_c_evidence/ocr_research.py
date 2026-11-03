"""Structured research metadata extraction from approval-sheet OCR text (advisory only)."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from kra_configuration.criterion_c_annex import CRITERION_C_ID

from documents.criterion_c_evidence.bundle import (
    BUNDLE_EXTRACTED_KEY,
    SLOT_STATUS_PRESENT_UNVERIFIED,
    bundle_from_document,
    empty_checklist_entry,
    persist_bundle,
)
from documents.criterion_c_evidence.checklist import SLOT_APPROVAL_SHEET
from documents.criterion_c_evidence.research_metadata import (
    is_unreliable_research_title,
    normalize_academic_year,
)

OCR_EXTRACTION_KEY = "criterionCOcrExtraction"
OCR_EXTRACTION_VERSION = "1.1"

_FIELD_KEYS = (
    "projectTitle",
    "studentNames",
    "studentGroupLabel",
    "academicYear",
    "completionDate",
)

_TITLE_LABELS = (
    r"title\s+of\s+(?:the\s+)?(?:thesis|dissertation|study|research|project|capstone)",
    r"(?:research|project|thesis)\s+title",
    r"^title\s*:",
)

_STUDENT_LABELS = (
    r"student\s*\(?s?\)?\s*name?s?",
    r"^students?\s*\(?s?\)?\s*:?\s*$",
    r"name\s+of\s+(?:the\s+)?student\s*\(?s?\)?",
    r"names\s+of\s+(?:the\s+)?student\s*\(?s?\)?",
    r"researcher\s*\(?s?\)?\s*name?s?",
    r"proponent\s*\(?s?\)?\s*name?s?",
    r"prepared\s+by",
    r"submitted\s+by",
    r"^authors?\s*:",
)

_ADVISER_LABELS = (
    r"thesis\s+adviser",
    r"research\s+adviser",
    r"^adviser\s*\(?s?\)?",
    r"^advisor\s*\(?s?\)?",
    r"name\s+of\s+(?:the\s+)?adviser",
    r"name\s+of\s+(?:the\s+)?advisor",
)

_PANEL_LABELS = (
    r"panel\s*members?",
    r"panelists?",
    r"names\s+of\s+(?:the\s+)?panel",
    r"committee\s*members?",
    r"board\s+of\s+examiners",
)

_GROUP_LABELS = (
    r"group\s+(?:name|label|no\.?|number|#)",
    r"team\s+name",
)

_AY_PATTERN = re.compile(
    r"(?:A\.?\s*Y\.?|Academic\s+Year|School\s+Year|S\.?\s*Y\.?)\s*[:\-]?\s*"
    r"(\d{4}\s*[-–/]\s*\d{2,4})",
    re.I,
)

_DATE_PATTERN = re.compile(
    r"(?:date\s+(?:of\s+)?(?:approval|completion|defense)|approval\s+date|defense\s+date|"
    r"date\s+approved|approved\s+on|signed\s+on)\s*[:\-]?\s*"
    r"(\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}[-/]\d{4})",
    re.I,
)

# Label on one line, date on the next (FacultyLink test / university forms).
_DEFENSE_DATE_LABEL = re.compile(r"^defense\s+date\s*:?\s*$", re.I)

_MONTH_DATE = re.compile(
    r"(?:date\s+(?:of\s+)?(?:approval|completion|defense)|approval\s+date|defense\s+date|"
    r"date\s+approved|approved\s+on)\s*[:\-]?\s*"
    r"((?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|"
    r"Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\.?\s+\d{1,2},?\s+\d{4})",
    re.I,
)

_ISO_DATE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")

_MONTHS = {
    "jan": 1,
    "january": 1,
    "feb": 2,
    "february": 2,
    "mar": 3,
    "march": 3,
    "apr": 4,
    "april": 4,
    "may": 5,
    "jun": 6,
    "june": 6,
    "jul": 7,
    "july": 7,
    "aug": 8,
    "august": 8,
    "sep": 9,
    "sept": 9,
    "september": 9,
    "oct": 10,
    "october": 10,
    "nov": 11,
    "november": 11,
    "dec": 12,
    "december": 12,
}

_ROLE_LABEL_HINT = re.compile(
    r"\b(adviser|advisor|panel\s*member|panelist|committee\s*member|"
    r"department\s+chair|dean|professor|ph\.?\s*d\.?|dr\.?)\b",
    re.I,
)


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _norm_date(raw: str) -> str | None:
    text = (raw or "").strip()
    if not text:
        return None
    if _ISO_DATE.match(text):
        return text
    m = re.match(r"^(\d{1,2})[-/](\d{1,2})[-/](\d{4})$", text)
    if m:
        d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if 1 <= mo <= 12 and 1 <= d <= 31:
            return f"{y:04d}-{mo:02d}-{d:02d}"
    m = re.match(r"^(\d{4})[-/](\d{1,2})[-/](\d{1,2})$", text)
    if m:
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if 1 <= mo <= 12 and 1 <= d <= 31:
            return f"{y:04d}-{mo:02d}-{d:02d}"
    m = re.match(
        r"^([A-Za-z]+)\.?\s+(\d{1,2}),?\s+(\d{4})$",
        text.replace(",", " ").strip(),
    )
    if m:
        mo = _MONTHS.get(m.group(1).lower())
        if mo:
            d, y = int(m.group(2)), int(m.group(3))
            if 1 <= d <= 31:
                return f"{y:04d}-{mo:02d}-{d:02d}"
    return None


def _looks_like_label_line(line: str) -> bool:
    return bool(re.match(r"^[A-Za-z][A-Za-z0-9\s/()]{0,48}:\s*\S", line))


def _field_label_match(stripped: str, pattern: re.Pattern) -> re.Match | None:
    m = pattern.search(stripped)
    if not m:
        return None
    if re.search(r"title\s+of\s+(?:the\s+)?(?:thesis|dissertation|study|research|project|capstone)", stripped, re.I):
        label = stripped[m.start() : m.end()].lower()
        if label in ("students", "student", "student(s)") or label.endswith("students"):
            return None
    if m.start() <= 2:
        return m
    if re.match(r"^(prepared\s+by|submitted\s+by|authors?)\b", stripped, re.I):
        return m
    if "name" in stripped[m.start() : m.end()].lower():
        return m
    return None


def _line_after_label(lines: list[str], label_patterns: tuple[str, ...]) -> str | None:
    compiled = [re.compile(p, re.I) for p in label_patterns]
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        for pat in compiled:
            m = _field_label_match(stripped, pat)
            if not m:
                continue
            remainder = stripped[m.end() :].strip(" :-\t")
            if remainder and not is_unreliable_research_title(remainder):
                return remainder
            for j in range(i + 1, min(i + 5, len(lines))):
                nxt = lines[j].strip()
                if not nxt or len(nxt) <= 2 or _looks_like_label_line(nxt):
                    continue
                if is_unreliable_research_title(nxt):
                    continue
                if not re.search(r"^(university|college|department|faculty|office)\b", nxt, re.I):
                    return nxt
    return None


def _collect_block_after_label(lines: list[str], label_patterns: tuple[str, ...], *, max_lines: int = 6) -> str:
    compiled = [re.compile(p, re.I) for p in label_patterns]
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        for pat in compiled:
            m = _field_label_match(stripped, pat)
            if not m:
                continue
            parts: list[str] = []
            remainder = stripped[m.end() :].strip(" :-\t")
            if remainder:
                parts.append(remainder)
            for j in range(i + 1, min(i + max_lines, len(lines))):
                nxt = lines[j].strip()
                if not nxt:
                    continue
                if _looks_like_label_line(nxt) or _line_matches_any_label(nxt):
                    break
                parts.append(nxt)
            return " ".join(parts).strip()
    return ""


def _line_matches_any_label(line: str) -> bool:
    checks = _STUDENT_LABELS + _ADVISER_LABELS + _PANEL_LABELS + _GROUP_LABELS + _TITLE_LABELS
    for pat in checks:
        if re.search(pat, line, re.I):
            return True
    return bool(re.search(r"^(date|academic|school\s+year|title)\b", line, re.I))


def _clean_title(value: str | None) -> str | None:
    if not value:
        return None
    text = value.strip()
    if is_unreliable_research_title(text):
        return None
    return text


def _clean_students(value: str | None) -> str | None:
    if not value:
        return None
    text = re.sub(r"\s+", " ", value.strip())
    text = re.sub(r"^(?:names?|students?|researchers?)\s*[:\-]\s*", "", text, flags=re.I)
    if len(text) < 3:
        return None
    return text


def _split_person_names(raw: str | None) -> list[str]:
    if not raw:
        return []
    text = re.sub(r"\s+and\s+", ",", raw, flags=re.I)
    text = text.replace("&", ",")
    parts = re.split(r"[,;/\n|]+", text)
    names: list[str] = []
    for part in parts:
        name = re.sub(r"\s+", " ", (part or "").strip())
        name = re.sub(r"^(?:mr\.?|ms\.?|mrs\.?|dr\.?|prof\.?)\s+", "", name, flags=re.I)
        if len(name) < 2:
            continue
        if len(name) >= 4 and is_unreliable_research_title(name):
            continue
        if _ROLE_LABEL_HINT.search(name) and "," not in name:
            continue
        names.append(name)
    return names


def _normalize_name_key(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", name.lower())


def _filter_students_from_role_names(
    students: list[str],
    advisers: list[str],
    panel: list[str],
) -> tuple[list[str], list[str]]:
    excluded: list[str] = []
    role_keys = {_normalize_name_key(n) for n in advisers + panel if n}
    role_keys.update(_normalize_name_key(n) for n in advisers + panel for n in _split_person_names(n))
    kept: list[str] = []
    for student in students:
        key = _normalize_name_key(student)
        if not key:
            continue
        if key in role_keys:
            excluded.append(student)
            continue
        if any(key in rk or rk in key for rk in role_keys if len(rk) >= 6):
            excluded.append(student)
            continue
        kept.append(student)
    return kept, excluded


def _field_entry(
    value: str | None,
    *,
    confidence: str,
    status: str | None = None,
) -> dict[str, Any]:
    if value and value.strip():
        st = status or "extracted"
        return {"value": value.strip(), "confidence": confidence, "status": st}
    return {"value": "", "confidence": "none", "status": status or "missing"}


def parse_research_approval_ocr(text: str) -> dict[str, Any]:
    """Parse OCR plain text; never invent values — missing fields stay empty."""
    raw = (text or "").strip()
    lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
    joined = "\n".join(lines)

    title = _clean_title(_line_after_label(lines, _TITLE_LABELS))

    student_block = _collect_block_after_label(lines, _STUDENT_LABELS)
    students_raw = _clean_students(student_block)
    student_labeled = bool(students_raw)
    if not students_raw:
        for pat in (
            r"(?:Student\s*\(?s?\)?|Researchers?|Proponents?|Prepared\s+by|Submitted\s+by)\s*[:\-]\s*(.+)",
        ):
            m = re.search(pat, joined, re.I)
            if m:
                students_raw = _clean_students(m.group(1))
                if students_raw:
                    break

    adviser_block = _collect_block_after_label(lines, _ADVISER_LABELS)
    panel_block = _collect_block_after_label(lines, _PANEL_LABELS)
    advisers = _split_person_names(adviser_block)
    panel_members = _split_person_names(panel_block)

    student_list = _split_person_names(students_raw or "")
    student_list, excluded = _filter_students_from_role_names(student_list, advisers, panel_members)

    students_display = ", ".join(student_list) if student_list else (students_raw or "")

    group = _line_after_label(lines, _GROUP_LABELS) or _collect_block_after_label(lines, _GROUP_LABELS, max_lines=2)
    if group and is_unreliable_research_title(group):
        group = None
    group = (group or "").strip() or None

    academic_year = None
    ay_m = _AY_PATTERN.search(joined)
    if ay_m:
        academic_year = normalize_academic_year(ay_m.group(1))

    completion = None
    date_m = _DATE_PATTERN.search(joined)
    if date_m:
        completion = _norm_date(date_m.group(1))
    if not completion:
        month_m = _MONTH_DATE.search(joined)
        if month_m:
            completion = _norm_date(month_m.group(1))
    if not completion:
        for i, line in enumerate(lines):
            if not _DEFENSE_DATE_LABEL.match(line.strip()):
                continue
            for j in range(i + 1, min(i + 4, len(lines))):
                nxt = lines[j].strip()
                if not nxt or _looks_like_label_line(nxt):
                    continue
                completion = _norm_date(nxt)
                if completion:
                    break
            if completion:
                break

    if student_list:
        if student_labeled:
            student_conf = "high"
            student_status = "extracted"
        else:
            student_conf = "medium"
            student_status = "needs_review"
    elif students_raw:
        student_conf = "low"
        student_status = "needs_review"
        students_display = students_raw
    else:
        student_conf = "none"
        student_status = "missing"
        students_display = ""

    if excluded:
        student_conf = "medium" if student_conf == "high" else student_conf
        student_status = "needs_review"

    def conf_for(value: str | None, *, labeled: bool) -> str:
        if not value:
            return "none"
        return "high" if labeled else "medium"

    fields = {
        "projectTitle": _field_entry(title, confidence=conf_for(title, labeled=True)),
        "studentNames": _field_entry(
            students_display or None,
            confidence=student_conf,
            status=student_status,
        ),
        "studentGroupLabel": _field_entry(group, confidence="high" if group else "none"),
        "academicYear": _field_entry(academic_year, confidence="high" if academic_year else "none"),
        "completionDate": _field_entry(
            completion,
            confidence="high" if completion else "none",
        ),
    }
    return {
        "version": OCR_EXTRACTION_VERSION,
        "documentType": "research_approval_sheet",
        "parsedAt": _utcnow_iso(),
        "fields": fields,
        "structured": {
            "students": student_list,
            "advisers": advisers,
            "panelMembers": panel_members,
            "excludedFromStudents": excluded,
        },
        "advisoryOnly": True,
    }


def _scrub_unreliable_bundle_titles(bundle: dict[str, Any]) -> dict[str, Any]:
    confirmed = bundle.get("metadataConfirmed")
    if isinstance(confirmed, dict) and confirmed.get("projectTitle") is True:
        return bundle
    if is_unreliable_research_title((bundle.get("projectTitle") or "").strip()):
        bundle["projectTitle"] = ""
    return bundle


def _merge_extraction_into_bundle(bundle: dict[str, Any], extraction: dict[str, Any]) -> dict[str, Any]:
    bundle = _scrub_unreliable_bundle_titles(bundle)
    confirmed = bundle.get("metadataConfirmed")
    if not isinstance(confirmed, dict):
        confirmed = {}
    fields = extraction.get("fields") if isinstance(extraction.get("fields"), dict) else {}
    for key in _FIELD_KEYS:
        if confirmed.get(key) is True:
            continue
        entry = fields.get(key)
        if not isinstance(entry, dict):
            continue
        value = (entry.get("value") or "").strip()
        if not value:
            continue
        if key == "projectTitle" and is_unreliable_research_title(value):
            continue
        if key == "studentGroupLabel":
            pass
        current = (bundle.get(key) or "").strip()
        if not current or (key == "projectTitle" and is_unreliable_research_title(current)):
            bundle[key] = value
    bundle["metadataConfirmed"] = confirmed
    return bundle


def _bundle_missing_extraction_values(bundle: dict[str, Any], extraction: dict[str, Any]) -> bool:
    fields = extraction.get("fields") if isinstance(extraction.get("fields"), dict) else {}
    for key in _FIELD_KEYS:
        if (bundle.get(key) or "").strip():
            continue
        entry = fields.get(key)
        if isinstance(entry, dict) and (entry.get("value") or "").strip():
            return True
    return False


def ensure_research_ocr_extraction(doc: Any) -> dict[str, Any] | None:
    """
    Re-parse stored ``Document.extracted_text`` when structured OCR metadata is missing
    or outdated (existing records without re-upload).
    """
    bundle = bundle_from_document(doc)
    if not bundle:
        return None
    if (bundle.get("serviceCategory") or "").strip().lower() != "research":
        return None
    text = (getattr(doc, "extracted_text", None) or "").strip()
    if not text:
        info = dict(getattr(doc, "extracted_info", None) or {})
        existing = info.get(OCR_EXTRACTION_KEY)
        return existing if isinstance(existing, dict) else None

    info = dict(getattr(doc, "extracted_info", None) or {})
    existing = info.get(OCR_EXTRACTION_KEY) if isinstance(info.get(OCR_EXTRACTION_KEY), dict) else None
    ocr_status = (getattr(doc, "ocr_status", None) or "").strip().lower()
    ex_students = ""
    if isinstance(existing, dict):
        fields = existing.get("fields") if isinstance(existing.get("fields"), dict) else {}
        sn = fields.get("studentNames") if isinstance(fields.get("studentNames"), dict) else {}
        ex_students = (sn.get("value") or "").strip()
    needs = (
        not isinstance(existing, dict)
        or existing.get("version") != OCR_EXTRACTION_VERSION
        or (ocr_status in ("completed", "complete") and not ex_students)
    )
    if not needs and isinstance(existing, dict):
        if _bundle_missing_extraction_values(bundle, existing):
            bundle = _merge_extraction_into_bundle(bundle, existing)
            persist_bundle(doc, bundle)
        return existing

    extraction = parse_research_approval_ocr(text)
    bundle = _merge_extraction_into_bundle(bundle, extraction)
    info[OCR_EXTRACTION_KEY] = extraction
    doc.extracted_info = info
    persist_bundle(doc, bundle)
    return extraction


def link_primary_document_as_approval_sheet(doc: Any, bundle: dict[str, Any]) -> dict[str, Any]:
    """Research primary upload is the signed approval sheet."""
    if (bundle.get("serviceCategory") or "").strip().lower() != "research":
        return bundle
    checklist = bundle.setdefault("checklist", {})
    entry = checklist.get(SLOT_APPROVAL_SHEET)
    if not isinstance(entry, dict):
        entry = empty_checklist_entry()
    entry["documentId"] = getattr(doc, "public_id", None)
    entry["fileHash"] = getattr(doc, "file_hash", None)
    if entry.get("status") == "missing":
        entry["status"] = SLOT_STATUS_PRESENT_UNVERIFIED
    entry["ocrHintOnly"] = True
    checklist[SLOT_APPROVAL_SHEET] = entry
    ids = list(bundle.get("supportingDocumentIds") or [])
    pid = getattr(doc, "public_id", None)
    if pid and pid not in ids:
        ids.append(pid)
    bundle["supportingDocumentIds"] = ids
    return bundle


def apply_criterion_c_research_ocr(doc: Any, *, text: str) -> None:
    """After OCR success on a Criterion C primary research document."""
    if (getattr(doc, "criterion_id", None) or "").strip() != CRITERION_C_ID:
        return
    bundle = bundle_from_document(doc)
    if not bundle:
        return
    if (bundle.get("serviceCategory") or "").strip().lower() != "research":
        return

    extraction = parse_research_approval_ocr(text)
    bundle = _merge_extraction_into_bundle(bundle, extraction)
    persist_bundle(doc, bundle)
    info = dict(getattr(doc, "extracted_info", None) or {})
    info[OCR_EXTRACTION_KEY] = extraction
    doc.extracted_info = info


def preserve_criterion_c_bundle_fields(before_info: dict[str, Any], after_info: dict[str, Any]) -> dict[str, Any]:
    """Keep faculty- or reviewer-confirmed bundle metadata across OCR merges."""
    before_bundle = before_info.get(BUNDLE_EXTRACTED_KEY)
    after_bundle = after_info.get(BUNDLE_EXTRACTED_KEY)
    if not isinstance(before_bundle, dict) or not isinstance(after_bundle, dict):
        return after_info
    confirmed = before_bundle.get("metadataConfirmed")
    if not isinstance(confirmed, dict):
        return after_info
    merged = dict(after_bundle)
    merged["metadataConfirmed"] = dict(confirmed)
    for key in _FIELD_KEYS:
        if confirmed.get(key) is True and (before_bundle.get(key) or "").strip():
            merged[key] = before_bundle[key]
    after_info = dict(after_info)
    after_info[BUNDLE_EXTRACTED_KEY] = merged
    if OCR_EXTRACTION_KEY in before_info and OCR_EXTRACTION_KEY not in after_info:
        after_info[OCR_EXTRACTION_KEY] = before_info[OCR_EXTRACTION_KEY]
    return after_info


def snapshot_criterion_c_bundle(info: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(info, dict):
        return None
    raw = info.get(BUNDLE_EXTRACTED_KEY)
    return dict(raw) if isinstance(raw, dict) else None
