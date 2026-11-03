"""Per-indicator JC PDF verification registry (annex pages 78–92 visual cross-check)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_DATA = Path(__file__).resolve().parent / "data" / "kra2_indicators.json"

# Base points / caps from annex table (PDF page). Co-* rows inherit same base; contribution via Annex D/F/G/H/I.
_PDF_ANNEX: dict[str, dict[str, Any]] = {
    "kra2-a-book-sole": {"pdfPages": [78], "basePoints": 100, "maxPoints": 100, "formula": "fixed", "annex": "A.1 Academic Book"},
    "kra2-a-book-co": {"pdfPages": [78, 12], "basePoints": 100, "maxPoints": 100, "formula": "percent × base", "annex": "A.1 + Annex D"},
    "kra2-a-chapter-sole": {"pdfPages": [78], "basePoints": 35, "maxPoints": 35, "formula": "fixed", "annex": "A.2 Chapter"},
    "kra2-a-chapter-co": {"pdfPages": [78, 12], "basePoints": 35, "maxPoints": 35, "formula": "percent × base", "annex": "A.2 + Annex D"},
    "kra2-a-journal-sole": {"pdfPages": [79], "basePoints": 50, "maxPoints": 50, "formula": "fixed", "annex": "A.3 Journal"},
    "kra2-a-journal-co": {"pdfPages": [79, 12], "basePoints": 50, "maxPoints": 50, "formula": "percent × base", "annex": "A.3 + Annex D"},
    "kra2-a-monograph-sole": {"pdfPages": [79], "basePoints": 100, "maxPoints": 100, "formula": "fixed", "annex": "A.4 Monograph"},
    "kra2-a-monograph-co": {"pdfPages": [79, 12], "basePoints": 100, "maxPoints": 100, "formula": "percent × base", "annex": "A.4 + Annex D"},
    "kra2-a-translation-sole": {"pdfPages": [80], "basePoints": 35, "maxPoints": 35, "formula": "fixed", "groupMax": 70, "annex": "A.5 Translation"},
    "kra2-a-translation-co": {"pdfPages": [80, 16], "basePoints": 35, "maxPoints": 35, "formula": "percent × base", "groupMax": 70, "annex": "A.5 + Annex E"},
    "kra2-a-cite": {"pdfPages": [17, 81], "basePoints": 10, "maxPoints": 10, "formula": "per cited article", "groupMax": 60, "annex": "A.6 Cited"},
    "kra2-b-patent-a-sole": {"pdfPages": [81, 18], "basePoints": 10, "maxPoints": 10, "formula": "stage A; highest stage only", "annex": "B.1.1 Patent A"},
    "kra2-b-patent-a-co": {"pdfPages": [81, 18, 19], "basePoints": 10, "maxPoints": 10, "formula": "percent × stage A", "annex": "B.1.1 + Annex F"},
    "kra2-b-patent-p-sole": {"pdfPages": [81, 18], "basePoints": 20, "maxPoints": 20, "formula": "stage P; highest stage only", "annex": "B.1.1 Patent P"},
    "kra2-b-patent-p-co": {"pdfPages": [81, 18, 19], "basePoints": 20, "maxPoints": 20, "formula": "percent × stage P", "annex": "B.1.1 + Annex F"},
    "kra2-b-patent-g-sole": {"pdfPages": [81, 18], "basePoints": 80, "maxPoints": 80, "formula": "stage G; highest stage only", "annex": "B.1.1 Patent G"},
    "kra2-b-patent-g-co": {"pdfPages": [81, 18, 19], "basePoints": 80, "maxPoints": 80, "formula": "percent × stage G", "annex": "B.1.1 + Annex F"},
    "kra2-b-comm-local": {"pdfPages": [20, 82], "basePoints": 5, "maxPoints": 5, "formula": "per product", "groupMax": 20, "annex": "B.1.2.1 Local"},
    "kra2-b-comm-intl": {"pdfPages": [20, 82], "basePoints": 10, "maxPoints": 10, "formula": "per product", "groupMax": 30, "annex": "B.1.2.2 International"},
    "kra2-b-um-sole": {"pdfPages": [82], "basePoints": 10, "maxPoints": 10, "formula": "fixed", "annex": "B.1.3.1 UM"},
    "kra2-b-um-co": {"pdfPages": [82, 19], "basePoints": 10, "maxPoints": 10, "formula": "percent × base", "annex": "B.1.3.1 + Annex F"},
    "kra2-b-id-sole": {"pdfPages": [82], "basePoints": 5, "maxPoints": 5, "formula": "fixed", "annex": "B.1.3.2 ID"},
    "kra2-b-id-co": {"pdfPages": [82, 19], "basePoints": 5, "maxPoints": 5, "formula": "percent × base", "annex": "B.1.3.2 + Annex F"},
    "kra2-b-sw-new-sole": {"pdfPages": [83], "basePoints": 10, "maxPoints": 10, "formula": "fixed", "annex": "B.2.1.1 New software"},
    "kra2-b-sw-new-co": {"pdfPages": [83], "basePoints": 10, "maxPoints": 10, "formula": "percent × base", "annex": "B.2.1.1 + Annex G"},
    "kra2-b-sw-upd-sole": {"pdfPages": [83], "basePoints": 4, "maxPoints": 4, "formula": "fixed", "annex": "B.2.1.2 Updated software"},
    "kra2-b-sw-upd-co": {"pdfPages": [83], "basePoints": 4, "maxPoints": 4, "formula": "percent × base", "annex": "B.2.1.2 + Annex G"},
    "kra2-b-variety-sole": {"pdfPages": [83, 84], "basePoints": 10, "maxPoints": 10, "formula": "fixed", "annex": "B.2.2 Variety/breed/strain"},
    "kra2-b-variety-co": {"pdfPages": [83, 84], "basePoints": 10, "maxPoints": 10, "formula": "percent × base", "annex": "B.2.2 + Annex H"},
    "kra2-c-music-comp-sole": {"pdfPages": [84, 85], "basePoints": 20, "maxPoints": 20, "formula": "fixed", "annex": "C.1.1.1.1 Composition"},
    "kra2-c-music-comp-co": {"pdfPages": [84, 85], "basePoints": 20, "maxPoints": 20, "formula": "percent × base", "annex": "C.1.1.1.1 + Annex I"},
    "kra2-c-music-arr-sole": {"pdfPages": [85], "basePoints": 20, "maxPoints": 20, "formula": "fixed", "annex": "C.1.1.1.2 Arrangement"},
    "kra2-c-music-arr-co": {"pdfPages": [85], "basePoints": 20, "maxPoints": 20, "formula": "percent × base", "annex": "C.1.1.1.2 + Annex I"},
    "kra2-c-music-perf": {"pdfPages": [86], "basePoints": 10, "maxPoints": 10, "formula": "fixed", "annex": "C.1.1.1.3 Performance"},
    "kra2-c-conducting": {"pdfPages": [86], "basePoints": 10, "maxPoints": 10, "formula": "fixed", "annex": "C.1.1.1.4 Conducting"},
    "kra2-c-music-prod-sole": {"pdfPages": [86], "basePoints": 20, "maxPoints": 20, "formula": "fixed", "annex": "C.1.1.1.5 Music production"},
    "kra2-c-music-prod-co": {"pdfPages": [86], "basePoints": 20, "maxPoints": 20, "formula": "percent × base", "annex": "C.1.1.1.5 + Annex I"},
    "kra2-c-choreo-sole": {"pdfPages": [87], "basePoints": 20, "maxPoints": 20, "formula": "fixed", "annex": "C.1.1.2 Choreography"},
    "kra2-c-choreo-co": {"pdfPages": [87], "basePoints": 20, "maxPoints": 20, "formula": "percent × base", "annex": "C.1.1.2 + Annex I"},
    "kra2-c-dance-perf": {"pdfPages": [87], "basePoints": 10, "maxPoints": 10, "formula": "fixed", "annex": "C.1.1.2 Dance performance"},
    "kra2-c-playwright-sole": {"pdfPages": [88], "basePoints": 20, "maxPoints": 20, "formula": "fixed", "annex": "C.1.1.3.1 Playwright"},
    "kra2-c-playwright-co": {"pdfPages": [88], "basePoints": 20, "maxPoints": 20, "formula": "percent × base", "annex": "C.1.1.3.1 + Annex I"},
    "kra2-c-directing": {"pdfPages": [88], "basePoints": 20, "maxPoints": 20, "formula": "fixed", "annex": "C.1.1.3.2 Directing"},
    "kra2-c-acting": {"pdfPages": [88], "basePoints": 20, "maxPoints": 20, "formula": "fixed", "annex": "C.1.1.3.3 Acting"},
    "kra2-c-prod-design": {"pdfPages": [88, 89], "basePoints": 20, "maxPoints": 20, "formula": "fixed", "annex": "C.1.1.3.4 Production design"},
    "kra2-c-visual": {"pdfPages": [89], "basePoints": 20, "maxPoints": 20, "formula": "fixed", "annex": "C.1.2 Visual arts"},
    "kra2-c-arch-design": {"pdfPages": [89], "basePoints": 20, "maxPoints": 20, "formula": "fixed", "annex": "C.1.2.7 Arch/interior"},
    "kra2-c-film": {"pdfPages": [90], "basePoints": 20, "maxPoints": 20, "formula": "fixed", "annex": "C.1.3 Film"},
    "kra2-c-novel-sole": {"pdfPages": [91], "basePoints": 20, "maxPoints": 20, "formula": "fixed", "annex": "C.1.4.1 Novel"},
    "kra2-c-novel-co": {"pdfPages": [91], "basePoints": 20, "maxPoints": 20, "formula": "percent × base", "annex": "C.1.4.1 + Annex I"},
    "kra2-c-story-sole": {"pdfPages": [91], "basePoints": 10, "maxPoints": 10, "formula": "fixed", "annex": "C.1.4.2 Short story"},
    "kra2-c-story-co": {"pdfPages": [91], "basePoints": 10, "maxPoints": 10, "formula": "percent × base", "annex": "C.1.4.2 + Annex I"},
    "kra2-c-poetry": {"pdfPages": [92], "basePoints": 2, "maxPoints": 2, "formula": "fixed", "annex": "C.1.4.3 Poetry"},
    "kra2-c-essay": {"pdfPages": [92], "basePoints": 2, "maxPoints": 2, "formula": "fixed", "annex": "C.1.4.4 Literary essay"},
}


def _load_catalog() -> list[dict[str, Any]]:
    raw = json.loads(_DATA.read_text(encoding="utf-8"))
    return list(raw.get("indicators") or [])


def indicator_verification_status(indicator_id: str) -> dict[str, Any]:
    row = next((r for r in _load_catalog() if r.get("id") == indicator_id), None)
    pdf = _PDF_ANNEX.get(indicator_id)
    if not row or not pdf:
        return {"id": indicator_id, "status": "NOT STARTED", "reason": "missing catalog or PDF map"}

    pts = float(row.get("points") or 0)
    mx = float(row.get("maxPoints") or 0)
    points_ok = abs(pts - float(pdf["basePoints"])) < 0.01
    per_output_max = float(pdf["maxPoints"])
    max_ok = abs(pts - per_output_max) < 0.01 or abs(mx - per_output_max) < 0.01
    group_ok = True
    if pdf.get("groupMax") is not None:
        effective_group = row.get("groupMax")
        if effective_group is None:
            effective_group = row.get("maxPoints")
        group_ok = float(effective_group or 0) == float(pdf["groupMax"])

    eligibility_partial = indicator_id.endswith("-co") or "cite" in indicator_id or "journal" in indicator_id

    if points_ok and max_ok and group_ok:
        status = "VERIFIED_POINTS" if not eligibility_partial else "PARTIAL"
    else:
        status = "MISMATCH"

    return {
        "id": indicator_id,
        "name": row.get("name"),
        "status": status,
        "catalogPoints": pts,
        "pdfBasePoints": pdf["basePoints"],
        "catalogMaxPoints": mx,
        "pdfMaxPoints": pdf["maxPoints"],
        "formula": pdf.get("formula"),
        "pdfPages": pdf.get("pdfPages"),
        "annexRef": pdf.get("annex"),
        "contribution": row.get("contribution"),
        "evidenceHints": row.get("evidenceHints"),
        "eligibilityNote": "Indexing/eligibility per Section 19–21; reviewer-gated"
        if eligibility_partial
        else None,
    }


def all_indicator_verifications() -> list[dict[str, Any]]:
    return [indicator_verification_status(r["id"]) for r in _load_catalog()]


def verification_summary() -> dict[str, Any]:
    rows = all_indicator_verifications()
    counts: dict[str, int] = {}
    for r in rows:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    return {
        "total": len(rows),
        "counts": counts,
        "verifiedPointsCount": counts.get("VERIFIED_POINTS", 0),
        "partialCount": counts.get("PARTIAL", 0),
        "mismatchCount": counts.get("MISMATCH", 0),
    }


KRA2_AGGREGATION_FORMULA = {
    "status": "CONFIRMED_IMPLEMENTATION",
    "formula": "kra2_total = min(criterion_a + criterion_b + criterion_c, 100)",
    "criterionFormula": "criterion_total = min(sum(eligible_accomplishments_after_dedup_and_group_caps), 100)",
    "pdfEvidence": [
        "Annex p.78: KRA II total 100; Criteria A/B/C each Max=100",
        "Sec. 28 (KRA III) explicit sum-then-cap pattern (parallel structure)",
        "Sec. 23.1.f p.18: patent highest stage within period",
    ],
    "notUsed": "max(criterion_a, criterion_b, criterion_c) alone",
    "implementation": "aggregate_kra2_kra_from_documents + aggregate_kra2_criterion_from_documents",
}
