"""Official faculty rank ordering and sub-rank increment application (simulation only)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

# Canonical simulation ladder (sub-ranks within each category, then category transitions).
RANK_LADDER: tuple[str, ...] = (
    "Instructor I",
    "Instructor II",
    "Instructor III",
    "Assistant Professor I",
    "Assistant Professor II",
    "Assistant Professor III",
    "Assistant Professor IV",
    "Associate Professor I",
    "Associate Professor II",
    "Associate Professor III",
    "Associate Professor IV",
    "Associate Professor V",
    "Professor I",
    "Professor II",
    "Professor III",
    "Professor IV",
    "Professor V",
    "Professor VI",
    "College/University Professor",
)

_CATEGORY_BY_INDEX: list[str] = []
for _label in RANK_LADDER:
    if _label.startswith("Instructor"):
        _CATEGORY_BY_INDEX.append("Instructor")
    elif _label.startswith("Assistant"):
        _CATEGORY_BY_INDEX.append("Assistant Professor")
    elif _label.startswith("Associate"):
        _CATEGORY_BY_INDEX.append("Associate Professor")
    elif _label.startswith("Professor"):
        _CATEGORY_BY_INDEX.append("Professor")
    else:
        _CATEGORY_BY_INDEX.append("College/University Professor")

_ROMAN = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6}


def _normalize_rank_text(rank: str | None) -> str:
    text = (rank or "").strip()
    if not text:
        return ""
    lowered = text.lower()
    if "college" in lowered or "university professor" in lowered or "col./univ" in lowered:
        return "College/University Professor"
    # Unify "Asst." → "Assistant"
    text = re.sub(r"\basst\.?\s*", "Assistant ", text, flags=re.I)
    text = re.sub(r"\bassoc\.?\s*", "Associate ", text, flags=re.I)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _ladder_index(normalized: str) -> int | None:
    if not normalized:
        return None
    if normalized == "College/University Professor":
        return len(RANK_LADDER) - 1
    for i, canonical in enumerate(RANK_LADDER):
        if normalized.casefold() == canonical.casefold():
            return i
    # Fuzzy: category + roman numeral
    m = re.match(
        r"^(Instructor|Assistant Professor|Associate Professor|Professor)\s+([IVXLC]+)$",
        normalized,
        re.I,
    )
    if m:
        cat = m.group(1).title()
        if cat == "Professor":
            cat = "Professor"
        roman = m.group(2).upper()
        target = f"{cat} {roman}"
        for i, canonical in enumerate(RANK_LADDER):
            if canonical.casefold() == target.casefold():
                return i
    return None


@dataclass
class RankIncrementResult:
    possible_rank: str | None
    subrank_increment_requested: int
    subrank_increment_applied: int
    rank_transition_blocked: bool
    rank_transition_note: str | None
    current_rank_recognized: bool


def category_transition_allowed(
    from_category: str,
    to_category: str,
    transition_rules: dict[str, Any] | None,
) -> bool:
    if from_category == to_category:
        return True
    if not transition_rules or not isinstance(transition_rules, dict):
        return False
    allowed = transition_rules.get("allowedCategoryTransitions")
    if isinstance(allowed, list):
        pair = f"{from_category}->{to_category}"
        return pair in allowed or {"from": from_category, "to": to_category} in allowed
    by_from = transition_rules.get(from_category)
    if isinstance(by_from, list):
        return to_category in by_from
    return bool(transition_rules.get("allowAllCategoryTransitions") is True)


def apply_subrank_increment(
    current_rank: str | None,
    increment: int,
    *,
    transition_rules: dict[str, Any] | None = None,
) -> RankIncrementResult:
    normalized = _normalize_rank_text(current_rank)
    idx = _ladder_index(normalized)
    if idx is None:
        return RankIncrementResult(
            possible_rank=None,
            subrank_increment_requested=max(0, increment),
            subrank_increment_applied=0,
            rank_transition_blocked=True,
            rank_transition_note="Current rank is not recognized on the official simulation ladder.",
            current_rank_recognized=False,
        )

    if increment <= 0:
        return RankIncrementResult(
            possible_rank=RANK_LADDER[idx],
            subrank_increment_requested=0,
            subrank_increment_applied=0,
            rank_transition_blocked=False,
            rank_transition_note=None,
            current_rank_recognized=True,
        )

    applied = 0
    remaining = increment
    cursor = idx
    blocked = False
    note: str | None = None

    while remaining > 0 and cursor < len(RANK_LADDER) - 1:
        next_idx = cursor + 1
        from_cat = _CATEGORY_BY_INDEX[cursor]
        to_cat = _CATEGORY_BY_INDEX[next_idx]
        if from_cat != to_cat and not category_transition_allowed(from_cat, to_cat, transition_rules):
            blocked = True
            note = (
                f"{remaining} sub-rank increment(s) could not be applied — "
                f"rank category transition ({from_cat} → {to_cat}) is not configured as permitted."
            )
            break
        cursor = next_idx
        applied += 1
        remaining -= 1

    if remaining > 0 and cursor >= len(RANK_LADDER) - 1 and not note:
        note = "Maximum rank on the simulation ladder reached."

    if applied > 0:
        possible = RANK_LADDER[cursor]
    else:
        possible = None

    return RankIncrementResult(
        possible_rank=possible,
        subrank_increment_requested=increment,
        subrank_increment_applied=applied,
        rank_transition_blocked=blocked,
        rank_transition_note=note,
        current_rank_recognized=True,
    )
