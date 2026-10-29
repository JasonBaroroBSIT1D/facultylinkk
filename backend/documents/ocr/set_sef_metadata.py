"""Parse SET/SEF evaluation metadata from extracted document text."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone

SET_INDICATOR_IDS = frozenset({"kra1-a-student"})
SEF_INDICATOR_IDS = frozenset({"kra1-a-supervisor"})
SET_SEF_INDICATOR_IDS = SET_INDICATOR_IDS | SEF_INDICATOR_IDS

_VERIFICATION_MATCH = "MATCH"
_VERIFICATION_MISMATCH = "POSSIBLE_MISMATCH"
_VERIFICATION_UNDETERMINED = "UNDETERMINED"
_VERIFICATION_FAILED = "PROCESSING_FAILED"

_SET_PHRASES = (
    "student evaluation of teachers",
    "student evaluation of teaching",
    "student evaluation of teacher",
    "student's evaluation",
    "fedaf set",
    " set ",
    "set rating",
    "set summary",
)
_SEF_PHRASES = (
    "supervisor evaluation of teaching",
    "supervisor evaluation of faculty",
    "supervisor's evaluation of faculty",
    "supervisor's evaluation",
    "supervisors evaluation",
    " sef ",
    "sef rating",
    "sef summary",
)

_YEAR_RE = re.compile(
    r"(?:academic\s+year|school\s+year|a\.?\s*y\.?|sy)\s*[:\s]*"
    r"(\d{4})\s*[-–—/]\s*(\d{2,4})",
    re.IGNORECASE,
)
_YEAR_FALLBACK = re.compile(r"\b(20\d{2})\s*[-–—/]\s*(20\d{2}|\d{2})\b")

_SEMESTER_RE = re.compile(
    r"(?:(?:first|1st)\s*semester|(?:second|2nd)\s*semester|"
    r"semester\s*[:\s]*(?:1|2|first|second|1st|2nd)|"
    r"(?:first|second)\s*sem(?:ester)?\.?)",
    re.IGNORECASE,
)

_RATING_FRACTION_RE = re.compile(
    r"(?:overall\s+(?:evaluation\s+)?(?:rating|score)|"
    r"overall\s+rating|final\s+rating|rating\s+summary)"
    r"\s*[:\s]*"
    r"(\d{1,3}(?:\.\d+)?)\s*(?:/|\s+out\s+of\s+)\s*(\d{1,3}(?:\.\d+)?)",
    re.IGNORECASE,
)
_RATING_PERCENT_RE = re.compile(
    r"(?:overall\s+(?:evaluation\s+)?(?:rating|score))\s*[:\s]*"
    r"(\d{1,3}(?:\.\d+)?)\s*%",
    re.IGNORECASE,
)

_FACULTY_NAME_RE = re.compile(
    r"(?:faculty(?:\s+name)?|name\s+of\s+faculty|ratee|teacher(?:\s+name)?|"
    r"faculty\s+member)\s*[:\s]+"
    r"([A-Za-z][A-Za-z\s.'\-]{2,80}?)(?:\s*(?:\n|$|academic|semester|overall|department|college))",
    re.IGNORECASE,
)

_TITLE_LINE_RE = re.compile(
    r"^(?:student|supervisor)\s+evaluation\s+of\s+(?:teachers?|faculty|teaching)\s*$",
    re.IGNORECASE | re.MULTILINE,
)


@dataclass
class SetSefExtraction:
    document_title: str | None = None
    faculty_name: str | None = None
    academic_year: str | None = None
    semester: str | None = None
    evaluation_type: str | None = None
    overall_rating: str | None = None
    rating_scale: str | None = None
    detected_kind: str | None = None  # "SET" | "SEF" | None
    verification_status: str = _VERIFICATION_UNDETERMINED
    missing_fields: list[str] = field(default_factory=list)
    ambiguous_fields: list[str] = field(default_factory=list)


def _normalize_year(start: str, end: str) -> str:
    end = end.strip()
    if len(end) == 2 and start.isdigit():
        prefix = start[:2] if len(start) >= 2 else "20"
        end = prefix + end
    return f"{start}-{end}"


def _normalize_semester(raw: str) -> str:
    lower = raw.lower()
    if "1" in lower or "first" in lower or "1st" in lower:
        return "1st Semester"
    if "2" in lower or "second" in lower or "2nd" in lower:
        return "2nd Semester"
    return raw.strip()


def _detect_kind(text_lower: str) -> str | None:
    set_hits = sum(1 for p in _SET_PHRASES if p in text_lower)
    sef_hits = sum(1 for p in _SEF_PHRASES if p in text_lower)
    if set_hits and not sef_hits:
        return "SET"
    if sef_hits and not set_hits:
        return "SEF"
    if set_hits and sef_hits:
        return None
    if "student evaluation" in text_lower:
        return "SET"
    if "supervisor evaluation" in text_lower:
        return "SEF"
    return None


def _evaluation_type_label(kind: str | None, text: str) -> str | None:
    if kind == "SET":
        return "Student Evaluation of Teaching"
    if kind == "SEF":
        return "Supervisor Evaluation of Teaching"
    if _TITLE_LINE_RE.search(text):
        line = _TITLE_LINE_RE.search(text).group(0).strip()
        return line[0].upper() + line[1:]
    return None


def _extract_title(text: str, kind: str | None) -> str | None:
    match = _TITLE_LINE_RE.search(text)
    if match:
        return match.group(0).strip()
    if kind == "SET":
        return "Student Evaluation of Teaching"
    if kind == "SEF":
        return "Supervisor Evaluation of Teaching"
    first = next((ln.strip() for ln in text.splitlines() if ln.strip()), None)
    if first and len(first) <= 120:
        return first
    return None


def parse_set_sef_metadata(text: str) -> SetSefExtraction:
    raw = (text or "").strip()
    out = SetSefExtraction()
    if not raw:
        out.missing_fields = [
            "document title",
            "faculty name",
            "academic year",
            "semester",
            "evaluation type",
            "overall rating",
        ]
        out.verification_status = _VERIFICATION_UNDETERMINED
        return out

    lower = raw.lower()
    out.detected_kind = _detect_kind(lower)
    out.evaluation_type = _evaluation_type_label(out.detected_kind, raw)
    out.document_title = _extract_title(raw, out.detected_kind)

    year_match = _YEAR_RE.search(raw) or _YEAR_FALLBACK.search(raw)
    if year_match:
        out.academic_year = _normalize_year(year_match.group(1), year_match.group(2))
    else:
        out.missing_fields.append("academic year")

    sem_match = _SEMESTER_RE.search(raw)
    if sem_match:
        out.semester = _normalize_semester(sem_match.group(0))
    else:
        out.missing_fields.append("semester")

    name_match = _FACULTY_NAME_RE.search(raw)
    if name_match:
        name = re.sub(r"\s+", " ", name_match.group(1)).strip(" .,")
        if len(name) >= 3:
            out.faculty_name = name
        else:
            out.missing_fields.append("faculty name")
    else:
        out.missing_fields.append("faculty name")

    rating_match = _RATING_FRACTION_RE.search(raw)
    if rating_match:
        num, denom = rating_match.group(1), rating_match.group(2)
        out.overall_rating = f"{num} / {denom}"
        out.rating_scale = denom
    else:
        pct = _RATING_PERCENT_RE.search(raw)
        if pct:
            out.overall_rating = f"{pct.group(1)}%"
            out.rating_scale = "100"
        else:
            out.missing_fields.append("overall rating")

    if not out.document_title:
        out.missing_fields.append("document title")
    if not out.evaluation_type:
        out.missing_fields.append("evaluation type")
        out.ambiguous_fields.append("evaluation type")

    return out


def verify_selected_indicator(selected_indicator_id: str | None, extraction: SetSefExtraction) -> str:
    if not selected_indicator_id or selected_indicator_id not in SET_SEF_INDICATOR_IDS:
        return _VERIFICATION_UNDETERMINED
    kind = extraction.detected_kind
    if not kind:
        return _VERIFICATION_UNDETERMINED
    if selected_indicator_id in SET_INDICATOR_IDS and kind == "SET":
        return _VERIFICATION_MATCH
    if selected_indicator_id in SEF_INDICATOR_IDS and kind == "SEF":
        return _VERIFICATION_MATCH
    return _VERIFICATION_MISMATCH


def is_set_sef_indicator(indicator_id: str | None) -> bool:
    return bool(indicator_id and indicator_id in SET_SEF_INDICATOR_IDS)


def apply_set_sef_to_extracted_info(
    info: dict,
    *,
    text: str,
    indicator_id: str | None,
    extraction_method: str | None,
) -> dict:
    """Merge SET/SEF parsing into document extracted_info (reviewer-facing keys)."""
    merged = dict(info or {})
    if not is_set_sef_indicator(indicator_id):
        return merged

    parsed = parse_set_sef_metadata(text)
    verification = verify_selected_indicator(indicator_id, parsed)

    if parsed.document_title:
        merged["Extracted title"] = parsed.document_title
    if parsed.faculty_name:
        merged["Faculty name"] = parsed.faculty_name
        merged["Extracted names"] = parsed.faculty_name
        merged["Identity field label"] = "Faculty name"
    if parsed.academic_year:
        merged["Academic year"] = parsed.academic_year
        merged["Extracted date"] = (
            f"{parsed.academic_year} · {parsed.semester}"
            if parsed.semester
            else parsed.academic_year
        )
    if parsed.semester:
        merged["Semester"] = parsed.semester
    if parsed.evaluation_type:
        merged["Evaluation type"] = parsed.evaluation_type
    if parsed.overall_rating:
        merged["Extracted rating"] = parsed.overall_rating
    if parsed.rating_scale:
        merged["Rating scale"] = parsed.rating_scale

    merged["Indicator verification status"] = verification
    merged["Detected evaluation kind"] = parsed.detected_kind or ""
    merged["Selected indicator ID"] = indicator_id or ""
    if parsed.missing_fields:
        merged["Missing extraction fields"] = ", ".join(sorted(set(parsed.missing_fields)))
    else:
        merged.pop("Missing extraction fields", None)
    if parsed.ambiguous_fields:
        merged["Ambiguous extraction fields"] = ", ".join(sorted(set(parsed.ambiguous_fields)))

    merged["SET/SEF extraction status"] = (
        "complete" if not parsed.missing_fields else "partial"
    )
    merged["Extraction processed at"] = datetime.now(timezone.utc).isoformat()
    if extraction_method:
        merged["Extraction method"] = extraction_method

    return merged


def mark_set_sef_processing_failed(info: dict, *, indicator_id: str | None, message: str) -> dict:
    merged = dict(info or {})
    if not is_set_sef_indicator(indicator_id):
        return merged
    merged["Indicator verification status"] = _VERIFICATION_FAILED
    merged["SET/SEF extraction status"] = "failed"
    merged["Missing extraction fields"] = merged.get("Missing extraction fields") or "all fields"
    merged["Extraction error"] = message
    merged["Extraction processed at"] = datetime.now(timezone.utc).isoformat()
    return merged
