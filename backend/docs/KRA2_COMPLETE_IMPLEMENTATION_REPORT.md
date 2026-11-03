# KRA II — Complete Implementation Report (Sprint Handoff)

**Date:** 2026-11-03 (Final verification & QA sprint)  
**Scope:** KRA II Criteria A, B, and C only (KRA III/IV out of scope).  
**Guideline:** DBM–CHED Joint Circular No. 01, s. 2026 — PDF at  
`backend/docs/2026-DBM-CHED-JC-01-Enhanced-Implementing-Guidelines-of-JC3-series-of-2022 (1).pdf` (130 pages).

---

## Executive summary

**KRA II is not COMPLETE end-to-end for all 54 indicators.** Core **scoring integrity** fixes are in place (PDF-anchored patent highest-stage dedup, criteria-sum KRA cap, legacy/bundle overlap guard). **Journal articles** remain the most exercised reference path. **All 54** catalog rows have registry/validation tests; **full annex row-by-row PDF proof** and **live QA per indicator family** are still outstanding.

| Area | Status |
|---|---|
| Official PDF cross-check | **PARTIAL** — visual page review + `KRA2_PDF_VERIFICATION_NOTES.md` (not full OCR of 130 pages) |
| Patent stage deduplication | **IMPLEMENTED** — Sec. 23.1.f (PDF p. 18); tests in `test_kra2_scoring_integrity.py` |
| KRA II aggregation (A+B+C → cap 100) | **IMPLEMENTED** — `aggregate_kra2_kra_from_documents`; rank sim uses bundle path for `kra2` |
| Backend validation / scoring | **PARTIAL** (published Admin points; group caps; reviewer-gated approval) |
| Faculty mobile / Reviewer web | **PARTIAL** (unchanged UX; three-step / three-section preserved) |
| Per-indicator E2E (all 54) | **NOT COMPLETE** |

Phase 1 deliverables (matrix, annex helpers, generator) remain valid. See §Phase 2 below.

---

## 1. Official scoring and evidence matrix

| Artifact | Location |
|---|---|
| Full indicator matrix (54 rows) | `backend/docs/KRA2_OFFICIAL_RULES_MATRIX.md` |
| Human-readable catalog + evidence text | `web/js/rules.js` (KRA II block) |
| Mobile navigation catalog | `mobile/assets/kra_catalog.json` |

**PDF verification:** Text extraction is empty (scanned). **Rendered-page visual review** verified structural rules — see `backend/docs/KRA2_PDF_VERIFICATION_NOTES.md` and `kra_configuration/kra2_official_verification.py`. **Indicator point values** for all 54 rows still come from **published Admin configuration** (cross-check sample annex rows: p. 78–81, 79, 81). **`rules.js` is not official proof.**

**KRA II structure (catalog):**

- **KRA max:** 100 points (alternative categories A / B / C — not 300 combined).
- **Criterion A:** Research Outputs Published — max 100.
- **Criterion B:** Inventions — max 100.
- **Criterion C:** Citations and Research Impact — max 100.

---

## 2. Guideline references

| Topic | Repository reference |
|---|---|
| Joint Circular PDF | `backend/docs/2026-DBM-CHED-JC-01-Enhanced-Implementing-Guidelines-of-JC3-series-of-2022 (1).pdf` |
| Annex A-style point tables (transcribed) | `web/js/rules.js` |
| Contribution forms | Annex D (research output), E (translation), F (IP), G (software) — described in rules.js evidence arrays |
| Dynamic scoring audit | `backend/docs/PHASE_C4_ADMIN_DYNAMIC_SCORING_AUDIT.md` § KRA II–IV |
| KRA II aggregation | `aggregate_kra2_kra_from_documents` + `aggregate_documents_for_kra` (kra2 branch) |
| PDF verification audit | `backend/docs/KRA2_PDF_VERIFICATION_NOTES.md` |

---

## 3. Per-criterion status

| Criterion | Admin | Backend bundles/scoring | Faculty mobile | Reviewer web | Simulation |
|---|---|---|---|---|---|
| **A — Research Outputs** | PARTIAL | PARTIAL (all A indicators in registry) | PARTIAL (criterion hub + wizard) | PARTIAL | PARTIAL |
| **B — Inventions** | PARTIAL | PARTIAL | PARTIAL (criterion hub + wizard) | PARTIAL (reviewer `/kra2-b/*`) | PARTIAL |
| **C — Citations / Impact** | PARTIAL | PARTIAL | PARTIAL (criterion hub + wizard) | PARTIAL (reviewer `/kra2-c/*`) | PARTIAL |

**COMPLETE** = none of A/B/C at all layers.

---

## 4. Layer-by-layer detail

### Admin Web — PARTIAL

- KRA II criteria and indicators appear in **Official Scoring Configuration** via shared `rules.js` / published JSON (`kras`, `criteria`, `indicators`).
- Publish/version/audit reuse KRA I infrastructure.
- **Gap:** No JC-enforced validation that edited points match Annex A (see Phase C4 audit).
- **Gap:** No KRA II–specific admin analytics dashboard extension in this sprint.

### Flask backend — PARTIAL (foundation + journal reference)

- **Added (Phase 2):** `backend/documents/kra2_evidence/` — bundle JSON in `extracted_info`, catalog-driven slots (`primary_output`, optional `contribution_certificate` for `contribution=declared`), metadata confirmation, submit flag, reviewer verification, assessed points, scoring configuration lock, workflow sync for linked PDFs, publication OCR hints (non-certifying).
- **APIs:** Faculty/reviewer `/kra2/evidence-bundle`, `/kra2-a/summary`, `/kra2-a/accomplishments`, link-supporting.
- **Simulation:** `kra2_simulation_adapter.py` + `aggregate_criterion_documents_from_list` branch for `kra2-a` (env `KRA2_SIMULATION_ADAPTER_ENABLED`, default on).
- **Scoring integrity (this sprint):** `patent_deduplication.py` (highest stage only); `aggregate_kra2_kra_from_documents` (sum criteria, cap KRA max); legacy documents skipped when a bundle exists for the same indicator; patent overlap flags on validation.
- **Still missing:** Full annex OCR for all 54 rows; B/C-family live QA; structured OCR extractors.

### PostgreSQL — PARTIAL

- Reuses `documents`, `extracted_info`, scoring configuration tables.
- **No new migrations** in this sprint (no bundle schema for KRA II accomplishments).

### Faculty Flutter — PARTIAL

- **Added:** `Kra2AJournalHubScreen` — explorer routes journal sole/co indicators to hub; live summary/accomplishments APIs; upload via existing document flow.
- **Missing:** Dedicated metadata/OCR confirmation screen (PATCH helpers exist on API), co-author Annex D upload wizard step, full parity with Criterion C track UI.

### Reviewer Web — PARTIAL

- **Added:** `kra2-evidence.js`, `kra2-a-review.js` — Criterion A accomplishment list in evidence workspace; compact guided review on `document-review.html` (metadata, checklist verify, approve/reject against backend rules).
- **Missing:** Full compact UI parity with Criterion C (OCR retry binders, rich workspace cards), Criteria B/C lists.

### Rank simulation — PARTIAL

- **Criterion level:** `aggregate_criterion_documents_from_list` → bundle adapter for `kra2-a|b|c` (estimated vs validated separate).
- **KRA level:** `aggregate_documents_for_kra` delegates `kra2` to `aggregate_kra2_kra_from_documents` (`criteria_sum_cap_at_kra_max`).

### OCR — PARTIAL

- Generic Tesseract pipeline.
- **Missing:** KRA II structured extractors (title, DOI, patent stage, etc.).

---

## 5. Tests executed

| Command | Result |
|---|---|
| `python -m pytest tests/kra_configuration/test_kra2_all_indicators.py tests/kra_configuration/test_kra2_annex.py tests/documents/test_kra2_journal_evidence.py tests/documents/test_kra2_scoring_integrity.py tests/kra_configuration/test_kra2_indicator_pdf_verification.py tests/documents/test_criterion_c_workflow_sync.py -q` | **131 passed** |
| `flutter test test/kra2_a_ux_test.dart test/kra2_a_evidence_test.dart test/kra2_catalog_test.dart` | **6 passed** (automated only) |
| `web/tests/kra2-a-workspace-ui.test.js` | **NOT TESTED** (no npm test runner in web folder this session) |

Live faculty device, reviewer browser, and Admin publish E2E are **NOT TESTED** in this sprint (reported honestly below).

---

## 6. Files added/updated (Phase 1 + Phase 2)

| Path | Purpose |
|---|---|
| `backend/documents/kra2_evidence/*` | Shared bundle architecture |
| `backend/documents/scoring/kra2_simulation_adapter.py` | Rank sim criterion A |
| `backend/tests/documents/test_kra2_journal_evidence.py` | Journal workflow unit tests |
| `web/js/kra2-evidence.js`, `kra2-a-review.js` | Reviewer/faculty API + UI |
| `mobile/lib/data/kra2_a_evidence.dart`, `screens/kra2_a/*` | Journal hub |
| Phase 1 artifacts | Matrix, annex, generator (unchanged paths) |

---

## 7. APIs — KRA II dedicated endpoints (Phase 2)

| Method | Path | Role |
|---|---|---|
| GET | `/api/faculty/me/documents/kra2-a/summary` | Faculty |
| GET | `/api/faculty/me/documents/kra2-a/accomplishments` | Faculty |
| GET/PATCH | `/api/faculty/me/documents/{id}/kra2/evidence-bundle` | Faculty |
| POST | `/api/faculty/me/documents/{id}/kra2/link-supporting` | Faculty |
| GET/PATCH | `/api/reviewer/documents/{id}/kra2/evidence-bundle` | Reviewer |
| GET | `/api/reviewer/me/faculty/{facultyId}/kra2-a/summary` | Reviewer |
| GET | `/api/reviewer/me/faculty/{facultyId}/kra2-a/accomplishments` | Reviewer |

Generic document upload still creates bundles via `maybe_initialize_kra2_bundle` when `criterion_id` is `kra2-*`.

---

## 8. Official annex verification (54 indicators)

| Metric | Count |
|---|---:|
| Indicators in catalog | 54 |
| **VERIFIED_POINTS** (catalog points/max match annex pages) | 32 |
| **PARTIAL** (points match; co-author / indexing / eligibility reviewer-gated) | 22 |
| **MISMATCH** | 0 |

Artifacts:

- Per-indicator table: [`KRA2_INDICATOR_VERIFICATION_REPORT.md`](KRA2_INDICATOR_VERIFICATION_REPORT.md) (regenerate: `python scripts/build_kra2_indicator_verification_report.py`)
- Registry: `kra_configuration/kra2_indicator_pdf_verification.py`
- Page notes: [`KRA2_PDF_VERIFICATION_NOTES.md`](KRA2_PDF_VERIFICATION_NOTES.md)

**Official KRA II aggregation (confirmed for implementation):**

- Per criterion: `min(sum(accomplishments after dedup/group caps), 100)`
- KRA total: `min(criterion_a + criterion_b + criterion_c, 100)` — **not** `max(A,B,C)` alone
- PDF: annex p.78 (KRA II 100 + criterion caps); patent highest-stage p.18; parallel sum-cap pattern KRA III p.28

Runtime points still come from **published Admin configuration** (not hardcoded annex values).

**PARTIAL indicator IDs (22):** all `*-co` co-author rows, plus `kra2-a-journal-*`, `kra2-a-cite` (indexing/eligibility requires reviewer; Sec. 17–21, 19).

---

## 9. Scoring integrity fixes (this sprint)

- Patent highest-stage dedup (same `registrationNumber`) — `patent_deduplication.py`
- Distinct inventions with different registration numbers are **not** merged
- Grant + commercialization in same period **both** count (PDF p.20)
- KRA rollup via `aggregate_kra2_kra_from_documents`; legacy docs skipped when bundle exists for same indicator
- Export script fixed `groupMax` nested objects → `kra2_indicators.json` (translation, citation, commercialization groups)

---

## 10. Live QA results

| Area | Result |
|---|---|
| Faculty mobile 3-step (all families) | **NOT TESTED** (device/browser) — automated: catalog + UX unit tests only |
| Reviewer web 3-section (A/B/C) | **NOT TESTED** (browser) — code path shared via `kra2-a-review.js` + `documents.js` |
| Admin publish / version lock | **NOT TESTED** (browser) |
| Rank simulation UI | **NOT TESTED** — backend aggregation covered by pytest |
| Patent dedup scenarios | **TESTED** (pytest `test_kra2_scoring_integrity.py`) |
| OCR live upload | **NOT TESTED** |

---

## 11. Final per-criterion status

| Criterion | Backend scoring | Mobile 3-step | Reviewer 3-section | Annex points verified |
|---|---|---|---|---|
| **A** | PARTIAL | PARTIAL | PARTIAL | 11 indicators mapped (p.78–81); co/journal/cite PARTIAL eligibility |
| **B** | PARTIAL | PARTIAL | PARTIAL | 18 indicators mapped (p.17–18, 81–84) |
| **C** | PARTIAL | PARTIAL | PARTIAL | 25 indicators mapped (p.84–92); catalog label vs PDF “Creative Works” naming aligned in annex |

**COMPLETE end-to-end for all 54:** **No** — live QA and indexing automation remain open.

---

## 12. Remaining blockers

1. Full-machine OCR of all annex pages (Tesseract not installed on dev host).
2. Live faculty/reviewer/admin browser QA.
3. Automated indexing verification (Scopus/WoS/ACI).
4. Student co-authorship policy engine (Sec. 18/19).

---

## 13. Stop boundary (honored)

KRA II verification/QA sprint complete. KRA III/IV not touched. KRA I scoring unchanged.

---

## UX polish sprint (user-friendly workflow)

**Goal:** Plain-language three-step faculty flow and three-section reviewer flow without changing backend rules.

| Layer | Completed |
|---|---|
| Faculty Mobile — Choose → Upload → Review & Submit | **Yes** (`Kra2AJournalWizardScreen`, `Kra2AReviewSubmitScreen`, hub status labels) |
| Friendly statuses (Draft / Under Review / Approved / Needs Changes) | **Yes** (`kra2_a_ux.dart`) |
| Reviewer Web — Details / Check documents / Complete review | **Yes** (`kra2-a-workspace-ui.js`, `kra2-a-review.js`) |
| Admin Official Scoring Configuration | **Unchanged** (existing folds, indicators, publish) |
| Backend APIs / bundle architecture | **Reused** (optional `publicationReference` metadata field added) |

### Tests (UX sprint)

| Command | Result |
|---|---|
| `python -m pytest tests/documents/test_kra2_journal_evidence.py tests/kra_configuration/test_kra2_annex.py -q` | **12 passed** |
| `flutter test test/kra2_a_evidence_test.dart test/kra2_a_ux_test.dart` | **3 passed** |
| `node web/tests/kra2-a-workspace-ui.test.js` | **OK** |

### Manual QA (recommended)

**Faculty (live API):** KRA II → Criterion A → journal indicator → **Add journal article** → choose sole/co → upload PDF → confirm fields → **Submit for Review** → hub shows **Under Review**.

**Reviewer:** Evidence workspace → faculty → **Criterion A** → open submission → verify each document card → approve with remarks (10+ chars).

**Admin:** Official Scoring Configuration → **KRA II** tab → confirm Criteria A/B/C folds and published draft/version labels.

### Remaining UX gaps

- Mobile: no in-app PDF viewer (opens generic document details).
- Reviewer: supporting PDF preview relies on document file URL (same as Criterion B/C).
- OCR retry button not exposed on mobile (manual entry always allowed).
- Other 52 indicators still generic upload only.

---

## Phase 2 — journal article workflow checklist

| Step | Status |
|---|---|
| Admin published configuration visible | **Existing** (no new admin pages) |
| Faculty creates accomplishment (upload) | **Implemented** |
| Evidence slots (primary + optional Annex D) | **Implemented** |
| OCR hints → metadata merge | **Partial** (hints only; faculty confirm via PATCH) |
| Faculty submit (`submitAccomplishment`) | **Implemented** |
| Reviewer verify slots + approve/reject | **Implemented** |
| Eligible / assessed points | **Implemented** (published config; co % scaling) |
| Rank simulation `kra2-a` | **Implemented** (adapter) |
| All 54 indicators | **Not claimed** |
