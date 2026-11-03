# KRA II — JC PDF verification notes

**Document:** `backend/docs/2026-DBM-CHED-JC-01-Enhanced-Implementing-Guidelines-of-JC3-series-of-2022 (1).pdf` (130 pages, scanned).

**Method:** PyMuPDF page render + visual inspection (Tesseract not installed on dev host). Sample renders saved under `backend/docs/pdf_render_kra2/` for audit.

## Verified rules (with PDF page numbers)

| Topic | Page(s) | Implementation |
|---|---|---|
| KRA II max 100 | 78 (Annex header) | `aggregate_kra2_kra_from_documents` caps sum of A+B+C at published KRA max |
| Criterion A max 100 | 78 | `aggregate_kra2_criterion_from_documents` |
| Criterion B max 100 | 17, 81 | Same |
| Criterion C (Creative Works) max 100 | 24 | Same (catalog maps creative/performance under `kra2-c`) |
| Journal article sole 50 pts | 79 | Published Admin indicator points |
| Citation 10 / max 60 | 17, 81 | `group_caps` + catalog `groupMax` |
| Patent stages A=10, P=20, G=80 | 81 | Published Admin indicator points |
| **Highest patent stage only** | **18 (Sec. 23.1.f)** | `patent_deduplication.apply_patent_highest_stage_only` |
| Patent + commercialization separate same period | 20 | Allowed as separate indicators (no stage dedup across comm) |
| Co-inventor % (Annex F) | 18–19 | `declaredContributionPercent` on bundle |

## Per-indicator verification (54)

Regenerate: `python backend/scripts/build_kra2_indicator_verification_report.py`

Latest automated cross-check (catalog vs annex page map):

- **32** `VERIFIED_POINTS`
- **22** `PARTIAL` (co-author / journal / citation eligibility)
- **0** `MISMATCH`

See [`KRA2_INDICATOR_VERIFICATION_REPORT.md`](KRA2_INDICATOR_VERIFICATION_REPORT.md).

## KRA II aggregation formula (confirmed)

`kra2_total = min(criterion_a + criterion_b + criterion_c, 100)` with each criterion capped at 100 first. Implemented in `aggregate_kra2_kra_from_documents`. Not `max(A,B,C)` only.

## Still reviewer-gated / not machine-verified

- Indexing (Scopus/WoS/ACI) at publication date (Sec. 19–21).
- Student co-authorship institutional policy (Sec. 18).
- Self-citation exclusion (Sec. 21).

## Machine-readable registry

- `backend/kra_configuration/kra2_official_verification.py`
- `backend/kra_configuration/kra2_indicator_pdf_verification.py`

**Do not treat `web/js/rules.js` as official proof** — use PDF page citations in the verification report.
