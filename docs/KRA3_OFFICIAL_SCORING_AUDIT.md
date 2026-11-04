# KRA III — Extension Services: official scoring audit (read-only)

**Source document:** `backend/docs/2026-DBM-CHED-JC-01-Enhanced-Implementing-Guidelines-of-JC3-series-of-2022 (1).pdf` (130 pages, scanned).  
**Method:** Visual review of rendered pages in `backend/docs/pdf_render_kra2/` (same PDF used for KRA II verification) plus catalog in `web/js/rules.js` / `mobile/assets/kra_catalog.json`.  
**Configured values:** Published Admin PostgreSQL row is **not queried** in this audit; **catalog defaults** = `rules.js` unless an institution has published overrides.

**Policy sections reviewed:** §§28–36 (printed pp. 28–35 in renders). **Annex A:** PDF pp. 92–96 (KRA III block starts p. 92).

---

## Executive summary

| Metric | Count |
|--------|------:|
| **Indicators in FacultyLink catalog** | **46** (plus 4 criterion header rows in `rules.js`) |
| **PDF point rules MATCH catalog** | **~40** (A income bands, B point rows in Annex 92–96, C formula) |
| **MISMATCH / gap vs PDF narrative** | **≥3** (see below) |
| **UNVERIFIED in Annex A (this PDF copy)** | **Criterion D per-designation point table**; exact ₱ boundary at 500,000 |

**Do not treat `rules.js` as legal proof** — use PDF page citations below.

---

## KRA III structure (§28)

| Criterion | Official max | Catalog (`rules.js`) | Status |
|-----------|-------------:|---------------------|--------|
| A — Service to the Institution | 30 | `kra3-a` maxPoints 30 | **MATCH** |
| B — Service to the Community | 50 | `kra3-b` maxPoints 50 | **MATCH** |
| C — Relevance / quality (CSR) | 20 | `kra3-c` maxPoints 20 | **MATCH** |
| D — Bonus (administrative designation) | 20 (bonus) | `kra3-d` maxPoints 20, `bonus: true` | **MATCH** (cap); **per-indicator points UNVERIFIED in Annex 92–96** |
| **KRA III overall** | 100 (A+B+C); D bonus subject to overall cap | `kra3` maxPoints 100, `bonusMax: 20` | **MATCH** (§28 note: final total ≤ 100) |

Backend: `published_kra_max_points('kra3')`, `criterion_is_bonus('kra3-d')` — `backend/kra_configuration/published_limits.py`, tests in `test_published_limits.py`.

---

## Section 31 vs Annex A — income bracket discrepancy (investigation)

**Audit brief asked:** Section 31 **₱600,000** vs Annex A **₱500,000**.

**Finding in repo PDF copy:**

| Source | Middle bracket wording | Next bracket |
|--------|------------------------|--------------|
| **§31** (render `page_029_hd.png`, printed **29**) | **100,001 to 500,000** → 4 pts; **500,001 to 6,000,000** → 6 pts | Aligns with catalog IDs `*-500k` / `*-6m` |
| **Annex A** (render `page_093_hd.png`, PDF **93**) | **100,001 to 500,000** → 4 pts; **500,000 to 6,000,000** → 6 pts (row 2.1.3) | Same bands, **inclusive-boundary wording differs** at **exactly ₱500,000** |

**₱600,000 boundary:** **NOT REPRODUCED** in §§28–36 or Annex pp. 92–96 in this PDF copy. No `600,000` string in project catalogs.

**Action:** Flag **only** the **₱500,000 vs ₱500,001** edge case for authorized clarification (which band owns exactly five hundred thousand pesos). Do **not** change published scoring until CHED/DBM confirms.

**Catalog:** `kra3-a-income-*-500k` names use **100,001 to ₱500,000**; `*-6m` use **500,001 to ₱6,000,000** — consistent with **§31**, not the Annex row label “500,000 to 6,000,000”.

---

## Criterion A — Service to the Institution (30)

### A.1 Linkages (`kra3-a-linkage`)

| Field | Official | Catalog | Status |
|-------|----------|---------|--------|
| Base points | 5 per successful partnership | points 5, maxPoints 5 | **MATCH** (Annex p. 92; §30) |
| Unit | Per activity | Per indicator row | **MATCH** |
| Lead/co | N/A (faculty initiative) | contribution `not-applicable` | **MATCH** |

### A.2 Income generation (10 lead + 10 contributor indicators)

| Indicator ID | Role | Official band (§31 / Annex 93) | Lead pts | Co pts (½ lead) | Catalog lead | Catalog co | Status |
|--------------|------|----------------------------------|---------:|------------------:|-------------:|-----------:|--------|
| `*-100k` | Lead / Co | ≤ ₱100,000 | 2 | 1 | 2 | 1 | **MATCH** |
| `*-500k` | Lead / Co | ₱100,001 – ₱500,000 | 4 | 2 | 4 | 2 | **MATCH** |
| `*-6m` | Lead / Co | ₱500,001 – ₱6,000,000 (§31) | 6 | 3 | 6 | 3 | **MATCH** §31; **BOUNDARY** vs Annex label |
| `*-12m` | Lead / Co | ₱6,000,001 – ₱12,000,000 | 12 | 6 | 12 | 6 | **MATCH** |
| `*-over` | Lead / Co | > ₱12,000,000 | 18 | 9 | 18 | 9 | **MATCH** |

**Special conditions (§31):** Gross income; lead full points; co-contributors **50%** — catalog conditions text matches.

**Criterion A subcap:** 30 — not a sum of all possible income rows; faculty claim **one band per accomplishment** (implementation must enforce mutual exclusion / reviewer choice — **not implemented** in KRA II-style bundles today).

---

## Criterion B — Service to the Community (50)

Annex pp. 94–96; narrative §§32–34, 33–34.

| Indicator ID | Official name (Annex) | Points | Max / group | Catalog | Status |
|--------------|----------------------|-------:|------------|---------|--------|
| `kra3-b-qa-local` | Accreditation/QA — Local | 8 | per agency | 8 / 8 | **MATCH** |
| `kra3-b-qa-intl` | International | 10 | per org | 10 / 10 | **MATCH** |
| `kra3-b-judge-research` | Judge — research awards | 2 | per engagement | 2 / 2 | **MATCH** |
| `kra3-b-judge-academic` | Judge — academic competitions | 1 | per engagement | 1 / 1 | **MATCH** |
| `kra3-b-consult-local` | Short-term consultant — Local | 8 | per engagement | 8 / 8 | **MATCH** |
| `kra3-b-consult-intl` | International | 10 | per engagement | 10 / 10 | **MATCH** |
| `kra3-b-column-occasional` | Occasional column | 2 | **max 10** | 2 / 10, groupMax 10 | **MATCH** |
| `kra3-b-column-regular` | Regular column | 10 | per column | 10 / 10 | **MATCH** |
| `kra3-b-host` | TV/radio host | 10 | per program | 10 / 10 | **MATCH** Annex; **MISMATCH** vs §33(c) **6-month minimum** (not in catalog conditions) |
| `kra3-b-guest` | Technical expert guesting | 1 | **max 10** | 1 / 10, groupMax 10 | **MATCH** |
| `kra3-b-train-local` | Resource person — local | 2 | **per hour** | 2 / 2 | **MATCH** |
| `kra3-b-train-intl` | International | 3 | **per hour** | 3 / 3 | **MATCH** |
| `kra3-b-ext-head` | Extension/ISR — Head | 5 | **ISR max 30** | 5 / 30, groupMax 30 | **MATCH** |
| `kra3-b-ext-participant` | Participant | 2 | **ISR max 30** | 2 / 30, groupMax 30 | **MATCH** |

**Criterion B cap:** 50 — catalog criterion max **MATCH**.

---

## Criterion C — Client satisfaction (20)

| Field | Official (§35, Annex p. 96) | Catalog `kra3-c-satisfaction` | Status |
|-------|------------------------------|----------------------------------|--------|
| Formula | (Overall CSR ÷ 100) × 20 | `formula.type: rating`, multiplier 20 | **MATCH** |
| Period | 3-year average CSR (§35 sample) | Not modeled in catalog | **UNVERIFIED** in app logic |
| Link to Criterion B ISR | Projects must be declared under ISR (§35e, Annex note) | Condition text present | **MATCH** (text); **no backend link** |
| CMO 18 s. 2025 phasing | §35b–c, Annex evidence timeline | Condition text partial | **PARTIAL** |

---

## Criterion D — Bonus administrative designation (20)

| Field | Official §36 | Catalog | Status |
|-------|--------------|---------|--------|
| Eligibility | ≥1 continuous year; OIC ≥1 year; per year credited | Conditions on each indicator | **MATCH** (narrative) |
| Concurrent vs sequential | Different roles in different years — points per year per designation | Not encoded | **UNVERIFIED** in engine |
| Governing Board | Committee chair/member — Board-approved creation | On inst/dept committee rows | **MATCH** (text) |
| KRA cap | Bonus; total KRA III ≤ 100 | `bonus: true`, KRA summary text | **MATCH** |

**Per-designation point schedule** (President 20, VP 15, …): Present in **`rules.js`** (20 indicators). **Annex A pp. 92–96** show **Criterion D header (max 20)** on p. 96 **without** the designation points table in the rendered extract. **Status: UNVERIFIED against Annex A** in this audit (may appear on other annex pages not rendered or only in body sections not captured in table form).

Cross-KRA: `kra3-d-inst-chair`, `kra3-d-inst-member`, `kra3-d-dept-chair`, `kra3-d-dept-member` referenced for **Criterion B program overlap** (`documents/criterion_b_evidence/cross_kra.py`) — scoring dedup **partial**, not full KRA III workflow.

---

## Full indicator register (configured catalog = `rules.js`)

Regenerate counts: `python backend/scripts/audit_kra3_catalog_extract.py`

| Criterion | Indicators |
|-----------|----------:|
| A | 11 (1 linkage + 10 income) |
| B | 14 |
| C | 1 |
| D | 20 |
| **Total** | **46** |

---

## Scoring integration status

| Layer | KRA III behavior | Audit |
|-------|------------------|-------|
| Admin Official Scoring | Publishes `criteria.kra3-*`, `indicators` from template/`rules.js` | **Caps supported**; no `kra3_indicator_pdf_verification.py` |
| Rank simulation | `aggregate_documents_for_kra(profile, 'kra3')` — document-stored points + published KRA max | **PARTIALLY DYNAMIC** (Phase C4 audit) |
| Faculty Mobile | `KraType.extension`, `kra_catalog.json` names only | **No KRA III evidence bundle / Check your work** |
| Reviewer Web | Legacy document + `FL.scoring.scoreDocument` | **No KRA III workspace** like KRA II A/B/C |

---

## Recommended official clarifications (no scoring changes)

1. Income band at **exactly ₱500,000** (§31 vs Annex 2.1.3 wording).  
2. **Criterion D** designation point table — confirm annex page reference for each role.  
3. **TV/radio host** minimum **6 months** (§33) vs catalog “per regular program”.  
4. **CSR** evaluation years vs CMO 18 s. 2025 transition for active evaluation periods.

**STOP — implementation not started per audit charter.**
