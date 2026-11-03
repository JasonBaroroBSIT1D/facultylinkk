"""Shared Criterion C research metadata helpers (OCR + bundle display)."""

from __future__ import annotations

import re

_REJECT_TITLE_PATTERNS = (
    re.compile(r"signed\s+approval\s+sheet", re.I),
    re.compile(r"\bapproval\s+sheet\b", re.I),
    re.compile(r"\bsample\b", re.I),
    re.compile(r"^\d{1,3}[\s._-]+(?:signed|approval|sheet)", re.I),
    re.compile(r"\.(pdf|docx?|png|jpe?g|webp|tif{1,2})\b", re.I),
    re.compile(r"^(?:scan|document|file|upload)[\s_-]", re.I),
)

def is_unreliable_research_title(value: str | None) -> bool:
    """True when value is likely a filename, form heading, or placeholder — not a thesis title."""
    text = (value or "").strip()
    if not text or len(text) < 4:
        return True
    lower = text.lower()
    for pat in _REJECT_TITLE_PATTERNS:
        if pat.search(text):
            return True
    if lower in ("title", "project title", "thesis title", "research title", "n/a", "na", "tbd"):
        return True
    # Underscore-heavy upload names with few spaces.
    if text.count("_") >= 2 and text.count(" ") <= 1:
        return True
    return False


def normalize_academic_year(raw: str | None) -> str | None:
    if not raw:
        return None
    text = re.sub(r"\s+", "", (raw or "").strip())
    m = re.match(r"^(\d{4})[-–/](\d{2,4})$", text)
    if not m:
        return raw.strip()
    start = int(m.group(1))
    end_raw = m.group(2)
    end = int(end_raw)
    if len(end_raw) == 2:
        century = start // 100 * 100
        end = century + end if end >= (start % 100) else century + 100 + end
    return f"{start}-{end}"
