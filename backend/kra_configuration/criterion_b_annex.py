"""KRA I Criterion B — map ten FacultyLink indicator IDs to six Annex A scoring rows (JC 01 s. 2026)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

CRITERION_B_ID: Final[str] = "kra1-b"
KRA1_ID: Final[str] = "kra1"

# All ten legacy indicator IDs (upload, Admin, Reviewer, Flutter).
CRITERION_B_INDICATOR_IDS: Final[frozenset[str]] = frozenset(
    {
        "kra1-b-textbook-sole",
        "kra1-b-textbook-co",
        "kra1-b-module-sole",
        "kra1-b-module-co",
        "kra1-b-manual-sole",
        "kra1-b-manual-co",
        "kra1-b-multimedia-sole",
        "kra1-b-multimedia-co",
        "kra1-b-program-lead",
        "kra1-b-program-contributor",
    }
)


@dataclass(frozen=True)
class CriterionBAnnexRow:
    """One official Annex A scoring line under Criterion B (Instruction, Max 30)."""

    row_id: str
    annex_reference: str
    base_indicator_id: str
    co_indicator_id: str | None
    indicator_ids: tuple[str, ...]


# Base points are read from published Admin config using ``base_indicator_id`` only
# (co-author rows share the same annex base; no duplicate official allocations).
ANNEX_ROWS: Final[tuple[CriterionBAnnexRow, ...]] = (
    CriterionBAnnexRow(
        row_id="textbook",
        annex_reference="Annex A §1.1 Sole Author of a Textbook",
        base_indicator_id="kra1-b-textbook-sole",
        co_indicator_id="kra1-b-textbook-co",
        indicator_ids=("kra1-b-textbook-sole", "kra1-b-textbook-co"),
    ),
    CriterionBAnnexRow(
        row_id="module",
        annex_reference="Annex A §1.2 Sole Author of a Module",
        base_indicator_id="kra1-b-module-sole",
        co_indicator_id="kra1-b-module-co",
        indicator_ids=("kra1-b-module-sole", "kra1-b-module-co"),
    ),
    CriterionBAnnexRow(
        row_id="instructional_manual",
        annex_reference="Annex A §1.3 Sole Author of Instructional Manual",
        base_indicator_id="kra1-b-manual-sole",
        co_indicator_id="kra1-b-manual-co",
        indicator_ids=("kra1-b-manual-sole", "kra1-b-manual-co"),
    ),
    CriterionBAnnexRow(
        row_id="multimedia",
        annex_reference="Annex A §1.4 Sole Author of Multimedia Teaching Materials",
        base_indicator_id="kra1-b-multimedia-sole",
        co_indicator_id="kra1-b-multimedia-co",
        indicator_ids=("kra1-b-multimedia-sole", "kra1-b-multimedia-co"),
    ),
    CriterionBAnnexRow(
        row_id="program_lead",
        annex_reference="Annex A §2.1 Academic Program — Lead",
        base_indicator_id="kra1-b-program-lead",
        co_indicator_id=None,
        indicator_ids=("kra1-b-program-lead",),
    ),
    CriterionBAnnexRow(
        row_id="program_contributor",
        annex_reference="Annex A §2.2 Academic Program — Contributor",
        base_indicator_id="kra1-b-program-contributor",
        co_indicator_id=None,
        indicator_ids=("kra1-b-program-contributor",),
    ),
)

_INDICATOR_TO_ROW: Final[dict[str, CriterionBAnnexRow]] = {
    ind: row for row in ANNEX_ROWS for ind in row.indicator_ids
}


def is_criterion_b_indicator(indicator_id: str | None) -> bool:
    return bool(indicator_id and indicator_id.strip() in CRITERION_B_INDICATOR_IDS)


def annex_row_for_indicator(indicator_id: str | None) -> CriterionBAnnexRow | None:
    if not indicator_id:
        return None
    return _INDICATOR_TO_ROW.get(indicator_id.strip())


def indicator_requires_contribution_percent(indicator_id: str | None) -> bool:
    """Co-author instructional material rows (Annex C contribution), not program roles."""
    row = annex_row_for_indicator(indicator_id)
    if not row or not row.co_indicator_id:
        return False
    return (indicator_id or "").strip() == row.co_indicator_id


def is_instructional_material_indicator(indicator_id: str | None) -> bool:
    row = annex_row_for_indicator(indicator_id)
    if not row:
        return False
    return row.row_id not in ("program_lead", "program_contributor")


PROGRAM_LEAD_INDICATOR: Final[str] = "kra1-b-program-lead"
PROGRAM_CONTRIBUTOR_INDICATOR: Final[str] = "kra1-b-program-contributor"
ACADEMIC_PROGRAM_INDICATOR_IDS: Final[frozenset[str]] = frozenset(
    {PROGRAM_LEAD_INDICATOR, PROGRAM_CONTRIBUTOR_INDICATOR}
)


def is_academic_program_indicator(indicator_id: str | None) -> bool:
    return bool(indicator_id and indicator_id.strip() in ACADEMIC_PROGRAM_INDICATOR_IDS)


def faculty_role_for_program_indicator(indicator_id: str | None) -> str | None:
    """Return ``lead`` or ``contributor`` for program indicators."""
    ind = (indicator_id or "").strip()
    if ind == PROGRAM_LEAD_INDICATOR:
        return "lead"
    if ind == PROGRAM_CONTRIBUTOR_INDICATOR:
        return "contributor"
    return None
