"""KRA II structured OCR metadata (advisory; reviewer verification still required)."""

from __future__ import annotations

import hashlib
import re
from typing import Any

from kra_configuration.kra2_annex import is_kra2_indicator
from kra_configuration.kra2_indicator_registry import (
    FAMILY_CITATION,
    FAMILY_COMMERCIAL,
    FAMILY_CREATIVE,
    FAMILY_INVENTION,
    FAMILY_PERFORMANCE,
    user_facing_title,
    workflow_family,
)

OCR_EXTRACTION_KEY = "kra2PublicationOcr"
OCR_EXTRACTION_VERSION = "1.3"

_DOI_RE = re.compile(r"\b(10\.\d{4,9}/[-._;()/:A-Z0-9]+)\b", re.I)
_ISBN_RE = re.compile(r"\b(?:ISBN[- ]?(?:13|10)?[: ]*)?(97[89][- ]?\d[- ]?\d{2}[- ]?\d{6}[- ]?\d)\b", re.I)
_DATE_RE = re.compile(
    r"\b(?:"
    r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
    r"Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
    r"[\s,]+?\d{1,2}[\s,]+?\d{4}|"
    r"\d{4}[-/]\d{2}[-/]\d{2}|"
    r"\d{1,2}[-/]\d{1,2}[-/]\d{4}|"
    r"\b(19|20)\d{2}\b"
    r")",
    re.I,
)

_REG_NUMBER_STOPWORDS = frozenset(
    {
        "publication",
        "application",
        "patent",
        "notice",
        "grant",
        "registration",
        "number",
        "certificate",
        "invention",
        "utility",
        "model",
        "accepted",
        "published",
        "pending",
    }
)

_REG_NUMBER_PATTERNS: tuple[tuple[re.Pattern[str], int], ...] = (
    (
        re.compile(
            r"\bPublication\s+(?:No\.|Number)\s*[:#]?\s*([A-Z0-9][A-Z0-9\-/\.]{2,})",
            re.I,
        ),
        30,
    ),
    (
        re.compile(
            r"\bApplication\s+(?:No\.|Number)\s*[:#]?\s*([A-Z0-9][A-Z0-9\-/\.]{2,})",
            re.I,
        ),
        25,
    ),
    (
        re.compile(
            r"\b(?:Patent|Registration|Utility\s+Model|UM)\s*(?:No\.?|Number)\s*[:#]?\s*"
            r"([A-Z0-9][A-Z0-9\-/\.]{2,})",
            re.I,
        ),
        20,
    ),
    (
        re.compile(
            r"\bReg(?:istration)?\.?\s*No\.?\s*[:#]?\s*([A-Z0-9][A-Z0-9\-/\.]{2,})",
            re.I,
        ),
        18,
    ),
    (
        re.compile(r"\bIPOPHL\s*(?:Patent|UM)?\s*No\.?\s*([0-9A-Z][0-9A-Z\-/\.]{2,})", re.I),
        15,
    ),
)

_TITLE_LABELS = (
    r"^title\s*:",
    r"title\s+of\s+(?:the\s+)?(?:invention|work|paper|article|book|chapter|study)",
    r"^article\s+title\s*:",
)
_AUTHOR_LABELS = (
    r"^authors?\s*:",
    r"^author\s*:",
    r"^inventors?\s*:",
    r"^inventors?\s*/\s*s\s*:",
    r"^inventor\(s\)\s*:",
    r"name\s*of\s*inventor",
    r"^proprietor\s*:",
    r"^by\s*:",
    r"^written\s+by\s*:",
)
_JOURNAL_LABELS = (
    r"^journal\s*:",
    r"^published\s+in\s*:",
    r"^source\s*:",
    r"^venue\s*:",
)
_PUBLISHER_LABELS = (r"^publisher\s*:", r"^press\s*:")
_DATE_LABELS = (r"^date\s*:", r"^publication\s+date\s*:", r"^published\s*:", r"^registration\s+date\s*:")
_INV_DATE_LABELS = (
    r"^date\s+of\s+publication\s*:",
    r"^publication\s+date\s*:",
    r"^filing\s+date\s*:",
    r"^grant\s+date\s*:",
    r"^registration\s+date\s*:",
    r"^date\s*:",
)
_INVENTION_TITLE_LABELS = (
    r"invention\s+title",
    r"title\s+of\s+(?:the\s+)?invention",
    r"^title\s+of\s+invention\s*:",
)
_INVENTOR_LABELS = (
    r"inventors?\s*/\s*s\s*:?",
    r"inventors?\s*(?:\(s\))?\s*:?",
    r"name\s*of\s*inventor(?:s)?",
    r"^authors?\s*:",
    r"^inventors?\s*:",
)
_REG_APPLICATION_LABELS = (
    r"registration\s*/\s*application\s*no\.?",
    r"application\s*/\s*registration\s*no\.?",
    r"registration\s*(?:/|or)\s*application\s*number",
    r"application\s+(?:no\.|number)\s*[:#]?\s*",
)
_PUBLICATION_NUMBER_LABELS = (
    r"publication\s+(?:no\.|number)\s*[:#]?\s*",
)
_GRANT_PATENT_NUMBER_LABELS = (
    r"patent\s+(?:no\.|number)\s*[:#]?\s*",
    r"grant\s+(?:no\.|number)\s*[:#]?\s*",
    r"registration\s+(?:no\.|number)\s*[:#]?\s*",
)
_FILING_DATE_LABELS = (
    r"filing\s*/\s*event\s+date",
    r"filing\s+date",
    r"event\s+date",
)
_ISSUING_ORG_LABELS = (
    r"issuing\s+organization",
    r"patent\s+office",
    r"registry\s*:?",
    r"intellectual\s+property\s+office",
)

_PLACEHOLDER_ACCOMPLISHMENT_TITLES = frozenset(
    {
        "patent application",
        "patent publication",
        "patent certificate",
        "utility model",
        "industrial design",
        "journal article",
        "book",
        "book chapter",
    }
)


def _info(doc: Any) -> dict[str, Any]:
    raw = getattr(doc, "extracted_info", None)
    return dict(raw) if isinstance(raw, dict) else {}


def ocr_text_from_document(doc: Any) -> str:
    text = (getattr(doc, "extracted_text", None) or "").strip()
    if text:
        return text
    info = _info(doc)
    excerpt = str(info.get("OCR excerpt") or info.get("ocrExcerpt") or "").strip()
    if excerpt:
        return excerpt
    ocr_block = info.get("ocr")
    if isinstance(ocr_block, dict):
        return str(ocr_block.get("text") or ocr_block.get("rawText") or "").strip()
    return ""


def _line_after_label(lines: list[str], patterns: tuple[str, ...]) -> str | None:
    compiled = [re.compile(p, re.I) for p in patterns]
    for i, ln in enumerate(lines):
        for pat in compiled:
            m = pat.search(ln.strip())
            if not m:
                continue
            rest = ln[m.end() :].lstrip(" \t:-#")
            if rest:
                return rest[:500]
            if i + 1 < len(lines):
                nxt = lines[i + 1].strip()
                if nxt and len(nxt) < 400:
                    return nxt[:500]
    return None


def _first_doi(text: str) -> str | None:
    m = _DOI_RE.search(text or "")
    return m.group(1)[:200] if m else None


def _first_date(text: str) -> str | None:
    m = _DATE_RE.search(text or "")
    return m.group(0)[:120] if m else None


def _normalize_inventor_line(value: str) -> str:
    v = (value or "").strip()
    if not v:
        return ""
    v = re.sub(r"\s*;\s*", "; ", v)
    v = re.sub(r"\s+and\s+", "; ", v, flags=re.I)
    return v.strip(" ;")[:300]


def _extract_best_date(text: str, lines: list[str], label_patterns: tuple[str, ...]) -> str | None:
    labeled = _line_after_label(lines, label_patterns)
    if labeled:
        for match in _DATE_RE.finditer(labeled):
            val = match.group(0)
            if not re.fullmatch(r"(19|20)\d{2}", val):
                return val[:120]
        match = _DATE_RE.search(labeled)
        if match:
            return match.group(0)[:120]
    full_dates: list[str] = []
    year_only: list[str] = []
    for match in _DATE_RE.finditer(text or ""):
        val = match.group(0)
        if re.fullmatch(r"(19|20)\d{2}", val):
            year_only.append(val)
        else:
            full_dates.append(val)
    if full_dates:
        for preferred in full_dates:
            if re.search(r"\d{4}[-/]\d{2}[-/]\d{2}", preferred):
                return preferred[:120]
        return full_dates[0][:120]
    return year_only[0][:120] if year_only else None


def _date_extraction_status(val: str) -> str:
    v = (val or "").strip()
    if re.fullmatch(r"(19|20)\d{2}", v):
        return "partial"
    return "extracted"


def _is_plausible_registration_number(value: str) -> bool:
    v = (value or "").strip().strip(".,;")
    if len(v) < 3:
        return False
    if v.casefold() in _REG_NUMBER_STOPWORDS:
        return False
    if re.fullmatch(r"[A-Za-z]+", v):
        return False
    if not re.search(r"\d", v):
        return False
    return True


def _invention_registration_number_kind(indicator_id: str) -> str:
    iid = (indicator_id or "").casefold()
    if "patent-p" in iid:
        return "publication"
    if "patent-g" in iid:
        return "grant"
    return "application"


def _extract_registration_number(
    text: str,
    lines: list[str] | None = None,
    *,
    indicator_id: str = "",
) -> str | None:
    if lines:
        kind = _invention_registration_number_kind(indicator_id)
        label_order: tuple[tuple[str, ...], ...]
        if kind == "publication":
            label_order = (_PUBLICATION_NUMBER_LABELS, _REG_APPLICATION_LABELS)
        elif kind == "grant":
            label_order = (_GRANT_PATENT_NUMBER_LABELS, _REG_APPLICATION_LABELS)
        else:
            label_order = (_REG_APPLICATION_LABELS, _PUBLICATION_NUMBER_LABELS)
        for label_set in label_order:
            labeled = _line_after_label(lines, label_set)
            if labeled:
                candidate = labeled.strip(" .,;")
                if _is_plausible_registration_number(candidate):
                    return candidate
    best: tuple[int, str] | None = None
    for pattern, priority in _REG_NUMBER_PATTERNS:
        for match in pattern.finditer(text or ""):
            candidate = match.group(1).strip(" .,;")
            if not _is_plausible_registration_number(candidate):
                continue
            if best is None or priority > best[0]:
                best = (priority, candidate)
    return best[1] if best else None


def validate_extracted_field(field_id: str, value: str, indicator_id: str) -> tuple[str | None, str]:
    """Return (cleaned value, status) where status is extracted | partial | rejected."""
    v = (value or "").strip()
    if not v:
        return None, "rejected"
    family = workflow_family(indicator_id) if indicator_id else ""

    if field_id == "registrationNumber":
        if not _is_plausible_registration_number(v):
            return None, "rejected"
        return v[:120], "extracted"

    if field_id in ("publicationDate", "registrationDate"):
        return v[:120], _date_extraction_status(v)

    if field_id == "outputTitle":
        low = v.casefold()
        if low in _PLACEHOLDER_ACCOMPLISHMENT_TITLES:
            return None, "rejected"
        if family == FAMILY_INVENTION and re.search(
            r"patent\s+publication\s+notice|formality\s+examination|"
            r"intellectual\s+property\s+office|substantive\s+examination|"
            r"application\s+acknowledgement|acknowledgment",
            low,
        ):
            return None, "rejected"
        return v[:500], "extracted"

    if field_id == "publicationReference":
        if _DOI_RE.search(v):
            return v[:200], "extracted"
        if _ISBN_RE.search(v):
            return v[:200], "extracted"
        return None, "rejected"

    if field_id == "authorsLine":
        if len(v) < 3 or v.casefold() in _REG_NUMBER_STOPWORDS:
            return None, "rejected"
        return v[:300], "extracted"

    return v[:500], "extracted"


def _names_after_label(lines: list[str], patterns: tuple[str, ...]) -> str | None:
    compiled = [re.compile(p, re.I) for p in patterns]
    section_break = re.compile(
        r"^(application|publication|patent|date|title|reg\.|registration|"
        r"this is to|intellectual property|ipophl|republic)\b",
        re.I,
    )
    for i, ln in enumerate(lines):
        for pat in compiled:
            m = pat.search(ln.strip())
            if not m:
                continue
            parts: list[str] = []
            rest = ln[m.end() :].strip(" :-\t")
            if rest:
                parts.append(rest)
            for j in range(i + 1, min(i + 8, len(lines))):
                nxt = lines[j].strip()
                if not nxt:
                    break
                if section_break.search(nxt):
                    break
                if re.search(r"\b(?:No\.|Number)\s*[:#]", nxt, re.I):
                    break
                parts.append(nxt)
            joined = ", ".join(p.strip() for p in parts if p.strip())
            if joined:
                return joined[:300]
    return None


def _guess_title_line(lines: list[str]) -> str | None:
    labeled = _line_after_label(lines, _TITLE_LABELS)
    if labeled:
        return labeled
    skip = re.compile(
        r"^(abstract|keywords|introduction|doi|issn|volume|issue|copyright|page|\d+\s*$)",
        re.I,
    )
    for ln in lines[:25]:
        if len(ln) < 12 or len(ln) > 300:
            continue
        if skip.search(ln):
            continue
        if re.search(r"\b(university|college|journal|vol\.|pp\.|issn|doi:)\b", ln, re.I):
            continue
        return ln[:500]
    return lines[0][:500] if lines else None


def _parse_publication(text: str) -> dict[str, str]:
    lines = [ln.strip() for ln in (text or "").splitlines() if ln.strip()]
    out: dict[str, str] = {}
    title = _guess_title_line(lines)
    if title:
        out["outputTitle"] = title
    authors = _line_after_label(lines, _AUTHOR_LABELS)
    if authors:
        out["authorsLine"] = authors[:300]
    journal = _line_after_label(lines, _JOURNAL_LABELS)
    if journal:
        out["outputVenue"] = journal[:300]
        out["journalTitle"] = journal[:300]
    if not journal:
        for ln in lines[:40]:
            if re.search(r"\bjournal\b|\bvol\.\s*\d|\bissn\b", ln, re.I) and len(ln) < 300:
                out.setdefault("outputVenue", ln[:300])
                out.setdefault("journalTitle", ln[:300])
                break
    publisher = _line_after_label(lines, _PUBLISHER_LABELS)
    if publisher and "outputVenue" not in out:
        out["outputVenue"] = publisher[:300]
    doi = _first_doi(text)
    if doi:
        out["publicationReference"] = doi
    date_val = _line_after_label(lines, _DATE_LABELS) or _first_date(text)
    if date_val:
        out["publicationDate"] = date_val
    isbn = _ISBN_RE.search(text or "")
    if isbn:
        out["publicationReference"] = out.get("publicationReference") or isbn.group(1)[:200]
    return out


def _guess_invention_title(lines: list[str], indicator_id: str) -> str | None:
    labeled = _line_after_label(lines, _INVENTION_TITLE_LABELS + _TITLE_LABELS)
    if labeled:
        cleaned, status = validate_extracted_field("outputTitle", labeled, indicator_id)
        if cleaned and status != "rejected":
            return cleaned
    skip = re.compile(
        r"^(patent\s+publication|republic\s+of|intellectual\s+property|ipophl|"
        r"application\s+no|publication\s+no|notice|formality|substantive|abstract|\d+\s*$)",
        re.I,
    )
    for ln in lines[:35]:
        if len(ln) < 12 or len(ln) > 300:
            continue
        if skip.search(ln):
            continue
        if re.search(r"\b(university|college|issn|doi:|vol\.|pp\.)\b", ln, re.I):
            continue
        cleaned, status = validate_extracted_field("outputTitle", ln, indicator_id)
        if cleaned and status != "rejected":
            return cleaned
    return None


def _parse_invention(text: str, indicator_id: str = "") -> dict[str, str]:
    lines = [ln.strip() for ln in (text or "").splitlines() if ln.strip()]
    out: dict[str, str] = {}
    title = (
        _line_after_label(lines, _INVENTION_TITLE_LABELS)
        or _guess_invention_title(lines, indicator_id)
        or _line_after_label(lines, _TITLE_LABELS)
    )
    if title:
        out["outputTitle"] = title
    raw_inventors = (
        _line_after_label(lines, _INVENTOR_LABELS)
        or _names_after_label(lines, _INVENTOR_LABELS + _AUTHOR_LABELS)
        or _line_after_label(lines, _AUTHOR_LABELS)
    )
    inventors = _normalize_inventor_line(raw_inventors or "")
    if inventors:
        out["authorsLine"] = inventors
    reg_no = _extract_registration_number(text or "", lines, indicator_id=indicator_id)
    if reg_no:
        out["registrationNumber"] = reg_no
    date_val = _extract_best_date(
        text or "",
        lines,
        _FILING_DATE_LABELS + _INV_DATE_LABELS,
    )
    if date_val:
        out["registrationDate"] = date_val
    venue = _line_after_label(lines, _ISSUING_ORG_LABELS)
    if venue:
        out["outputVenue"] = venue[:300]
    else:
        for ln in lines[:40]:
            if len(ln) < 300 and re.search(
                r"\bIntellectual\s+Property\s+Office\b|\bIPOPHL\b|\bIPO\b|\bregistry\b|\bBureau\b",
                ln,
                re.I,
            ):
                out["outputVenue"] = ln[:300]
                break
    return out


def _parse_citation(text: str) -> dict[str, str]:
    lines = [ln.strip() for ln in (text or "").splitlines() if ln.strip()]
    out: dict[str, str] = {}
    title = _guess_title_line(lines)
    if title:
        out["outputTitle"] = title
    for ln in lines[:40]:
        if re.search(r"\bcit(?:ed|ing|ation)\b", ln, re.I) and len(ln) < 400:
            out["citationContext"] = ln[:400]
            break
    date_val = _first_date(text)
    if date_val:
        out["publicationDate"] = date_val
    doi = _first_doi(text)
    if doi:
        out["publicationReference"] = doi
    return out


def _parse_creative(text: str) -> dict[str, str]:
    lines = [ln.strip() for ln in (text or "").splitlines() if ln.strip()]
    out: dict[str, str] = {}
    title = _line_after_label(lines, _TITLE_LABELS) or _guess_title_line(lines)
    if title:
        out["outputTitle"] = title
    creators = _line_after_label(lines, _AUTHOR_LABELS)
    if creators:
        out["authorsLine"] = creators[:300]
    venue = _line_after_label(lines, _JOURNAL_LABELS + (r"^venue\s*:", r"^organization\s*:", r"^presented\s+at\s*:"))
    if venue:
        out["outputVenue"] = venue[:300]
    date_val = _line_after_label(lines, _DATE_LABELS) or _first_date(text)
    if date_val:
        out["publicationDate"] = date_val
    return out


def extract_fields_for_indicator(text: str, indicator_id: str) -> dict[str, str]:
    family = workflow_family(indicator_id)
    if family == FAMILY_CITATION:
        return _parse_citation(text)
    if family == FAMILY_INVENTION:
        return _parse_invention(text, indicator_id)
    if family == FAMILY_COMMERCIAL:
        parsed = _parse_invention(text, indicator_id)
        if "outputVenue" not in parsed:
            for ln in (text or "").splitlines():
                if re.search(r"\bcommercial|market|license\b", ln, re.I):
                    parsed["outputVenue"] = ln.strip()[:300]
                    break
        return parsed
    if family in (FAMILY_CREATIVE, FAMILY_PERFORMANCE):
        return _parse_creative(text)
    return _parse_publication(text)


def _field_blocks(raw: dict[str, str], indicator_id: str) -> dict[str, dict[str, str]]:
    blocks: dict[str, dict[str, str]] = {}
    for key, val in raw.items():
        v = (val or "").strip()
        if not v:
            continue
        cleaned, status = validate_extracted_field(key, v, indicator_id)
        if not cleaned or status == "rejected":
            continue
        blocks[key] = {"value": cleaned, "status": status, "source": "ocr"}
    return blocks


def build_extraction_payload(fields: dict[str, str], *, indicator_id: str = "") -> dict[str, Any]:
    return {
        "version": OCR_EXTRACTION_VERSION,
        "fields": _field_blocks(fields, indicator_id),
        "ocrHintOnly": True,
    }


def parse_and_store_kra2_ocr(doc: Any, *, text: str | None = None, force: bool = False) -> dict[str, Any] | None:
    if not is_kra2_indicator(getattr(doc, "indicator_id", None)):
        return None
    ocr_status = (getattr(doc, "ocr_status", None) or "").strip().lower()
    if ocr_status not in ("complete", "completed", "done") and text is None:
        return None
    body = (text if text is not None else ocr_text_from_document(doc)).strip()
    if not body:
        info = _info(doc)
        existing = info.get(OCR_EXTRACTION_KEY)
        return existing if isinstance(existing, dict) else None
    info = _info(doc)
    digest = hashlib.sha256(body.encode("utf-8", errors="ignore")).hexdigest()
    if not force:
        existing = info.get(OCR_EXTRACTION_KEY)
        if isinstance(existing, dict) and existing.get("fields") and existing.get("sourceTextHash"):
            if (
                existing.get("sourceTextHash") == digest
                and existing.get("version") == OCR_EXTRACTION_VERSION
            ):
                return existing
    indicator_id = (getattr(doc, "indicator_id", None) or "").strip()
    fields = extract_fields_for_indicator(body, indicator_id)
    payload = build_extraction_payload(fields, indicator_id=indicator_id)
    payload["sourceTextHash"] = hashlib.sha256(body.encode("utf-8", errors="ignore")).hexdigest()
    info[OCR_EXTRACTION_KEY] = payload
    doc.extracted_info = info
    return payload


def ensure_publication_ocr_extraction(doc: Any) -> dict[str, Any] | None:
    """Re-parse stored OCR text into structured fields when missing."""
    return parse_and_store_kra2_ocr(doc, force=False)


def _is_year_only_date(value: str) -> bool:
    return bool(re.fullmatch(r"(19|20)\d{2}", (value or "").strip()))


def _is_placeholder_title(bundle: dict[str, Any], current: str) -> bool:
    cur = (current or "").strip()
    if not cur:
        return True
    if cur.casefold() in _PLACEHOLDER_ACCOMPLISHMENT_TITLES:
        return True
    indicator_id = (bundle.get("indicatorId") or "").strip()
    if not indicator_id:
        return False
    for candidate in (
        (bundle.get("indicatorTitle") or "").strip(),
        user_facing_title(indicator_id),
    ):
        if candidate and cur.casefold() == candidate.casefold():
            return True
    return False


def merge_ocr_into_bundle(bundle: dict[str, Any], extraction: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(extraction, dict):
        return bundle
    confirmed = bundle.get("metadataConfirmed") if isinstance(bundle.get("metadataConfirmed"), dict) else {}
    fields = extraction.get("fields") if isinstance(extraction.get("fields"), dict) else {}
    merge_keys = (
        "outputTitle",
        "journalTitle",
        "outputVenue",
        "authorsLine",
        "publicationDate",
        "publicationReference",
        "registrationNumber",
        "registrationDate",
        "citationContext",
    )
    for key in merge_keys:
        if confirmed.get(key):
            continue
        block = fields.get(key) if isinstance(fields.get(key), dict) else {}
        if (block.get("status") or "").strip().lower() == "rejected":
            continue
        val = (block.get("value") or "").strip()
        if not val:
            continue
        current = (bundle.get(key) or "").strip()
        if key == "outputTitle":
            if current and not _is_placeholder_title(bundle, current):
                continue
        elif current:
            if key == "registrationNumber" and not _is_plausible_registration_number(current):
                bundle[key] = val
            elif key in ("registrationDate", "publicationDate") and _is_year_only_date(current) and not _is_year_only_date(val):
                bundle[key] = val
            continue
        bundle[key] = val
    jt = (bundle.get("journalTitle") or "").strip()
    if jt and not (bundle.get("outputVenue") or "").strip():
        bundle["outputVenue"] = jt
    return bundle


def _normalize_name(name: str) -> str:
    return re.sub(r"\s+", " ", (name or "").strip().casefold())


def _name_tokens(name: str) -> set[str]:
    return {t for t in _normalize_name(name).split() if len(t) > 1}


def author_match_flags(
    *,
    authors_line: str,
    faculty_display_name: str,
) -> list[str]:
    flags: list[str] = []
    faculty = (faculty_display_name or "").strip()
    authors = (authors_line or "").strip()
    if not faculty or not authors:
        return flags
    fn = _normalize_name(faculty)
    an = _normalize_name(authors)
    if fn in an or an in fn:
        return flags
    ft = _name_tokens(faculty)
    at = _name_tokens(authors)
    if ft and at and ft.intersection(at):
        return flags
    flags.append("logged_in_faculty_not_detected_in_authors")
    return flags


def ocr_review_flags_for_document(doc: Any, bundle: dict[str, Any] | None) -> list[str]:
    if not isinstance(bundle, dict):
        return []
    try:
        from models import FacultyProfile

        profile = FacultyProfile.query.get(doc.faculty_profile_id) if doc.faculty_profile_id else None
        display = ""
        if profile and profile.user:
            display = (profile.user.full_name or "").strip()
    except Exception:  # noqa: BLE001
        display = ""
    return author_match_flags(
        authors_line=str(bundle.get("authorsLine") or ""),
        faculty_display_name=display,
    )


def apply_kra2_ocr_pipeline(doc: Any, *, text: str) -> None:
    """Run after OCR success: parse text, persist extraction, merge into bundle if present."""
    from documents.kra2_evidence.bundle import bundle_from_document, persist_bundle

    parse_and_store_kra2_ocr(doc, text=text, force=True)
    bundle = bundle_from_document(doc)
    if not isinstance(bundle, dict):
        return
    info = _info(doc)
    extraction = info.get(OCR_EXTRACTION_KEY)
    if isinstance(extraction, dict):
        merge_ocr_into_bundle(bundle, extraction)
        persist_bundle(doc, bundle)
