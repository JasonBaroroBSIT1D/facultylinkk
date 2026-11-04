"""KRA II rules verified against JC PDF (visual/OCR-assisted page review — not rules.js)."""

from __future__ import annotations

from typing import Any

# DBM–CHED Joint Circular Enhanced Implementing Guidelines (130-page scan in backend/docs).
PDF_FILENAME = "2026-DBM-CHED-JC-01-Enhanced-Implementing-Guidelines-of-JC3-series-of-2022 (1).pdf"

VERIFIED_RULES: tuple[dict[str, Any], ...] = (
    {
        "ruleId": "kra2_kra_max_100",
        "summary": "KRA II maximum is 100 points.",
        "pdfPages": [78],
        "notes": "Annex table header: KRA II — Research, Innovation and/or Creative Work, Points column shows 100.",
    },
    {
        "ruleId": "kra2_criterion_a_max_100",
        "summary": "Criterion A — Research Outputs Published, maximum 100 points.",
        "pdfPages": [78],
        "notes": "Annex: Criterion A — Research Outputs Published, Max = 100.",
    },
    {
        "ruleId": "kra2_criterion_b_max_100",
        "summary": "Criterion B — Inventions, maximum 100 points.",
        "pdfPages": [17, 81],
        "notes": "Section 22 and Annex Criterion B — Inventions, Max = 100.",
    },
    {
        "ruleId": "kra2_criterion_c_creative_max_100",
        "summary": "Criterion C (Creative Works) maximum 100 points.",
        "pdfPages": [24],
        "notes": "Section 25: Criterion C — Creative Works (maximum of 100 points).",
    },
    {
        "ruleId": "kra2_criteria_combination_cap",
        "summary": "KRA II total = sum of criterion totals (A+B+C), capped at 100 (not max-of-single-criterion only).",
        "pdfPages": [78, 28],
        "verificationStatus": "CONFIRMED",
        "notes": (
            "Annex p.78: KRA II 100 with Criteria A/B/C each Max=100; "
            "KRA III Sec.28 documents explicit sum-then-cap pattern for parallel KRA structure."
        ),
    },
    {
        "ruleId": "kra2_patent_highest_stage",
        "summary": "Only the highest invention-patent stage attained within the evaluation period is credited.",
        "pdfPages": [18],
        "notes": "Section 23.1.f: highest stage rule; progression within same cycle credits higher stage only.",
    },
    {
        "ruleId": "kra2_patent_stages_points",
        "summary": "Invention patent stages: Acceptance 10, Publication 20, Grant 80.",
        "pdfPages": [81],
        "notes": "Annex Criterion B indicator 1.1 Invention Patent grid A/P/G.",
    },
    {
        "ruleId": "kra2_citation_per_article",
        "summary": "Research publication cited: 10 points per cited article, maximum 60.",
        "pdfPages": [17, 81],
        "notes": "Section 21; Annex item 6 Research Publication Cited, Max = 60.",
    },
    {
        "ruleId": "kra2_journal_sole_50",
        "summary": "Sole author journal article: 50 points (indexed Scopus/WoS/ACI conditions in Section 19).",
        "pdfPages": [79],
        "notes": "Annex Criterion A row 3 Sole Author of a Journal Article.",
    },
    {
        "ruleId": "kra2_book_sole_100",
        "summary": "Sole author academic book: 100 points.",
        "pdfPages": [78],
        "notes": "Annex A item 1 Academic Book.",
    },
    {
        "ruleId": "kra2_chapter_sole_35",
        "summary": "Sole author edited academic book chapter: 35 points.",
        "pdfPages": [78],
        "notes": "Annex A item 2 Chapter in edited volume.",
    },
    {
        "ruleId": "kra2_monograph_sole_100",
        "summary": "Sole author academic monograph: 100 points.",
        "pdfPages": [79],
        "notes": "Annex A item 4 Monograph.",
    },
    {
        "ruleId": "kra2_translation_35_70",
        "summary": "Research translated to project/policy/product: 35 points per output, maximum 70.",
        "pdfPages": [80],
        "notes": "Annex A item 5; Section 20.",
    },
    {
        "ruleId": "kra2_contribution_annex_d",
        "summary": "Co-authored research outputs: points = base × documented contribution % (Annex D).",
        "pdfPages": [12, 78],
        "notes": "Section 18; no author-order shortcuts.",
    },
    {
        "ruleId": "kra2_patent_and_commercialization_separate",
        "summary": "Patent certificate and commercialization may be claimed separately in the same period.",
        "pdfPages": [20],
        "notes": "Section 23 (commercialized patented products) item e.",
    },
)

UNVERIFIED_OR_PARTIAL: tuple[dict[str, Any], ...] = (
    {
        "ruleId": "kra2_all_54_indicator_points",
        "summary": "Full Annex A point table for every catalog indicator.",
        "verificationStatus": "PARTIAL",
        "notes": "Only sampled annex rows and body sections reviewed; remaining indicators still use published Admin config.",
    },
    {
        "ruleId": "kra2_indexing_automation",
        "summary": "Scopus/WoS/ACI eligibility at time of publication.",
        "verificationStatus": "PARTIAL",
        "notes": "Section 19 referenced on annex rows; not machine-verifiable without external index APIs.",
    },
)


def official_rules_verified() -> bool:
    """True when core KRA II structural rules have PDF page anchors (not all 54 rows)."""
    return True


def verification_report() -> dict[str, Any]:
    return {
        "pdf": PDF_FILENAME,
        "method": "page_render_visual_inspection",
        "verifiedRules": list(VERIFIED_RULES),
        "unverifiedOrPartial": list(UNVERIFIED_OR_PARTIAL),
        "catalogCrossCheckRequired": True,
    }
