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

EXTRACTION_COMPLETE = "complete"
EXTRACTION_PARTIAL = "partial"
EXTRACTION_AMBIGUOUS = "ambiguous"

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

_SECTION_HEADER_RE = re.compile(
    r"(?m)^(?:"
    r"(?:student|supervisor)\s+evaluation\s+of\s+(?:teachers?|faculty|teaching)"
    r"|(?:SET|SEF)\s+(?:summary|rating|report|evaluation)"
    r")\s*$",
    re.IGNORECASE,
)

_PAGE_MARKER_RE = re.compile(
    r"(?:\[(?:Page|PAGE)\s*(\d+)\]|^---+\s*Page\s+(\d+)\s*---+$)",
    re.MULTILINE,
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


@dataclass
class SetSefEvaluationRecord:
    """One SET or SEF semester evaluation detected within a document."""

    evaluation_type: str | None = None  # "SET" | "SEF"
    academic_year: str | None = None
    semester: str | None = None
    overall_rating: str | None = None
    rating_scale: str | None = None
    extraction_status: str = EXTRACTION_PARTIAL
    source_section_ref: str | None = None
    faculty_name: str | None = None
    document_title: str | None = None
    missing_fields: list[str] = field(default_factory=list)
    ambiguous_fields: list[str] = field(default_factory=list)
    uncertainty_notes: list[str] = field(default_factory=list)


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
    title_match = _TITLE_LINE_RE.search(text)
    if title_match:
        line = title_match.group(0).strip()
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


def _line_number_at(text: str, index: int) -> int:
    return text[:index].count("\n") + 1


def _page_hint_at(text: str, index: int) -> str | None:
    """Nearest page marker at or before index in extracted text."""
    prefix = text[:index]
    last_page: str | None = None
    for match in _PAGE_MARKER_RE.finditer(text):
        if match.start() > index:
            break
        page = match.group(1) or match.group(2)
        if page:
            last_page = page
    if last_page:
        return f"page:{last_page}"
    page_breaks = prefix.count("\f")
    if page_breaks:
        return f"page:{page_breaks + 1}"
    return None


def _extract_faculty_name(block: str) -> str | None:
    name_match = _FACULTY_NAME_RE.search(block)
    if not name_match:
        return None
    name = re.sub(r"\s+", " ", name_match.group(1)).strip(" .,")
    return name if len(name) >= 3 else None


def _extract_year(block: str) -> str | None:
    year_match = _YEAR_RE.search(block) or _YEAR_FALLBACK.search(block)
    if not year_match:
        return None
    return _normalize_year(year_match.group(1), year_match.group(2))


def _extract_semester_after(block: str, after_index: int = 0) -> str | None:
    sem_match = _SEMESTER_RE.search(block, pos=after_index)
    if not sem_match:
        return None
    return _normalize_semester(sem_match.group(0))


def _extract_rating_after(block: str, after_index: int = 0) -> tuple[str | None, str | None]:
    sub = block[after_index:]
    rating_match = _RATING_FRACTION_RE.search(sub)
    if rating_match:
        num, denom = rating_match.group(1), rating_match.group(2)
        return f"{num} / {denom}", denom
    pct = _RATING_PERCENT_RE.search(sub)
    if pct:
        return f"{pct.group(1)}%", "100"
    return None, None


def _record_extraction_status(record: SetSefEvaluationRecord) -> str:
    if record.ambiguous_fields:
        return EXTRACTION_AMBIGUOUS
    required = ("evaluation type", "academic year", "semester", "overall rating")
    missing = set(record.missing_fields)
    if any(f in missing for f in required):
        return EXTRACTION_PARTIAL
    if record.evaluation_type in ("SET", "SEF") and record.academic_year and record.semester and record.overall_rating:
        return EXTRACTION_COMPLETE
    return EXTRACTION_PARTIAL


def _parse_block_to_record(block: str, *, section_ref: str, doc_faculty: str | None) -> SetSefEvaluationRecord:
    block = block.strip()
    lower = block.lower()
    kind = _detect_kind(lower)
    record = SetSefEvaluationRecord(source_section_ref=section_ref)
    record.evaluation_type = kind
    record.document_title = _extract_title(block, kind)
    record.faculty_name = _extract_faculty_name(block) or doc_faculty

    year_match = _YEAR_RE.search(block) or _YEAR_FALLBACK.search(block)
    year_pos = year_match.start() if year_match else 0
    if year_match:
        record.academic_year = _normalize_year(year_match.group(1), year_match.group(2))
    else:
        record.missing_fields.append("academic year")

    sem_match = _SEMESTER_RE.search(block, pos=year_pos)
    sem_pos = sem_match.start() if sem_match else year_pos
    if sem_match:
        record.semester = _normalize_semester(sem_match.group(0))
    else:
        record.missing_fields.append("semester")

    rating_start = sem_match.end() if sem_match else year_pos
    rating, scale = _extract_rating_after(block, rating_start)
    if rating:
        record.overall_rating = rating
        record.rating_scale = scale
    else:
        record.missing_fields.append("overall rating")

    if not kind:
        record.missing_fields.append("evaluation type")
        record.ambiguous_fields.append("evaluation type")

    rating_values: set[str] = set()
    for match in _RATING_FRACTION_RE.finditer(block):
        rating_values.add(f"{match.group(1)}/{match.group(2)}")
    for match in _RATING_PERCENT_RE.finditer(block):
        rating_values.add(f"{match.group(1)}%")
    if len(rating_values) > 1:
        record.ambiguous_fields.append("overall rating")
        record.uncertainty_notes.append("Multiple distinct ratings in section; using first after semester.")

    year_values: set[str] = set()
    for match in _YEAR_RE.finditer(block):
        year_values.add(_normalize_year(match.group(1), match.group(2)))
    for match in _YEAR_FALLBACK.finditer(block):
        year_values.add(_normalize_year(match.group(1), match.group(2)))
    if len(year_values) > 1:
        record.ambiguous_fields.append("academic year")
        record.uncertainty_notes.append("Multiple academic years in section; using first in block.")

    page_hint = _page_hint_at(block, 0)
    if page_hint:
        record.source_section_ref = f"{section_ref};{page_hint}"

    record.extraction_status = _record_extraction_status(record)
    return record


def _split_into_blocks(raw: str) -> list[tuple[str, str]]:
    text = (raw or "").replace("\r\n", "\n").strip()
    if not text:
        return []

    headers = list(_SECTION_HEADER_RE.finditer(text))
    if len(headers) >= 2:
        blocks: list[tuple[str, str]] = []
        for i, match in enumerate(headers):
            start = match.start()
            end = headers[i + 1].start() if i + 1 < len(headers) else len(text)
            line_no = _line_number_at(text, start)
            ref = f"section:{i + 1}:line{line_no}"
            blocks.append((ref, text[start:end].strip()))
        return blocks

    if len(headers) == 1:
        return [(f"section:1:line{_line_number_at(text, headers[0].start())}", text)]

    year_spans: list[tuple[int, int]] = []
    seen_anchors: list[tuple[int, str]] = []
    for match in _YEAR_RE.finditer(text):
        norm = _normalize_year(match.group(1), match.group(2))
        seen_anchors.append((match.start(), norm))
    for match in _YEAR_FALLBACK.finditer(text):
        norm = _normalize_year(match.group(1), match.group(2))
        if any(abs(match.start() - pos) < 16 and norm == existing for pos, existing in seen_anchors):
            continue
        seen_anchors.append((match.start(), norm))
    seen_anchors.sort(key=lambda t: t[0])
    collapsed: list[tuple[int, str]] = []
    for pos, norm in seen_anchors:
        if collapsed and norm == collapsed[-1][1] and pos - collapsed[-1][0] < 80:
            continue
        collapsed.append((pos, norm))
    year_spans = [(pos, pos) for pos, _ in collapsed]

    if len(year_spans) >= 2:
        blocks = []
        for i, (ystart, _) in enumerate(year_spans):
            if i == 0:
                chunk_start = text.rfind("\n\n", 0, ystart)
                if chunk_start == -1:
                    chunk_start = max(0, ystart - 400)
            else:
                chunk_start = ystart
            next_start = year_spans[i + 1][0] if i + 1 < len(year_spans) else len(text)
            chunk = text[chunk_start:next_start].strip()
            line_no = _line_number_at(text, ystart)
            blocks.append((f"period:{i + 1}:line{line_no}", chunk))
        return blocks

    return [("section:1", text)]


def parse_set_sef_metadata_multi(text: str) -> list[SetSefEvaluationRecord]:
    """
    Detect zero or more SET/SEF evaluation records in document text.

    Does not assume a fixed semester count. Does not invent missing fields.
    """
    raw = (text or "").strip()
    if not raw:
        return []

    doc_faculty = _extract_faculty_name(raw)
    blocks = _split_into_blocks(raw)
    records: list[SetSefEvaluationRecord] = []
    for section_ref, block in blocks:
        if not block.strip():
            continue
        record = _parse_block_to_record(block, section_ref=section_ref, doc_faculty=doc_faculty)
        records.append(record)

    if not records and raw:
        records.append(
            _parse_block_to_record(raw, section_ref="section:1", doc_faculty=doc_faculty)
        )

    return records


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


def verify_record_indicator(selected_indicator_id: str | None, record: SetSefEvaluationRecord) -> str:
    if not selected_indicator_id or selected_indicator_id not in SET_SEF_INDICATOR_IDS:
        return _VERIFICATION_UNDETERMINED
    kind = record.evaluation_type
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
