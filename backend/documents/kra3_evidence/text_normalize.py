"""Normalize OCR / PDF text before KRA III field extraction."""

from __future__ import annotations

import re


def normalize_document_text(text: str) -> str:
    """Collapse noisy layout (tables, wraps, bullets) into line-oriented text."""
    if not text:
        return ""
    raw = text.replace("\r\n", "\n").replace("\r", "\n")
    raw = raw.replace("\u2013", "-").replace("\u2014", "-").replace("\u00a0", " ")
    lines: list[str] = []
    for ln in raw.split("\n"):
        stripped = ln.strip()
        if not stripped:
            lines.append("")
            continue
        if "|" in stripped:
            cells = [c.strip() for c in stripped.split("|") if c.strip()]
            if len(cells) >= 2 and all(len(c) < 120 for c in cells):
                for i in range(0, len(cells) - 1, 2):
                    lines.append(f"{cells[i]}: {cells[i + 1]}")
                if len(cells) % 2 == 1:
                    lines.append(cells[-1])
                continue
        if "\t" in stripped:
            parts = [p.strip() for p in stripped.split("\t") if p.strip()]
            if len(parts) == 2 and len(parts[0]) < 80:
                lines.append(f"{parts[0]}: {parts[1]}")
                continue
        merged = re.sub(r"\s{2,}", " ", stripped)
        lines.append(merged)
    return _merge_wrapped_label_lines("\n".join(lines))


def _merge_wrapped_label_lines(text: str) -> str:
    """Join hyphen-wrapped title lines only (do not merge label + value lines)."""
    out: list[str] = []
    for ln in text.split("\n"):
        if not ln.strip():
            out.append(ln)
            continue
        prev = out[-1].strip() if out else ""
        cur = ln.strip()
        if prev.endswith("-") and cur and cur[0].islower():
            out[-1] = prev.rstrip("-") + cur
        else:
            out.append(ln)
    return "\n".join(out)
