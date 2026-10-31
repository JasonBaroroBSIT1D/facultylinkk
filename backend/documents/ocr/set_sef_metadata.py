"""Parse SET/SEF evaluation metadata from extracted document text."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone

from documents.criterion_a_upload import (
    classification_status_from_composition,
    is_auto_criterion_a_upload,
    should_run_set_sef_pipeline,
)

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
    "set rating summary",
    "set summary report",
)
_SEF_PHRASES = (
    "supervisor evaluation of teaching",
    "supervisor evaluation of faculty",
    "supervisor's evaluation of faculty",
    "supervisor's evaluation",
    "supervisors evaluation",
    "sef rating summary",
    "sef summary report",
)

_SET_HEADER_RE = re.compile(
    r"(?:student\s+evaluation\s+of\s+(?:teachers?|teaching)|"
    r"fedaf\s+set|set\s+rating\s+summary)",
    re.IGNORECASE,
)
_SEF_HEADER_RE = re.compile(
    r"(?:supervisor\s+evaluation\s+of\s+(?:faculty|teaching)|"
    r"sef\s+rating\s+summary)",
    re.IGNORECASE,
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
_RATING_LOOSE_FRACTION_RE = re.compile(
    r"(?<![\d.])(\d{1,3}(?:\.\d+)?)\s*(?:/|\s+out\s+of\s+)\s*(100|\d{2,3})(?!\d)",
    re.IGNORECASE,
)

# Explicit label patterns only (colon required). Do not match headings like "Faculty Rating".
_FACULTY_LABEL_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(
        r"Faculty\s*:\s*"
        r"([A-Za-z][A-Za-z\s.'\-]+?)"
        r"(?=\s*(?:\n|Department|Position|Designation|College|School|Academic|Semester|SY\b|AY\b|$))",
        re.IGNORECASE,
    ),
    re.compile(
        r"Faculty\s+Name\s*:\s*"
        r"([A-Za-z][A-Za-z\s.'\-]+?)"
        r"(?=\s*(?:\n|$|Department|Academic|Semester|SY\b|AY\b))",
        re.IGNORECASE,
    ),
    re.compile(
        r"Name\s+of\s+Faculty\s*:\s*"
        r"([A-Za-z][A-Za-z\s.'\-]+?)"
        r"(?=\s*(?:\n|$|Department|Academic|Semester))",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:Ratee|Teacher(?:\s+Name)?|Faculty\s+Member)\s*:\s*"
        r"([A-Za-z][A-Za-z\s.'\-]+?)"
        r"(?=\s*(?:\n|$|Academic|Semester|Overall|Department|College))",
        re.IGNORECASE,
    ),
    re.compile(
        r"Faculty\s+Subject\s*:\s*"
        r"([A-Za-z][A-Za-z\s.'\-,]+?)"
        r"(?=\s*(?:\n|$|Document|Department|Academic|Semester|Overall|ID\b))",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:^|\n)\s*Name\s*:\s*"
        r"([A-Za-z][A-Za-z\s.'\-,]+?)"
        r"(?=\s*(?:\n|$|Department|Document|Academic|Semester|Faculty|Overall|ID\b))",
        re.IGNORECASE | re.MULTILINE,
    ),
)

_FACULTY_NAME_REJECT_TOKENS = frozenset(
    {
        "rating",
        "ratings",
        "evaluation",
        "evaluations",
        "summary",
        "individual",
        "student",
        "students",
        "supervisor",
        "supervisors",
        "teaching",
        "report",
        "semester",
        "average",
        "overall",
        "department",
        "college",
        "school",
        "name",
        "faculty",
        "teacher",
        "teachers",
        "score",
        "scores",
        "combined",
        "mixed",
        "unknown",
        "n/a",
        "na",
    }
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

# Combined summary table: one row per semester with SET and SEF raw ratings in columns.
_TABLE_NUM_RE = re.compile(r"\b(\d{1,3}(?:\.\d+)?)\b")
_SEM_TABLE_ROW_PATTERNS = (
    re.compile(
        r"(?P<sem_word>1st|2nd|First|Second)\s+Sem\.?,?\s*"
        r"(?:SY|AY|School\s+Year|Academic\s+Year)\s+"
        r"(?P<y1>\d{4})\s*[-–—/]\s*(?P<y2>\d{2,4})",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:SY|AY|School\s+Year|Academic\s+Year)\s+"
        r"(?P<y1>\d{4})\s*[-–—/]\s*(?P<y2>\d{2,4})\s*,?\s*"
        r"(?P<sem_word>1st|2nd|First|Second)\s+Sem(?:ester)?\.?",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?P<sem_word>1st|2nd|First|Second)\s+Semester,?\s+"
        r"(?:Academic\s+Year|AY|SY)\s+"
        r"(?P<y1>\d{4})\s*[-–—/]\s*(?P<y2>\d{2,4})",
        re.IGNORECASE,
    ),
)
_SET_WEIGHT_SHARE = 0.6
_SEF_WEIGHT_SHARE = 0.4


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
    has_set_header = bool(_SET_HEADER_RE.search(text_lower))
    has_sef_header = bool(_SEF_HEADER_RE.search(text_lower))
    set_hits = sum(1 for p in _SET_PHRASES if p in text_lower)
    sef_hits = sum(1 for p in _SEF_PHRASES if p in text_lower)
    if has_set_header and not has_sef_header:
        return "SET"
    if has_sef_header and not has_set_header:
        return "SEF"
    if set_hits and not sef_hits and not has_sef_header:
        return "SET"
    if sef_hits and not set_hits and not has_set_header:
        return "SEF"
    if (set_hits or has_set_header) and (sef_hits or has_sef_header):
        return None
    if "student evaluation" in text_lower and "supervisor evaluation" not in text_lower:
        return "SET"
    if "supervisor evaluation" in text_lower and "student evaluation" not in text_lower:
        return "SEF"
    return None


def _page_from_section_ref(ref: str | None) -> str | None:
    if not ref:
        return None
    for part in ref.split(";"):
        part = part.strip()
        if part.startswith("page:"):
            return part
    return None


def _completeness(record: SetSefEvaluationRecord) -> int:
    score = 0
    if record.evaluation_type in ("SET", "SEF"):
        score += 1
    if record.academic_year:
        score += 2
    if record.semester:
        score += 2
    if record.overall_rating:
        score += 2
    return score


def _types_compatible(a: str | None, b: str | None) -> bool:
    if not a or not b:
        return True
    return a == b


def _recompute_missing_fields(record: SetSefEvaluationRecord) -> None:
    record.missing_fields = []
    if not record.academic_year:
        record.missing_fields.append("academic year")
    if not record.semester:
        record.missing_fields.append("semester")
    if not record.overall_rating:
        record.missing_fields.append("overall rating")
    if not record.evaluation_type:
        record.missing_fields.append("evaluation type")
        if "evaluation type" not in record.ambiguous_fields:
            record.ambiguous_fields.append("evaluation type")
    record.extraction_status = _record_extraction_status(record)


def _merge_record_pair(
    left: SetSefEvaluationRecord,
    right: SetSefEvaluationRecord,
) -> SetSefEvaluationRecord:
    base, other = (left, right) if _completeness(left) >= _completeness(right) else (right, left)
    merged = SetSefEvaluationRecord(
        evaluation_type=base.evaluation_type or other.evaluation_type,
        document_title=base.document_title or other.document_title,
        faculty_name=base.faculty_name or other.faculty_name,
        academic_year=base.academic_year or other.academic_year,
        semester=base.semester or other.semester,
        overall_rating=base.overall_rating or other.overall_rating,
        rating_scale=base.rating_scale or other.rating_scale,
        source_section_ref=base.source_section_ref or other.source_section_ref,
    )
    merged.ambiguous_fields = sorted(set(base.ambiguous_fields + other.ambiguous_fields))
    merged.uncertainty_notes = list(dict.fromkeys(base.uncertainty_notes + other.uncertainty_notes))
    if base.source_section_ref and other.source_section_ref and base.source_section_ref != other.source_section_ref:
        merged.uncertainty_notes.append(
            f"Merged OCR sections {base.source_section_ref} and {other.source_section_ref}."
        )
        merged.source_section_ref = base.source_section_ref
    _recompute_missing_fields(merged)
    return merged


def _should_merge_fragments(a: SetSefEvaluationRecord, b: SetSefEvaluationRecord) -> bool:
    if not _types_compatible(a.evaluation_type, b.evaluation_type):
        return False
    a_period = bool(a.academic_year and a.semester)
    b_period = bool(b.academic_year and b.semester)
    a_rating = bool(a.overall_rating)
    b_rating = bool(b.overall_rating)
    if a_period and b_period and a.academic_year == b.academic_year and a.semester == b.semester:
        return True
    if (a_period and b_rating and not b_period) or (b_period and a_rating and not a_period):
        page_a = _page_from_section_ref(a.source_section_ref)
        page_b = _page_from_section_ref(b.source_section_ref)
        if page_a and page_b and page_a != page_b:
            return False
        return True
    return False


def _is_orphan_rating_fragment(record: SetSefEvaluationRecord) -> bool:
    if record.academic_year and record.semester:
        return False
    if not record.overall_rating:
        return False
    lower = (record.document_title or "").lower()
    if _SET_HEADER_RE.search(lower) or _SEF_HEADER_RE.search(lower):
        return False
    if record.academic_year or record.semester:
        return False
    return True


def merge_fragment_records(records: list[SetSefEvaluationRecord]) -> list[SetSefEvaluationRecord]:
    """Combine complementary OCR fragments (period vs rating) into one evaluation row."""
    if len(records) <= 1:
        return [r for r in records if not _is_orphan_rating_fragment(r)]

    merged: list[SetSefEvaluationRecord] = list(records)
    changed = True
    while changed and len(merged) > 1:
        changed = False
        next_pass: list[SetSefEvaluationRecord] = []
        consumed: set[int] = set()
        for i, left in enumerate(merged):
            if i in consumed:
                continue
            current = left
            for j in range(i + 1, len(merged)):
                if j in consumed:
                    continue
                right = merged[j]
                if _should_merge_fragments(current, right):
                    current = _merge_record_pair(current, right)
                    consumed.add(j)
                    changed = True
            next_pass.append(current)
            consumed.add(i)
        merged = next_pass

    return [r for r in merged if not _is_orphan_rating_fragment(r)]


def classify_document_composition(records: list[SetSefEvaluationRecord]) -> str:
    set_count = sum(1 for r in records if r.evaluation_type == "SET")
    sef_count = sum(1 for r in records if r.evaluation_type == "SEF")
    unknown = sum(1 for r in records if not r.evaluation_type)
    if set_count and sef_count:
        return "Mixed SET and SEF"
    if set_count:
        return "SET only"
    if sef_count:
        return "SEF only"
    if unknown:
        return "Uncertain evaluation content"
    return "No evaluation sections detected"


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


def _clean_faculty_name_candidate(raw: str | None) -> str | None:
    if not raw:
        return None
    name = re.sub(r"\s+", " ", raw).strip(" .,")
    if len(name) < 3:
        return None
    lower = name.lower()
    if lower in _FACULTY_NAME_REJECT_TOKENS:
        return None
    words = lower.split()
    if not words or all(w in _FACULTY_NAME_REJECT_TOKENS for w in words):
        return None
    if "rating" in lower and "faculty" not in lower:
        return None
    if re.search(r"\b(?:summary|individual|evaluation)\b", lower):
        return None
    return name


def _extract_faculty_name(block: str) -> str | None:
    for pattern in _FACULTY_LABEL_PATTERNS:
        match = pattern.search(block)
        if not match:
            continue
        cleaned = _clean_faculty_name_candidate(match.group(1))
        if cleaned:
            return cleaned
    return None


def _faculty_name_from_records(records: list[SetSefEvaluationRecord]) -> str | None:
    names = [_clean_faculty_name_candidate(r.faculty_name) for r in records]
    names = [n for n in names if n]
    if not names:
        return None
    unique = sorted(set(names))
    if len(unique) == 1:
        return unique[0]
    return None


def _collect_faculty_name_candidates(
    raw: str,
    records: list[SetSefEvaluationRecord],
) -> list[str]:
    candidates: list[str] = []
    from_records = [_clean_faculty_name_candidate(r.faculty_name) for r in records]
    candidates.extend(n for n in from_records if n)
    table = _extract_table_document_faculty(raw)
    if table:
        candidates.append(table)
    block_name = _extract_faculty_name(raw)
    if block_name:
        candidates.append(block_name)
    return sorted({c for c in candidates if c})


def _resolve_document_faculty_name(
    raw: str,
    records: list[SetSefEvaluationRecord],
) -> str | None:
    from_records = _faculty_name_from_records(records)
    if from_records:
        return from_records
    table = _extract_table_document_faculty(raw)
    if table:
        return table
    return _extract_faculty_name(raw)


def _composition_display(composition: str) -> str:
    mapping = {
        "SET only": "SET Only",
        "SEF only": "SEF Only",
        "Mixed SET and SEF": "Mixed SET and SEF",
        "Uncertain evaluation content": "Needs Classification",
        "No evaluation sections detected": "Needs Classification",
    }
    return mapping.get(composition, composition or "Needs Classification")


def _apply_multi_semester_summary_fields(
    merged: dict,
    records: list[SetSefEvaluationRecord],
    *,
    composition: str,
) -> None:
    years = sorted({r.academic_year for r in records if r.academic_year})
    semesters = sorted(
        {r.semester for r in records if r.semester},
        key=lambda s: (0 if s.lower().startswith("1") else 1, s),
    )
    set_count = sum(1 for r in records if r.evaluation_type == "SET")
    sef_count = sum(1 for r in records if r.evaluation_type == "SEF")
    merged["Multi-semester document"] = "yes"
    merged["Academic years covered"] = ", ".join(years) if years else ""
    merged["Semesters detected"] = "; ".join(semesters) if semesters else ""
    merged["SET record count"] = str(set_count)
    merged["SEF record count"] = str(sef_count)
    merged["Document type"] = _composition_display(composition)
    merged.pop("Semester", None)
    merged.pop("Extracted rating", None)
    merged.pop("Rating scale", None)
    merged["Document-level rating note"] = (
        "This PDF contains multiple semester evaluations. "
        "Overall ratings appear on each SET/SEF record below."
    )


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
    if not rating:
        rating, scale = _extract_rating_after(block, 0)
    if not rating and record.academic_year and record.semester:
        loose = _RATING_LOOSE_FRACTION_RE.findall(block)
        if len(loose) == 1:
            num, denom = loose[0]
            rating, scale = f"{num} / {denom}", denom
        elif len(loose) > 1:
            record.ambiguous_fields.append("overall rating")
            record.uncertainty_notes.append(
                "Multiple numeric ratings in section; reviewer should confirm the overall rating."
            )
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


def _rating_display_from_float(value: float) -> tuple[str, str]:
    return f"{value:.2f} / 100", "100"


def _approx_weighted_component(raw: float, weighted: float, *, share: float) -> bool:
    expected = raw * share
    return abs(weighted - expected) <= max(0.35, expected * 0.02)


def _near(value: float, target: float) -> bool:
    return abs(value - target) <= max(0.35, abs(target) * 0.025)


def _semester_label_from_token(sem_word: str) -> str:
    token = (sem_word or "").strip().lower()
    if token.startswith("1") or token.startswith("first"):
        return "1st Semester"
    if token.startswith("2") or token.startswith("second"):
        return "2nd Semester"
    return _normalize_semester(sem_word)


def _iter_semester_table_row_anchors(text: str) -> list[re.Match[str]]:
    hits: list[tuple[int, re.Match[str]]] = []
    for pattern in _SEM_TABLE_ROW_PATTERNS:
        for match in pattern.finditer(text):
            if "overall" in text[max(0, match.start() - 24) : match.start()].lower():
                continue
            hits.append((match.start(), match))
    hits.sort(key=lambda t: t[0])
    merged: list[re.Match[str]] = []
    last_start = -999
    for start, match in hits:
        if start - last_start < 8:
            continue
        merged.append(match)
        last_start = start
    return merged


def _combined_table_header_region(raw: str, first_row_start: int) -> str:
    return raw[: max(0, first_row_start)]


def _combined_table_header_hints(header: str) -> dict[str, bool | None]:
    lower = header.lower()
    set_rating = re.search(r"student[s]?\s*(?:\n|\s|/)*rating", lower)
    sef_rating = re.search(r"supervisor\s*(?:\n|\s|/)*rating", lower)
    set_weight = re.search(r"student[s]?\s*(?:\n|\s|/)*x\s*60", lower) or "60%" in lower
    sef_weight = re.search(r"supervisor\s*(?:\n|\s|/)*x\s*40", lower) or "40%" in lower
    set_before_sef = None
    if set_rating and sef_rating:
        set_before_sef = set_rating.start() < sef_rating.start()
    return {
        "has_set_column": bool(set_rating or set_weight or "student" in lower),
        "has_sef_column": bool(sef_rating or sef_weight or "supervisor" in lower),
        "set_before_sef": set_before_sef,
        "has_semester_average": bool(re.search(r"semester\s*average", lower)),
    }


def _looks_like_combined_set_sef_rating_table(raw: str) -> bool:
    lower = raw.lower()
    anchors = _iter_semester_table_row_anchors(raw)
    if not anchors:
        return False
    first = anchors[0].start()
    hints = _combined_table_header_hints(_combined_table_header_region(raw, first))
    if not hints["has_set_column"] or not hints["has_sef_column"]:
        return False
    if "student" not in lower or "supervisor" not in lower:
        return False
    strong = (
        hints["has_semester_average"]
        or hints["has_set_column"]
        and hints["has_sef_column"]
        and (
            re.search(r"students?\s*(?:\n|\s)*rating", lower)
            and re.search(r"supervisor\s*(?:\n|\s)*rating", lower)
        )
    )
    if len(anchors) >= 2:
        return strong
    return strong and hints["has_semester_average"]


def _first_index(numbers: list[float], value: float) -> int:
    for index, number in enumerate(numbers):
        if _near(number, value):
            return index
    return 999


def _identify_raw_set_sef_from_row_numbers(
    numbers: list[float],
    *,
    prefer_set_before_sef: bool | None,
) -> tuple[float, float] | None | str:
    """
    Identify raw SET and SEF ratings in a table row using 60/40 weighted fingerprints.

    Returns None if no reliable match, or \"ambiguous\" when multiple equally valid pairs exist.
    """
    candidates = [n for n in numbers if 0 <= n <= 100]
    if len(candidates) < 2:
        return None

    matches: list[tuple[float, float, int]] = []

    for set_raw in candidates:
        for sef_raw in candidates:
            if abs(set_raw - sef_raw) < 0.001 and candidates.count(set_raw) < 2:
                continue
            set_w = set_raw * _SET_WEIGHT_SHARE
            sef_w = sef_raw * _SEF_WEIGHT_SHARE
            sem_avg = set_raw * _SET_WEIGHT_SHARE + sef_raw * _SEF_WEIGHT_SHARE
            has_set_w = any(_near(n, set_w) for n in candidates)
            has_sef_w = any(_near(n, sef_w) for n in candidates)
            has_avg = any(_near(n, sem_avg) for n in candidates)
            score = int(has_set_w) + int(has_sef_w) + int(has_avg)
            if has_set_w and has_sef_w:
                matches.append((set_raw, sef_raw, score + 2))
                continue
            if len(candidates) == 3:
                expected_avg = set_raw * _SET_WEIGHT_SHARE + sef_raw * _SEF_WEIGHT_SHARE
                third_values = [n for n in candidates if not _near(n, set_raw) and not _near(n, sef_raw)]
                if third_values and _near(third_values[0], expected_avg):
                    matches.append((set_raw, sef_raw, score + 1))

    if not matches:
        return None
    best_score = max(m[2] for m in matches)
    best = [m for m in matches if m[2] == best_score]
    if len(best) > 1 and prefer_set_before_sef is not None:
        if prefer_set_before_sef:
            best = sorted(best, key=lambda m: (_first_index(numbers, m[0]), _first_index(numbers, m[1])))
        else:
            best = sorted(best, key=lambda m: (_first_index(numbers, m[1]), _first_index(numbers, m[0])))
        return best[0][0], best[0][1]
    if len(best) > 1:
        pairs = {(round(a, 2), round(b, 2)) for a, b, _ in best}
        if len(pairs) > 1:
            return "ambiguous"
    set_raw, sef_raw, _ = best[0]
    return set_raw, sef_raw


def _extract_table_document_faculty(raw: str) -> str | None:
    return _extract_faculty_name(raw)


def _infer_combined_table_title(raw: str) -> str:
    for line in raw.splitlines():
        cleaned = line.strip()
        if not cleaned or len(cleaned) > 120:
            continue
        lower = cleaned.lower()
        if "student" in lower and "supervisor" in lower:
            return cleaned
        if "summary" in lower and ("rating" in lower or "evaluation" in lower):
            return cleaned
    return "Combined semester SET/SEF summary"


def _parse_combined_semester_rating_table(raw: str) -> list[SetSefEvaluationRecord]:
    """
    Parse combined semester summary tables (any faculty, any semester count).

    Uses weighted 60/40 fingerprints to locate raw SET/SEF values regardless of column order.
    """
    if not _looks_like_combined_set_sef_rating_table(raw):
        return []

    anchors = _iter_semester_table_row_anchors(raw)
    if not anchors:
        return []

    first_row_start = anchors[0].start()
    header_hints = _combined_table_header_hints(_combined_table_header_region(raw, first_row_start))
    prefer_order = header_hints.get("set_before_sef")
    body = raw[first_row_start:]
    body_anchors = _iter_semester_table_row_anchors(body)

    doc_faculty = _extract_table_document_faculty(raw)
    title = _infer_combined_table_title(raw)
    records: list[SetSefEvaluationRecord] = []

    for i, match in enumerate(body_anchors):
        tail_end = body_anchors[i + 1].start() if i + 1 < len(body_anchors) else len(body)
        tail = body[match.end() : tail_end]
        tail = re.split(r"overall\s+average", tail, maxsplit=1, flags=re.IGNORECASE)[0]
        numbers = [float(n) for n in _TABLE_NUM_RE.findall(tail)]
        if not numbers or any(n > 100 for n in numbers):
            continue
        pair = _identify_raw_set_sef_from_row_numbers(
            numbers,
            prefer_set_before_sef=prefer_order if isinstance(prefer_order, bool) else None,
        )
        if pair == "ambiguous":
            sem_word = match.group("sem_word")
            semester = _semester_label_from_token(sem_word)
            academic_year = _normalize_year(match.group("y1"), match.group("y2"))
            line_no = _line_number_at(body, match.start())
            for kind in ("SET", "SEF"):
                record = SetSefEvaluationRecord(
                    evaluation_type=kind,
                    academic_year=academic_year,
                    semester=semester,
                    source_section_ref=f"table-row:{i + 1}:{kind}:line{line_no}",
                    faculty_name=doc_faculty,
                    document_title=title,
                )
                record.ambiguous_fields.append("overall rating")
                record.uncertainty_notes.append(
                    "Could not reliably separate SET and SEF raw ratings in this table row."
                )
                _recompute_missing_fields(record)
                records.append(record)
            continue
        if not pair:
            continue
        set_raw, sef_raw = pair
        sem_word = match.group("sem_word")
        semester = _semester_label_from_token(sem_word)
        academic_year = _normalize_year(match.group("y1"), match.group("y2"))
        line_no = _line_number_at(body, match.start())

        for kind, raw_rating in (("SET", set_raw), ("SEF", sef_raw)):
            rating_text, scale = _rating_display_from_float(raw_rating)
            record = SetSefEvaluationRecord(
                evaluation_type=kind,
                academic_year=academic_year,
                semester=semester,
                overall_rating=rating_text,
                rating_scale=scale,
                source_section_ref=f"table-row:{i + 1}:{kind}:line{line_no}",
                faculty_name=doc_faculty,
                document_title=title,
            )
            _recompute_missing_fields(record)
            records.append(record)

    complete = [r for r in records if r.extraction_status == EXTRACTION_COMPLETE]
    if len(complete) >= 2:
        return records
    if any(r.ambiguous_fields or r.uncertainty_notes for r in records):
        return records
    return []


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
    filtered: list[tuple[int, str]] = []
    for pos, norm in collapsed:
        if filtered and pos - filtered[-1][0] < 120:
            continue
        filtered.append((pos, norm))
    year_spans = [(pos, pos) for pos, _ in filtered]

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
            if len(chunk) < 40:
                continue
            line_no = _line_number_at(text, ystart)
            blocks.append((f"period:{i + 1}:line{line_no}", chunk))
        if len(blocks) >= 2:
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

    table_records = _parse_combined_semester_rating_table(raw)
    if table_records:
        return table_records

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

    return merge_fragment_records(records)


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

    doc_faculty = _extract_faculty_name(raw)
    if doc_faculty:
        out.faculty_name = doc_faculty
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
    criterion_id: str | None = None,
) -> dict:
    """Merge SET/SEF parsing into document extracted_info (reviewer-facing keys)."""
    merged = dict(info or {})
    if not should_run_set_sef_pipeline(indicator_id=indicator_id, criterion_id=criterion_id):
        return merged

    multi = parse_set_sef_metadata_multi(text)
    parsed = parse_set_sef_metadata(text)
    composition = classify_document_composition(multi)
    auto_upload = is_auto_criterion_a_upload(indicator_id)
    verification = (
        _VERIFICATION_UNDETERMINED
        if auto_upload
        else verify_selected_indicator(indicator_id, parsed)
    )
    merged["Document evaluation composition"] = composition
    merged["Detected evaluation section count"] = str(len(multi))
    if auto_upload:
        class_status = classification_status_from_composition(composition, len(multi))
        merged["Document classification status"] = class_status
        merged["OCR-based indicator routing"] = "automatic"
        if class_status == "needs_classification":
            merged["Validation status"] = "Needs Classification"
        else:
            merged.pop("Validation status", None)

    if parsed.document_title:
        merged["Extracted title"] = parsed.document_title

    candidates = _collect_faculty_name_candidates(text, multi)
    doc_faculty = _resolve_document_faculty_name(text, multi)
    if len(candidates) > 1:
        merged["Faculty name candidates"] = "; ".join(candidates)
        merged["Faculty name extraction status"] = "ambiguous"
        merged["Faculty name on document"] = candidates[0]
        merged.pop("Faculty name", None)
        merged.pop("Extracted names", None)
    elif doc_faculty:
        merged["Faculty name on document"] = doc_faculty
        merged["Faculty name"] = doc_faculty
        merged["Extracted names"] = doc_faculty
        merged["Faculty name extraction status"] = "detected"
        merged["Identity field label"] = "Faculty name"
        merged.pop("Faculty name candidates", None)
    else:
        merged.pop("Faculty name", None)
        merged.pop("Extracted names", None)
        merged.pop("Faculty name candidates", None)
        merged["Faculty name on document"] = ""
        merged["Faculty name extraction status"] = "not_detected"

    multi_semester = len(multi) > 1
    if multi_semester:
        _apply_multi_semester_summary_fields(merged, multi, composition=composition)
    else:
        merged.pop("Multi-semester document", None)
        merged.pop("Document-level rating note", None)
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
        merged["Document type"] = _composition_display(composition)
        if multi:
            merged["SET record count"] = str(sum(1 for r in multi if r.evaluation_type == "SET"))
            merged["SEF record count"] = str(sum(1 for r in multi if r.evaluation_type == "SEF"))

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


def mark_set_sef_processing_failed(
    info: dict,
    *,
    indicator_id: str | None,
    message: str,
    criterion_id: str | None = None,
) -> dict:
    merged = dict(info or {})
    if not should_run_set_sef_pipeline(indicator_id=indicator_id, criterion_id=criterion_id):
        return merged
    if is_auto_criterion_a_upload(indicator_id):
        merged["Document classification status"] = "needs_classification"
        merged["Validation status"] = "Needs Classification"
    merged["Indicator verification status"] = _VERIFICATION_FAILED
    merged["SET/SEF extraction status"] = "failed"
    merged["Missing extraction fields"] = merged.get("Missing extraction fields") or "all fields"
    merged["Extraction error"] = message
    merged["Extraction processed at"] = datetime.now(timezone.utc).isoformat()
    return merged
