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
OCR_EXTRACTION_VERSION = "1.7"

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
_WORK_TITLE_LABELS = (
    r"title\s+of\s+work\s*/?\s*invention?",
    r"title\s+of\s+(?:the\s+)?work",
    r"name\s+of\s+(?:the\s+)?work",
)
_ARTICLE_TITLE_LABELS = (
    r"chapter\s+title",
    r"title\s+of\s+(?:the\s+)?chapter",
    r"article\s+title",
    r"title\s+of\s+(?:the\s+)?article",
    r"paper\s+title",
    r"manuscript\s+title",
    r"research\s+article\s+title",
    r"^book\s+title\s*:?\s*$",
    r"title\s+of\s+(?:the\s+)?book",
)
_AUTHOR_LABELS = (
    r"author\s*\(?s?\)?\s*/\s*inventor\s*\(?s?\)?\s*/\s*creator\s*\(?s?\)?",
    r"creators?\s*\(?s?\)?\s*:?\s*$",
    r"contributors?\s*\(?s?\)?\s*:?\s*$",
    r"^authors?\s*:",
    r"^author\s+names?\s*:",
    r"^author\s*:",
    r"^authors?\s*:?\s*$",
    r"^author\s+names?\s*:?\s*$",
    r"^inventors?\s*:",
    r"^inventors?\s*/\s*s\s*:",
    r"^inventor\(s\)\s*:",
    r"name\s*of\s*inventor",
    r"^proprietor\s*:",
    r"^by\s*:",
    r"^written\s+by\s*:",
)
_JOURNAL_LABELS = (
    r"journal\s*/\s*publisher\s*/\s*issuing\s+organization",
    r"journal\s+name",
    r"^journal\s*:",
    r"^journal\s*:?\s*$",
    r"^published\s+in\s*:",
    r"^publisher\s*:",
    r"^publisher\s*:?\s*$",
    r"^source\s*:",
    r"^venue\s*:?\s*$",
    r"^venue\s*:",
    r"^press\s*:",
)
_PUBLICATION_DATE_LABELS = (
    r"publication\s*/\s*registration\s*/\s*event\s+date",
    r"publication\s+date",
    r"date\s+published",
    r"^date\s*:",
    r"^publication\s+date\s*:",
    r"^published\s*:",
)
_REFERENCE_LABELS = (
    r"doi\s*/\s*registration\s*/\s*reference\s*(?:number)?\s*:?\s*$",
    r"doi\s*/\s*reference\s*(?:number)?\s*:?\s*$",
    r"registration\s*/\s*reference\s*(?:number)?\s*:?\s*$",
    r"^doi\s*:?\s*$",
    r"^reference\s*:?\s*$",
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

_DISCLAIMER_TITLE_RE = re.compile(
    r"(?:"
    r"\bfictional\b|"
    r"for\s+system\s+testing|"
    r"system\s+testing\s+only|"
    r"not\s+(?:a\s+)?real(?:\s+certification|\s+document|\s+record)?|"
    r"not\s+an?\s+official|"
    r"sample\s+document|"
    r"for\s+testing\s+purposes|"
    r"facultylink\s+test|"
    r"simulated\s+test\s+evidence|"
    r"software\s+testing\s+only|"
    r"synthetic|"
    r"not\s+issued|"
    r"not\s+authentic"
    r")",
    re.I,
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


def _is_disclaimer_or_banner_line(line: str) -> bool:
    ln = (line or "").strip()
    if len(ln) < 8:
        return False
    if len(ln) > 18 and re.search(r"\((?:fictional|not\s+real)\)\s*$", ln, re.I) and not re.search(
        r"for\s+system\s+testing|testing\s+only|system\s+testing\s+only", ln, re.I
    ):
        return False
    if _DISCLAIMER_TITLE_RE.search(ln):
        if len(ln) > 32 and re.search(
            r"\b(journal\s+of|press|university|office|department|learning)\b", ln, re.I
        ) and not re.search(r"for\s+system\s+testing|system\s+testing\s+only", ln, re.I):
            return False
        return True
    if re.search(r"facultylink\s*[|•]", ln, re.I) and re.search(r"test|simulated|fictional", ln, re.I):
        return True
    return False


def _is_disclaimer_title(value: str) -> bool:
    v = (value or "").strip()
    if not v:
        return False
    return _is_disclaimer_or_banner_line(v)


_METADATA_LABEL_PHRASE = re.compile(
    r"(?:"
    r"publication\s+information|page\s+and\s+publication|document\s+details|"
    r"supporting\s+document|field\s+labels?|accomplishment\s+type|"
    r"testing\s+instructions|supporting\s+narrative|kra\s+ii\s+criterion|"
    r"criterion\s+[abc]\b|"
    r"journal\s*/\s*publisher|issuing\s+organization|"
    r"author\s*names?|publication\s+date|reference\s+number|"
    r"doi\s*/\s*registration|registration\s*/\s*reference|"
    r"publication\s*/\s*registration"
    r")",
    re.I,
)


def _value_looks_like_date(value: str) -> bool:
    v = (value or "").strip()
    if not v:
        return False
    if re.fullmatch(r"(19|20)\d{2}", v):
        return True
    if _DATE_RE.search(v) and len(v) <= 40:
        return True
    return False


def _looks_like_ui_instruction_text(value: str) -> bool:
    """OCR sometimes captures faculty-facing helper copy, not documentary names."""
    v = (value or "").strip()
    if len(v) < 18:
        return False
    low = v.casefold()
    if re.search(
        r"\b(please\s+(enter|add|complete|check)|enter\s+the\s+missing|try\s+reading\s+again|"
        r"information\s+below|missing\s+information|we\s+could\s*n'?t\s+read|found\s+in\s+your\s+document|"
        r"you\s+can\s+try|check\s+these\s+details|before\s+you\s+send)\b",
        low,
    ):
        return True
    if v.endswith(".") and re.search(r"\b(you|your|please|enter|missing|information)\b", low) and len(v) > 40:
        return True
    return False


def is_metadata_label_value(value: str, *, field_id: str = "") -> bool:
    """True when text is a form heading/label, not documentary metadata."""
    v = (value or "").strip()
    if not v:
        return True
    low = v.casefold()
    if _is_disclaimer_title(v):
        return True
    if v.rstrip().endswith("/") or v.rstrip().endswith(" /"):
        return True
    if re.fullmatch(r"(authors?|journal|venue|publisher|doi|date|book|title|inventors?)", low):
        return True
    if v.count("/") >= 2 and re.search(
        r"journal|publisher|author|inventor|creator|venue|organization|registration|reference",
        low,
    ):
        return True
    if _METADATA_LABEL_PHRASE.search(v) and len(v) < 160:
        return True
    if field_id == "outputTitle" and re.search(
        r"\b(information|details|instructions|narrative|overview|type)\b", low
    ) and len(v) < 100:
        return True
    if field_id in ("outputVenue", "journalTitle"):
        if re.search(r"\b(journal\s+of|press|university|college|publisher)\b", low) and len(v) > 14:
            if not v.rstrip().endswith("/"):
                return False
        if _METADATA_LABEL_PHRASE.search(v):
            return True
        if re.search(r"simulated\s+journal|journal\s+article\s+page", low):
            return True
    if field_id in ("publicationDate", "registrationDate") and not _value_looks_like_date(v):
        return True
    if field_id == "authorsLine":
        if len(v) < 3 or low in _REG_NUMBER_STOPWORDS:
            return True
        if _METADATA_LABEL_PHRASE.search(v):
            return True
        if _looks_like_ui_instruction_text(v):
            return True
    if field_id in ("outputTitle", "outputVenue", "citationContext") and _looks_like_ui_instruction_text(v):
        return True
    return False


def _line_after_label_priority(
    lines: list[str],
    pattern_groups: tuple[tuple[str, ...], ...],
) -> str | None:
    for patterns in pattern_groups:
        val = _line_after_label(lines, patterns)
        if val:
            return val
    return None


def _following_value_line(lines: list[str], start_index: int) -> str | None:
    for j in range(start_index + 1, min(start_index + 6, len(lines))):
        nxt = lines[j].strip()
        if not nxt:
            continue
        if _is_disclaimer_or_banner_line(nxt):
            break
        if is_metadata_label_value(nxt):
            continue
        if len(nxt) < 400:
            return nxt[:500]
    return None


def _line_after_label(lines: list[str], patterns: tuple[str, ...], *, field_id: str = "") -> str | None:
    compiled = [re.compile(p, re.I) for p in patterns]
    for i, ln in enumerate(lines):
        for pat in compiled:
            m = pat.search(ln.strip())
            if not m:
                continue
            rest = ln[m.end() :].lstrip(" \t:-#")
            if rest and re.fullmatch(r"number", rest, re.I):
                rest = ""
            candidate = rest if rest and not is_metadata_label_value(rest, field_id=field_id) else None
            if not candidate:
                candidate = _following_value_line(lines, i)
            if candidate and not is_metadata_label_value(candidate, field_id=field_id):
                return candidate[:500]
    return None


def _first_doi(text: str) -> str | None:
    m = _DOI_RE.search(text or "")
    return m.group(1)[:200] if m else None


def _first_date(text: str) -> str | None:
    m = _DATE_RE.search(text or "")
    return m.group(0)[:120] if m else None


def _normalize_issuing_venue(venue: str | None, full_text: str) -> str | None:
    v = (venue or "").strip()
    if re.search(r"Intellectual\s+Property\s+Office\s+of", v, re.I):
        return v[:300]
    if re.search(r"\bIPOPHL\b", v, re.I) and "Intellectual Property Office" not in v:
        v = ""
    elif v and not re.match(r"^(?:of|the)\b", v, re.I):
        if len(v) >= 8:
            return v[:300]
    if re.match(r"^(?:of|the)\b", (venue or "").strip(), re.I):
        v = ""
    m = re.search(
        r"Intellectual\s+Property\s+Office\s+of\s+the\s+Philippines(?:\s*\(\s*IPOPHL\s*\))?",
        full_text or "",
        re.I,
    )
    if m:
        return m.group(0).strip()[:300]
    if re.search(r"\bIPOPHL\b", full_text or "", re.I):
        return "Intellectual Property Office of the Philippines (IPOPHL)"
    return v[:300] if v else None


_CONTRIBUTION_PERCENT_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(
        r"percentage\s+of\s+contribution\s*:?\s*(\d{1,3})\s*%?",
        re.I,
    ),
    re.compile(
        r"contribution\s+(?:share|percent(?:age)?)\s*:?\s*(\d{1,3})\s*%?",
        re.I,
    ),
    re.compile(r"(\d{1,3})\s*%\s*contribution", re.I),
)


def _extract_contribution_percent_advisory(text: str) -> str | None:
    body = text or ""
    for pat in _CONTRIBUTION_PERCENT_PATTERNS:
        m = pat.search(body)
        if not m:
            continue
        try:
            pct = int(m.group(1))
        except (TypeError, ValueError):
            continue
        if 0 < pct <= 100:
            return str(pct)
    return None


def _merge_contribution_annex_hints(raw: dict[str, str], text: str, indicator_id: str) -> None:
    if "declaredContributionPercent" in raw:
        return
    if not re.search(
        r"Annex\s+[FGH]|Certificate\s+of\s+Contribution|Form[_\s]+Software|Cultivars?,\s*Breeds",
        text or "",
        re.I,
    ):
        from kra_configuration.kra2_indicator_registry import contribution_mode

        if contribution_mode(indicator_id) != "declared":
            return
    pct = _extract_contribution_percent_advisory(text)
    if pct:
        raw["declaredContributionPercent"] = pct


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
        if not _value_looks_like_date(v):
            return None, "rejected"
        return v[:120], _date_extraction_status(v)

    if field_id == "outputTitle":
        low = v.casefold()
        if is_metadata_label_value(v, field_id="outputTitle"):
            return None, "rejected"
        if low in _PLACEHOLDER_ACCOMPLISHMENT_TITLES:
            return None, "rejected"
        if _is_disclaimer_title(v):
            return None, "rejected"
        if family in (FAMILY_CREATIVE, FAMILY_PERFORMANCE):
            if re.match(r"^/?\s*(invention|patent|utility\s+model|journal\s+article)\b", low):
                return None, "rejected"
            if re.fullmatch(r"/?\s*invention", low):
                return None, "rejected"
            if len(v) < 4:
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
        if re.fullmatch(r"[A-Z0-9][A-Z0-9\-/.]{4,}", v, re.I) and v.casefold() not in _REG_NUMBER_STOPWORDS:
            return v[:200], "extracted"
        return None, "rejected"

    if field_id == "authorsLine":
        if is_metadata_label_value(v, field_id="authorsLine"):
            return None, "rejected"
        if not re.search(r"[A-Za-z]{2,}", v):
            return None, "rejected"
        return v[:300], "extracted"

    if field_id == "declaredContributionPercent":
        try:
            pct = float(v.replace("%", "").strip())
        except ValueError:
            return None, "rejected"
        if not 0 < pct <= 100:
            return None, "rejected"
        normalized = str(int(pct)) if pct == int(pct) else str(round(pct, 2))
        return normalized, "partial"

    if field_id in ("outputVenue", "journalTitle", "citationContext"):
        if is_metadata_label_value(v, field_id=field_id):
            return None, "rejected"

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
    return _guess_publication_title(lines)


def _guess_publication_title(lines: list[str]) -> str | None:
    labeled = _line_after_label(lines, _ARTICLE_TITLE_LABELS + _TITLE_LABELS)
    if labeled and not _is_disclaimer_title(labeled):
        return labeled
    skip = re.compile(
        r"^(abstract|keywords|introduction|doi|issn|volume|issue|copyright|page|"
        r"faculty|document\s+type|evidence\s+status|overview|note|\d+\s*$)",
        re.I,
    )
    for ln in lines[:40]:
        if len(ln) < 12 or len(ln) > 300:
            continue
        if _is_disclaimer_or_banner_line(ln):
            continue
        if skip.search(ln):
            continue
        if re.search(r"\b(university|college|vol\.|pp\.|issn|doi:|facultylink|simulated)\b", ln, re.I):
            continue
        if re.fullmatch(r"(authors?|journal|publication\s+date|doi)", ln, re.I):
            continue
        return ln[:500]
    return None


def _publication_title_label_groups(indicator_id: str) -> tuple[tuple[str, ...], ...]:
    iid = (indicator_id or "").casefold()
    if "chapter" in iid:
        return (
            (r"chapter\s+title", r"title\s+of\s+(?:the\s+)?chapter"),
            _WORK_TITLE_LABELS,
            _ARTICLE_TITLE_LABELS,
            _TITLE_LABELS,
        )
    if "book" in iid or "monograph" in iid:
        return (_WORK_TITLE_LABELS, _ARTICLE_TITLE_LABELS, _TITLE_LABELS)
    return (_WORK_TITLE_LABELS, _ARTICLE_TITLE_LABELS, _TITLE_LABELS)


def _parse_publication(text: str, indicator_id: str = "") -> dict[str, str]:
    lines = [ln.strip() for ln in (text or "").splitlines() if ln.strip()]
    out: dict[str, str] = {}
    title = _line_after_label_priority(lines, _publication_title_label_groups(indicator_id)) or _guess_publication_title(
        lines
    )
    if title and not _is_disclaimer_title(title) and not is_metadata_label_value(title, field_id="outputTitle"):
        out["outputTitle"] = title
    raw_authors = (
        _line_after_label(lines, _AUTHOR_LABELS, field_id="authorsLine")
        or _names_after_label(lines, _AUTHOR_LABELS)
    )
    if raw_authors and not re.match(r"^faculty\s*:", raw_authors, re.I):
        out["authorsLine"] = _normalize_inventor_line(raw_authors) or raw_authors[:300]
    journal = _line_after_label(lines, _JOURNAL_LABELS, field_id="outputVenue")
    if journal:
        out["outputVenue"] = journal[:300]
        out["journalTitle"] = journal[:300]
    if not journal:
        for ln in lines[:40]:
            if _is_disclaimer_or_banner_line(ln):
                continue
            if is_metadata_label_value(ln, field_id="outputVenue"):
                continue
            if re.search(r"\bjournal\b|\bvol\.\s*\d|\bissn\b", ln, re.I) and len(ln) < 300:
                out["outputVenue"] = ln[:300]
                out["journalTitle"] = ln[:300]
                break
    publisher = _line_after_label(lines, _PUBLISHER_LABELS)
    if publisher and "outputVenue" not in out:
        out["outputVenue"] = publisher[:300]
    ref_line = _line_after_label(lines, _REFERENCE_LABELS, field_id="publicationReference")
    doi = _first_doi(text)
    if ref_line and not is_metadata_label_value(ref_line, field_id="publicationReference"):
        out["publicationReference"] = ref_line[:200]
    elif doi:
        out["publicationReference"] = doi
    date_val = _line_after_label(lines, _PUBLICATION_DATE_LABELS + _DATE_LABELS, field_id="publicationDate")
    if not date_val or not _value_looks_like_date(date_val):
        date_val = _extract_best_date(text or "", lines, _PUBLICATION_DATE_LABELS)
    if not date_val or not _value_looks_like_date(date_val):
        date_val = _first_date(text)
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
    venue = _normalize_issuing_venue(_line_after_label(lines, _ISSUING_ORG_LABELS), text or "")
    if venue:
        out["outputVenue"] = venue
    return out


_SOFTWARE_TITLE_LABELS = (
    r"software\s+title",
    r"title\s+of\s+(?:the\s+)?(?:software|program|application)",
    r"program\s+title",
    r"^name\s+of\s+software\s*:?",
)
_COPYRIGHT_REG_LABELS = (
    r"copyright\s+(?:reg(?:istration)?\.?\s*)?(?:no\.?|number)\s*:?",
    r"certificate\s+(?:no\.?|number)\s*:?",
    r"reg(?:istration)?\.?\s*no\.?\s*:?",
)
_DEVELOPER_LABELS = (
    r"developer\s*\(?s?\)?\s*:?",
    r"software\s+developer\s*\(?s?\)?\s*:?",
    r"author\s*\(?s?\)?\s*of\s+(?:the\s+)?software",
)
_VARIETY_TITLE_LABELS = (
    r"(?:cultivar|variety|breed|strain)\s+name\s*:?",
    r"name\s+of\s+(?:the\s+)?(?:cultivar|variety|breed|strain)",
    r"title\s+of\s+(?:the\s+)?(?:cultivar|variety|breed|strain)",
)
_DEPOSIT_REG_LABELS = (
    r"deposit\s+(?:no\.?|number)\s*:?",
    r"registration\s+(?:no\.?|number)\s*:?",
    r"accession\s+(?:no\.?|number)\s*:?",
)


def _parse_software(text: str, indicator_id: str = "") -> dict[str, str]:
    lines = [ln.strip() for ln in (text or "").splitlines() if ln.strip()]
    out: dict[str, str] = {}
    title = (
        _line_after_label(lines, _SOFTWARE_TITLE_LABELS + _WORK_TITLE_LABELS + _INVENTION_TITLE_LABELS)
        or _guess_invention_title(lines, indicator_id)
    )
    if title:
        out["outputTitle"] = title
    devs = (
        _line_after_label(lines, _DEVELOPER_LABELS + _INVENTOR_LABELS)
        or _names_after_label(lines, _DEVELOPER_LABELS + _AUTHOR_LABELS)
    )
    if devs:
        out["authorsLine"] = (_normalize_inventor_line(devs) or devs)[:300]
    reg = _line_after_label(lines, _COPYRIGHT_REG_LABELS) or _extract_registration_number(
        text or "", lines, indicator_id=indicator_id
    )
    if reg:
        out["registrationNumber"] = reg
    date_val = _extract_best_date(text or "", lines, _INV_DATE_LABELS + _PUBLICATION_DATE_LABELS)
    if date_val:
        out["registrationDate"] = date_val
    venue = _normalize_issuing_venue(_line_after_label(lines, _ISSUING_ORG_LABELS), text or "")
    if venue:
        out["outputVenue"] = venue
    return out


def _parse_variety(text: str, indicator_id: str = "") -> dict[str, str]:
    lines = [ln.strip() for ln in (text or "").splitlines() if ln.strip()]
    out: dict[str, str] = {}
    title = (
        _line_after_label(lines, _VARIETY_TITLE_LABELS + _INVENTION_TITLE_LABELS)
        or _guess_invention_title(lines, indicator_id)
    )
    if title:
        out["outputTitle"] = title
    breeders = (
        _line_after_label(lines, _DEVELOPER_LABELS + _INVENTOR_LABELS)
        or _names_after_label(lines, _AUTHOR_LABELS)
    )
    if breeders:
        out["authorsLine"] = (_normalize_inventor_line(breeders) or breeders)[:300]
    reg = _line_after_label(lines, _DEPOSIT_REG_LABELS) or _extract_registration_number(
        text or "", lines, indicator_id=indicator_id
    )
    if reg:
        out["registrationNumber"] = reg
    date_val = _extract_best_date(text or "", lines, _INV_DATE_LABELS)
    if date_val:
        out["registrationDate"] = date_val
    for ln in lines[:40]:
        if re.search(r"\b(?:PCAARRD|Bureau|registry|gene\s+bank|deposit)\b", ln, re.I) and len(ln) < 300:
            out["outputVenue"] = ln[:300]
            break
    return out


_CITATION_TITLE_LABELS = (
    r"cited\s+work\s*:?",
    r"title\s+of\s+cited\s+work\s*:?",
    r"work\s+cited\s*:?",
    r"cited\s+publication\s*:?",
)
_CITATION_CONTEXT_LABELS = (
    r"citation\s+context",
    r"citing\s+publication",
    r"cited\s+in",
    r"source\s+of\s+citation",
    r"citation\s+details",
)
_CREATIVE_TITLE_LABELS = (
    r"title\s+of\s+(?:the\s+)?(?:creative\s+)?work",
    r"creative\s+work\s+title",
    r"performance\s+title",
    r"title\s+of\s+(?:the\s+)?(?:performance|production|composition|exhibit)",
)
_CREATIVE_VENUE_LABELS = (
    r"exhibition\s+venue",
    r"venue",
    r"presented\s+at",
    r"organization",
    r"^venue\s*:?\s*$",
    r"^organization\s*:?\s*$",
)
_CREATIVE_DATE_LABELS = (
    r"performance\s+date",
    r"exhibition\s+date",
    r"date\s+of\s+(?:the\s+)?performance",
    r"event\s+date",
)
_PERFORMANCE_TITLE_LABELS = (
    r"title\s+of\s+(?:the\s+)?(?:play|production|performance|show|musical)",
    r"(?:play|production|performance|show)\s+title",
    r"production\s+name",
    r"character\s+portrayed",
)
_PERFORMANCE_VENUE_LABELS = (
    r"performance\s+venue",
    r"theater",
    r"theatre",
    r"organizer",
    r"invited\s+by",
    r"presented\s+at",
)


_LITERARY_TITLE_LABELS = (
    r"title\s+of\s+(?:the\s+)?(?:work|book|novel|story|poem|essay|literary)",
    r"literary\s+work",
    r"book\s+title",
)
_LITERARY_AUTHOR_LABELS = (r"author\s*\(?s?\)?", r"writer", r"by\s*:")
_LITERARY_PUBLISHER_LABELS = (r"publisher", r"publication", r"published\s+by", r"press")

_FILM_TITLE_LABELS = (r"film\s+title", r"title\s+of\s+(?:the\s+)?film", r"motion\s+picture")
_FILM_DIRECTOR_LABELS = (r"director", r"created\s+by", r"filmmaker")
_FILM_VENUE_LABELS = (r"festival", r"screening", r"venue", r"cinematheque", r"organizer")

_EXHIBITION_TITLE_LABELS = (r"title\s+of\s+(?:the\s+)?(?:artwork|work|piece|design|project)", r"exhibition")
_EXHIBITION_ARTIST_LABELS = (r"artist", r"creator", r"designer", r"architect")
_EXHIBITION_VENUE_LABELS = (r"gallery", r"museum", r"exhibition\s+venue", r"exhibited\s+at", r"venue")

_MUSIC_WORK_TITLE_LABELS = (
    r"title\s+of\s+(?:the\s+)?(?:composition|arrangement|work|piece|production)",
    r"composition",
    r"arrangement",
)
_MUSIC_CREATOR_LABELS = (r"composer", r"arranger", r"producer", r"music\s+by")


def _parse_literary(text: str, indicator_id: str = "") -> dict[str, str]:
    lines = [ln.strip() for ln in (text or "").splitlines() if ln.strip()]
    out: dict[str, str] = {}
    title = _line_after_label(
        lines, _LITERARY_TITLE_LABELS + _CREATIVE_TITLE_LABELS + _TITLE_LABELS, field_id="outputTitle"
    )
    if title and not _is_disclaimer_title(title) and not is_metadata_label_value(title, field_id="outputTitle"):
        cleaned, status = validate_extracted_field("outputTitle", title, indicator_id)
        if cleaned and status != "rejected":
            out["outputTitle"] = cleaned
    author = _line_after_label(lines, _LITERARY_AUTHOR_LABELS + _AUTHOR_LABELS, field_id="authorsLine") or _names_after_label(
        lines, _AUTHOR_LABELS
    )
    if author and not is_metadata_label_value(author, field_id="authorsLine"):
        out["authorsLine"] = (_normalize_inventor_line(author) or author)[:300]
    venue = _line_after_label(lines, _LITERARY_PUBLISHER_LABELS + _PUBLISHER_LABELS, field_id="outputVenue")
    if venue and not is_metadata_label_value(venue, field_id="outputVenue"):
        out["outputVenue"] = venue[:300]
    date_val = _line_after_label(
        lines, _PUBLICATION_DATE_LABELS + _CREATIVE_DATE_LABELS + _DATE_LABELS, field_id="publicationDate"
    )
    if not date_val or not _value_looks_like_date(date_val):
        date_val = _first_date(text)
    if date_val:
        out["publicationDate"] = date_val
    return out


def _parse_film(text: str, indicator_id: str = "") -> dict[str, str]:
    lines = [ln.strip() for ln in (text or "").splitlines() if ln.strip()]
    out: dict[str, str] = {}
    title = _line_after_label(lines, _FILM_TITLE_LABELS + _CREATIVE_TITLE_LABELS + _TITLE_LABELS, field_id="outputTitle")
    if title and not _is_disclaimer_title(title) and not is_metadata_label_value(title, field_id="outputTitle"):
        cleaned, status = validate_extracted_field("outputTitle", title, indicator_id)
        if cleaned and status != "rejected":
            out["outputTitle"] = cleaned
    director = _line_after_label(lines, _FILM_DIRECTOR_LABELS + _AUTHOR_LABELS, field_id="authorsLine") or _names_after_label(
        lines, _FILM_DIRECTOR_LABELS
    )
    if director and not is_metadata_label_value(director, field_id="authorsLine"):
        out["authorsLine"] = (_normalize_inventor_line(director) or director)[:300]
    venue = _line_after_label(lines, _FILM_VENUE_LABELS + _CREATIVE_VENUE_LABELS, field_id="outputVenue")
    if venue and not is_metadata_label_value(venue, field_id="outputVenue"):
        out["outputVenue"] = venue[:300]
    date_val = _line_after_label(
        lines,
        (r"screening\s+date", r"release\s+date", r"premiere") + _CREATIVE_DATE_LABELS + _DATE_LABELS,
        field_id="publicationDate",
    )
    if not date_val or not _value_looks_like_date(date_val):
        date_val = _first_date(text)
    if date_val:
        out["publicationDate"] = date_val
    return out


def _parse_exhibition(text: str, indicator_id: str = "") -> dict[str, str]:
    lines = [ln.strip() for ln in (text or "").splitlines() if ln.strip()]
    out: dict[str, str] = {}
    title = _line_after_label(
        lines, _EXHIBITION_TITLE_LABELS + _CREATIVE_TITLE_LABELS + _TITLE_LABELS, field_id="outputTitle"
    )
    if title and not _is_disclaimer_title(title) and not is_metadata_label_value(title, field_id="outputTitle"):
        cleaned, status = validate_extracted_field("outputTitle", title, indicator_id)
        if cleaned and status != "rejected":
            out["outputTitle"] = cleaned
    artist = _line_after_label(lines, _EXHIBITION_ARTIST_LABELS + _AUTHOR_LABELS, field_id="authorsLine") or _names_after_label(
        lines, _EXHIBITION_ARTIST_LABELS
    )
    if artist and not is_metadata_label_value(artist, field_id="authorsLine"):
        out["authorsLine"] = (_normalize_inventor_line(artist) or artist)[:300]
    venue = _line_after_label(lines, _EXHIBITION_VENUE_LABELS + _CREATIVE_VENUE_LABELS, field_id="outputVenue")
    if venue and not is_metadata_label_value(venue, field_id="outputVenue"):
        out["outputVenue"] = venue[:300]
    date_val = _line_after_label(
        lines,
        (r"exhibition\s+date", r"opening\s+date") + _CREATIVE_DATE_LABELS + _DATE_LABELS,
        field_id="publicationDate",
    )
    if not date_val or not _value_looks_like_date(date_val):
        date_val = _first_date(text)
    if date_val:
        out["publicationDate"] = date_val
    return out


def _parse_music_work(text: str, indicator_id: str = "") -> dict[str, str]:
    lines = [ln.strip() for ln in (text or "").splitlines() if ln.strip()]
    out: dict[str, str] = {}
    title = _line_after_label(
        lines, _MUSIC_WORK_TITLE_LABELS + _CREATIVE_TITLE_LABELS + _TITLE_LABELS, field_id="outputTitle"
    )
    if title and not _is_disclaimer_title(title) and not is_metadata_label_value(title, field_id="outputTitle"):
        cleaned, status = validate_extracted_field("outputTitle", title, indicator_id)
        if cleaned and status != "rejected":
            out["outputTitle"] = cleaned
    creator = _line_after_label(lines, _MUSIC_CREATOR_LABELS + _AUTHOR_LABELS, field_id="authorsLine") or _names_after_label(
        lines, _MUSIC_CREATOR_LABELS
    )
    if creator and not is_metadata_label_value(creator, field_id="authorsLine"):
        out["authorsLine"] = (_normalize_inventor_line(creator) or creator)[:300]
    venue = _line_after_label(
        lines, _CREATIVE_VENUE_LABELS + _PUBLISHER_LABELS + _PERFORMANCE_VENUE_LABELS, field_id="outputVenue"
    )
    if venue and not is_metadata_label_value(venue, field_id="outputVenue"):
        out["outputVenue"] = venue[:300]
    date_val = _line_after_label(
        lines, _CREATIVE_DATE_LABELS + _PUBLICATION_DATE_LABELS + _DATE_LABELS, field_id="publicationDate"
    )
    if not date_val or not _value_looks_like_date(date_val):
        date_val = _first_date(text)
    if date_val:
        out["publicationDate"] = date_val
    return out


def _parse_performance(text: str, indicator_id: str = "") -> dict[str, str]:
    """Performing arts — acting, directing, music/dance performance, conducting."""
    lines = [ln.strip() for ln in (text or "").splitlines() if ln.strip()]
    out: dict[str, str] = {}
    title = _line_after_label(
        lines,
        _PERFORMANCE_TITLE_LABELS + _CREATIVE_TITLE_LABELS + _WORK_TITLE_LABELS + _TITLE_LABELS,
        field_id="outputTitle",
    )
    if title and not _is_disclaimer_title(title) and not is_metadata_label_value(title, field_id="outputTitle"):
        cleaned, status = validate_extracted_field("outputTitle", title, indicator_id)
        if cleaned and status != "rejected":
            out["outputTitle"] = cleaned
    performers = (
        _line_after_label(lines, (r"performer\s*\(?s?\)?", r"actor\s*\(?s?\)?", r"cast"), field_id="authorsLine")
        or _line_after_label(lines, _AUTHOR_LABELS, field_id="authorsLine")
        or _names_after_label(lines, _AUTHOR_LABELS)
    )
    if performers and not is_metadata_label_value(performers, field_id="authorsLine"):
        out["authorsLine"] = (_normalize_inventor_line(performers) or performers)[:300]
    venue = _line_after_label(
        lines,
        _PERFORMANCE_VENUE_LABELS + _CREATIVE_VENUE_LABELS + _JOURNAL_LABELS,
        field_id="outputVenue",
    )
    if venue and not is_metadata_label_value(venue, field_id="outputVenue"):
        out["outputVenue"] = venue[:300]
    date_val = _line_after_label(
        lines, _CREATIVE_DATE_LABELS + _PUBLICATION_DATE_LABELS + _DATE_LABELS, field_id="publicationDate"
    )
    if not date_val or not _value_looks_like_date(date_val):
        date_val = _first_date(text)
    if date_val:
        out["publicationDate"] = date_val
    return out


def _parse_citation(text: str, indicator_id: str = "") -> dict[str, str]:
    lines = [ln.strip() for ln in (text or "").splitlines() if ln.strip()]
    out: dict[str, str] = {}
    title = _line_after_label(lines, _CITATION_TITLE_LABELS, field_id="outputTitle") or _guess_title_line(lines)
    if title and not is_metadata_label_value(title, field_id="outputTitle"):
        out["outputTitle"] = title
    ctx = _line_after_label(lines, _CITATION_CONTEXT_LABELS, field_id="citationContext")
    if ctx and not is_metadata_label_value(ctx, field_id="citationContext"):
        out["citationContext"] = ctx[:400]
    else:
        for ln in lines[:40]:
            if _is_disclaimer_or_banner_line(ln):
                continue
            if re.search(r"\bcit(?:ed|ing|ation)\b", ln, re.I) and len(ln) < 400:
                if not is_metadata_label_value(ln, field_id="citationContext"):
                    out["citationContext"] = ln[:400]
                break
    date_val = _line_after_label(lines, _PUBLICATION_DATE_LABELS + _DATE_LABELS, field_id="publicationDate")
    if not date_val or not _value_looks_like_date(date_val):
        date_val = _first_date(text)
    if date_val:
        out["publicationDate"] = date_val
    ref_line = _line_after_label(lines, _REFERENCE_LABELS, field_id="publicationReference")
    doi = _first_doi(text)
    if ref_line and not is_metadata_label_value(ref_line, field_id="publicationReference"):
        out["publicationReference"] = ref_line[:200]
    elif doi:
        out["publicationReference"] = doi
    return out


def _parse_creative(text: str, indicator_id: str = "") -> dict[str, str]:
    lines = [ln.strip() for ln in (text or "").splitlines() if ln.strip()]
    out: dict[str, str] = {}
    title = _line_after_label(
        lines, _CREATIVE_TITLE_LABELS + _WORK_TITLE_LABELS + _TITLE_LABELS, field_id="outputTitle"
    )
    if title and not _is_disclaimer_title(title) and not is_metadata_label_value(title, field_id="outputTitle"):
        cleaned, status = validate_extracted_field("outputTitle", title, indicator_id)
        if cleaned and status != "rejected":
            out["outputTitle"] = cleaned
    raw_creators = _line_after_label(lines, _AUTHOR_LABELS, field_id="authorsLine") or _names_after_label(
        lines, _AUTHOR_LABELS
    )
    if raw_creators and not is_metadata_label_value(raw_creators, field_id="authorsLine"):
        out["authorsLine"] = (_normalize_inventor_line(raw_creators) or raw_creators)[:300]
    venue = _line_after_label(
        lines,
        _CREATIVE_VENUE_LABELS + _JOURNAL_LABELS + _PUBLISHER_LABELS,
        field_id="outputVenue",
    )
    if venue and not is_metadata_label_value(venue, field_id="outputVenue"):
        out["outputVenue"] = venue[:300]
    date_val = _line_after_label(
        lines, _CREATIVE_DATE_LABELS + _PUBLICATION_DATE_LABELS + _DATE_LABELS, field_id="publicationDate"
    )
    if not date_val or not _value_looks_like_date(date_val):
        date_val = _first_date(text)
    if date_val:
        out["publicationDate"] = date_val
    ref_line = _line_after_label(lines, _REFERENCE_LABELS, field_id="publicationReference")
    if ref_line and not is_metadata_label_value(ref_line, field_id="publicationReference"):
        out["publicationReference"] = ref_line[:200]
    return out


def extract_fields_for_indicator(text: str, indicator_id: str) -> dict[str, str]:
    from documents.kra2_evidence.ocr_profiles import filter_extracted_fields
    from documents.kra2_evidence.text_normalize import normalize_document_text

    text = normalize_document_text(text or "")
    family = workflow_family(indicator_id)
    if family == FAMILY_CITATION:
        raw = _parse_citation(text, indicator_id)
    elif family == FAMILY_INVENTION:
        iid = (indicator_id or "").casefold()
        if iid.startswith("kra2-b-sw-"):
            raw = _parse_software(text, indicator_id)
        elif "variety" in iid:
            raw = _parse_variety(text, indicator_id)
        else:
            raw = _parse_invention(text, indicator_id)
    elif family == FAMILY_COMMERCIAL:
        raw = _parse_invention(text, indicator_id)
        if "outputVenue" not in raw:
            for ln in (text or "").splitlines():
                if re.search(r"\bcommercial|market|license\b", ln, re.I):
                    candidate = ln.strip()[:300]
                    if not is_metadata_label_value(candidate, field_id="outputVenue"):
                        raw["outputVenue"] = candidate
                    break
    else:
        from kra_configuration.kra2_c_workflow import criterion_c_ocr_parser_id, is_criterion_c_indicator

        if is_criterion_c_indicator(indicator_id):
            route = criterion_c_ocr_parser_id(indicator_id)
            if route == "literary":
                raw = _parse_literary(text, indicator_id)
            elif route == "film":
                raw = _parse_film(text, indicator_id)
            elif route == "exhibition":
                raw = _parse_exhibition(text, indicator_id)
            elif route == "music_work":
                raw = _parse_music_work(text, indicator_id)
            elif route == "performance":
                raw = _parse_performance(text, indicator_id)
            else:
                raw = _parse_creative(text, indicator_id)
        elif family == FAMILY_PERFORMANCE:
            raw = _parse_performance(text, indicator_id)
        elif family == FAMILY_CREATIVE:
            raw = _parse_creative(text, indicator_id)
        else:
            raw = _parse_publication(text, indicator_id)
    _merge_contribution_annex_hints(raw, text, indicator_id)
    return filter_extracted_fields(raw, indicator_id)


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


def _bundle_value_replaceable(key: str, current: str, bundle: dict[str, Any]) -> bool:
    cur = (current or "").strip()
    if not cur:
        return True
    if key == "outputTitle" and _is_placeholder_title(bundle, cur):
        return True
    if is_metadata_label_value(cur, field_id=key):
        return True
    if key in ("publicationDate", "registrationDate") and not _value_looks_like_date(cur):
        return True
    if key == "registrationNumber" and not _is_plausible_registration_number(cur):
        return True
    return False


def _is_placeholder_title(bundle: dict[str, Any], current: str) -> bool:
    cur = (current or "").strip()
    if not cur:
        return True
    if is_metadata_label_value(cur, field_id="outputTitle"):
        return True
    if re.match(r"^/?\s*invention\b", cur, re.I):
        return True
    if _is_disclaimer_title(cur):
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
    indicator_id = (bundle.get("indicatorId") or "").strip()
    invention_only_keys = frozenset({"registrationNumber", "registrationDate"})
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
    from kra_configuration.kra2_annex import criterion_id_for_indicator

    crit = criterion_id_for_indicator(indicator_id) if indicator_id else None
    for key in merge_keys:
        if key in invention_only_keys and crit == "kra2-c":
            continue
        if confirmed.get(key):
            continue
        block = fields.get(key) if isinstance(fields.get(key), dict) else {}
        if (block.get("status") or "").strip().lower() == "rejected":
            continue
        val = (block.get("value") or "").strip()
        if not val:
            continue
        current = (bundle.get(key) or "").strip()
        if current and not _bundle_value_replaceable(key, current, bundle):
            continue
        if key in ("registrationDate", "publicationDate") and current and _value_looks_like_date(current):
            if not _is_year_only_date(current) or _is_year_only_date(val):
                if not _bundle_value_replaceable(key, current, bundle):
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
