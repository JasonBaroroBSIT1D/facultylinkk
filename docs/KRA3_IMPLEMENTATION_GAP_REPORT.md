# KRA III — implementation gap report (read-only audit)

**Date:** 2025-11-04  
**Charter:** Audit only — **no code changes, no DB reset, no published scoring changes.**

---

## 1. Totals

| Item | Count / status |
|------|----------------|
| Indicators audited (catalog) | **46** |
| Criteria A–D | **4** |
| Scoring rules **MATCH** PDF (in repo copy) | **~40** indicator rows + 4 criterion caps |
| **MISMATCH** / narrative gaps | **≥3** (host 6-month; CSR period logic; income ₱500k boundary) |
| **UNVERIFIED** in Annex pp. 92–96 | **Criterion D** point schedule; full CMO 18 evidence phasing |
| **₱600,000** Section 31 vs Annex | **Not found** in PDF copy — see scoring audit |

---

## 2. Matched scoring rules (high confidence)

- KRA III caps: 100 overall; A=30, B=50, C=20; D bonus 20 (`rules.js`, §28).  
- Linkage 5 points.  
- Income bands and lead/co point pairs (§31, Annex 93).  
- Criterion B point rows in Annex 94–96 (QA, judge, consult, media, hourly, ISR).  
- Group maxima: occasional column 10, guest 10, ISR 30.  
- CSR formula `(CSR/100)×20` (`kra3-c-satisfaction` formula object).

---

## 3. Mismatches & clarifications needed

| Issue | Catalog / code | Official source | Severity |
|-------|----------------|-----------------|----------|
| Income at **exactly ₱500,000** | Bands `500k` vs `6m` | §31 uses 500,001; Annex 2.1.3 says “500,000 to 6M” | **Clarification** |
| TV/radio **host 6 months** | `kra3-b-host` conditions | §33.4(c) | **MISMATCH** (missing condition) |
| **CSR** 3-year average & CMO phasing | Text only | §35, Annex p. 96 timeline | **Not implemented** |
| **Criterion D** role points | 20 rows in `rules.js` | Annex extract incomplete | **UNVERIFIED** |
| **Consultancy** NGO profile pack | Partial catalog evidence | Annex 1.3.4, §33.3d | **Catalog gap** |
| **Judge** NGO profile pack | Missing in catalog | Annex 1.2.5 | **Catalog gap** |

---

## 4. Unverified official requirements

- Full **Annex A** evidence table for **Criterion D** designations (points + documents).  
- **Concurrent** administrative designations in the same year (stacking rules beyond §36b narrative).  
- **Income accomplishment** — whether multiple bands can be claimed for disjoint projects or one gross total per period.  
- **Peer review** journal eligibility (Scopus/WoS future rule, §33.3e).  
- **Resource person** authorization matrix (study leave exception, Annex 1.5.4).

---

## 5. Existing reusable components

| Component | Path | KRA III readiness |
|-----------|------|-------------------|
| Official rules catalog | `web/js/rules.js` (KRA III block) | **Seed complete** (46 indicators) |
| Mobile name catalog | `mobile/assets/kra_catalog.json` | **IDs/names only** |
| Published KRA/criterion caps | `kra_configuration/published_limits.py` | **Works** (`test_published_limits.py`) |
| Admin publish pipeline | `kra_configuration/service.py`, version lock | **Works** |
| Rank simulation KRA bucket | `rank_simulation_engine.py`, `kra_document_aggregate.py` | **Legacy document points** |
| Bonus criterion handling | `criterion_is_bonus('kra3-d')` | **Works** |
| Cross-KRA designation overlap | `criterion_b_evidence/cross_kra.py` | **Partial** (4 committee IDs) |
| Web scoring helper | `web/js/scoring.js` (`rating` formula) | **Works** for CSR-shaped docs |
| KRA II evidence bundle pattern | `documents/kra2_evidence/*` | **Template for KRA III** |

---

## 6. Missing implementation components

| Component | Priority | Notes |
|-----------|----------|-------|
| `kra3_indicator_registry.py` + JSON export | P0 | Parity with KRA II |
| `kra3_indicator_pdf_verification.py` | P0 | Automated MATCH/MISMATCH |
| `kra3_evidence_slots.py` + API `requiredEvidenceSlots` | P0 | Annex-driven checklist |
| Faculty Mobile KRA III hub + Check your work | P0 | Reuse `Kra2ReviewSubmitScreen` pattern |
| Backend bundle + validation service | P0 | Not `kra2_*` — new namespace |
| Reviewer Web workspace UI | P1 | Slot verify/reject |
| OCR profiles (`kra3_ocr_extraction.py`) | P1 | See OCR matrix doc |
| Published **base points** in rank aggregation | P1 | Same gap as KRA II–IV (Phase C4) |
| CSR ↔ ISR **project linkage** | P0 | §35e mandatory |
| Income **band selector** UX + mutual exclusion | P1 | Prevent double band claim |
| Hourly resource person **hour multiplier** | P1 | Per-hour scoring |
| Group max aggregation (column, guest, ISR) | P1 | Like KRA II `groupMax` |
| E2E tests (mobile + Playwright) | P2 | After credentials/fixtures |
| `docs/` annex page renders for KRA III D | P2 | Close UNVERIFIED |

**Explicitly absent today:** `backend/documents/kra3_evidence/`, mobile `kra3_*` screens, web `kra3-*-workspace-ui.js`.

---

## 7. Recommended implementation order

1. **Official verification layer** — PDF page map + `kra3_indicator_pdf_verification.py`; resolve D table & ₱500k boundary with CHED before publish lock.  
2. **Evidence slot catalog** — Annex pp. 92–96 → slot IDs; sync web/mobile/backend tests (KRA II checklist sync pattern).  
3. **Backend bundle API** — PATCH metadata, validation, submit for review; persist PostgreSQL; **no** change to approved legacy docs.  
4. **Admin** — Keep existing UI; ingest indicator evidence hints from registry (no redesign).  
5. **Faculty Mobile** — Extension hub, multi-slot upload, `Kra3SubmitReadiness`, CSR formula display from API.  
6. **Reviewer Web** — Workspace + scoring breakdown from published config.  
7. **OCR profiles** — Family parsers (advisory); reject cert boilerplate.  
8. **Rank simulation** — Wire `published_kra3_indicator_*` + group caps + bonus cap.  
9. **Cross-KRA** — CSR↔ISR project IDs; extend `cross_kra.py` for designation overlap.  
10. **Live QA matrix** — Per criterion family PASS/FAIL/NOT TESTED.

---

## 8. Safety & compatibility (confirmed audit constraints)

- **No PostgreSQL reset** in this audit.  
- **No modification** to approved accomplishments.  
- **No new published scoring** values published.  
- **KRA I / KRA II** codepaths not altered.

---

## 9. Deliverables index

| Document | Purpose |
|----------|---------|
| [`KRA3_OFFICIAL_SCORING_AUDIT.md`](KRA3_OFFICIAL_SCORING_AUDIT.md) | Points, caps, discrepancies |
| [`KRA3_OFFICIAL_EVIDENCE_MATRIX.md`](KRA3_OFFICIAL_EVIDENCE_MATRIX.md) | Annex vs catalog evidence |
| [`KRA3_OCR_VALIDATION_MATRIX.md`](KRA3_OCR_VALIDATION_MATRIX.md) | Future OCR/validation design |
| This file | Gaps and build order |

**Helper (read-only):** `python backend/scripts/audit_kra3_catalog_extract.py`

---

**STOP — await stakeholder review before implementation.**
