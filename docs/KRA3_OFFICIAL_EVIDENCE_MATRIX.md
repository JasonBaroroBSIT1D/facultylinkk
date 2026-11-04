# KRA III — official evidence matrix (read-only audit)

**Sources:** DBM–CHED JC No. 01, s. 2026 §§28–36; Annex A PDF pp. **92–96**; FacultyLink catalog evidence text in `web/js/rules.js`.

**Legend**

- **Annex** — explicit required evidence in Annex A table.
- **Section** — narrative requirement in Enhanced Guidelines body (§30–36).
- **Catalog** — FacultyLink `rules.js` `evidence[]` strings (metadata only today).
- **Slots** — structured checklist slot IDs (KRA II pattern). **None exist for KRA III** in backend.

---

## Criterion A (max 30)

### `kra3-a-linkage` — Successful linkage / partnership

| # | Annex A (p. 92) | Section §30 | Catalog | Suggested slot ID |
|---|-----------------|-------------|---------|-------------------|
| 1 | Board/President/Chancellor approval authorizing partnership | MOA + successful implementation; faculty spearheaded | ✓ (paraphrased) | `partnership_approval` |
| 2 | Notarized MOA/MOU (or project proposal if activities not in MOA) | ✓ | ✓ | `moa_mou` |
| 3 | Implementation or terminal report | ✓ | ✓ | `implementation_report` |
| 4 | Certification President/VP — initiated through faculty initiative | ✓ | ✓ | `faculty_initiative_certification` |

**Conditional:** Partnership excludes pure OJT/practicum-only links (§30.2) — **Section only**.

---

### Income generation (`kra3-a-income-lead-*`, `kra3-a-income-co-*`)

| # | Annex A (p. 93) | Catalog | Notes |
|---|-----------------|---------|-------|
| A1 | Financial reports (commercialization), SUC Accountant certified | ✓ | Redaction allowed (Annex note) |
| A2 | Finance Division certification of contribution + income | ✓ | Lead vs co must show role |
| B1 | Sub-ARO or equivalent (grants) | ✓ (Sub-ARO) | |
| B2 | Finance certification — role in securing grant | ✓ | |
| C1 | Financial reports (industry projects) | ✓ | |
| C2 | Finance certification — involvement | ✓ | |

**Alternative paths:** Income type A / B / C are **alternatives by source**, not all required for one accomplishment.

**Role:** Separate indicator IDs for **Lead** vs **Contributor** (§31.4) — not Annex I %; **half points** baked into co-indicator points.

---

## Criterion B (max 50)

### Accreditation / QA — `kra3-b-qa-local`, `kra3-b-qa-intl`

| # | Annex (p. 94) | §33 | Catalog |
|---|---------------|-----|---------|
| 1 | Official appointment/designation as evaluator/accreditor | Per **agency**, not per deployment | ✓ |
| 2 | Proof of engagement (travel order, report, minutes, certificate) | ✓ | ✓ |
| 3 | SUC President authorization | ✓ | ✓ |
| 4 | Agency profile + website if not on prescribed list | §33d–e lists (CHED, DTI, AACCUP, …) | Partial in § only |

---

### Judging — `kra3-b-judge-research`, `kra3-b-judge-academic`

| # | Annex (p. 94) | §31–32 (p. 31) | Catalog |
|---|---------------|----------------|---------|
| 1 | Official invitation as judge/examiner | ✓ | ✓ |
| 2 | Proof of award/competition | ✓ | ✓ |
| 3 | Proof of engagement | ✓ | ✓ |
| 4 | President/VP authorization | ✓ | ✓ |
| 5 | NGO: org profile, mandate, history, prior awardees | §31d | **Not in catalog** |

**Conditional:** SUC-internal competitions **excluded** (§32e) — **Section only**.

---

### Consultancy — `kra3-b-consult-local`, `kra3-b-consult-intl`

| # | Annex (p. 95) | §33.3 (p. 32) | Catalog |
|---|---------------|---------------|---------|
| 1 | Agreement/contract/invitation + acceptance (duration & scope) | 1–6 months typical | ✓ |
| 2 | Certificate or consultancy report | ✓ | ✓ (engagement) |
| 3 | President/Chancellor/VP authorization | ✓ | ✓ |
| 4 | Private org: profile, mandate, SEC/DTI, website | ✓ | **Not in catalog** |
| 5 | International journal peer review — editorial board; future Scopus/WoS | §33.3e | **UNVERIFIED** in catalog |

---

### Media — columns, host, guest

| Indicator | Annex (p. 95) | §33.4 (pp. 32–33) | Catalog gaps |
|-----------|---------------|-------------------|--------------|
| `column-occasional` | Compiled articles + front pages (max 10) | Broadsheet / official online | ✓ |
| `column-regular` | Same | Max 10 pts regular column (§33b) | Catalog says 10 per column — **verify** vs § |
| `host` | Contract/invitation + on-air schedule + online link | **Min 6 months** regular host | Catalog missing 6-month rule |
| `guest` | Invitation + recording/link/article | Max 10 guestings | ✓ |

---

### Resource person — `kra3-b-train-local`, `kra3-b-train-intl`

| # | Annex (p. 96) | §33.5 / §34 (p. 33–34) | Catalog |
|---|---------------|-------------------------|---------|
| 1 | Invitation (title, topic, date, venue) | Tertiary+ or industry | ✓ (partial) |
| 2 | Program with **topic and allocated time** | No time → no points | Program only in catalog |
| 3 | Certificate of appreciation | ✓ | ✓ |
| 4 | Authorization (local: President…Dean; intl: board approval) | In-house SUC activities excluded | **Not in catalog** |

**Unit:** Points **per hour** — evidence must support hour count (Annex + §33.5d).

---

### Extension / ISR — `kra3-b-ext-head`, `kra3-b-ext-participant`

| # | Annex (p. 96) | §34 (p. 34) | Catalog |
|---|---------------|-------------|---------|
| 1 | Special Order (roles) | Active expert delivery only | Partial (`appointment`) |
| 2 | Board-approved extension project proposal | ✓ | **Not in catalog** |
| 3 | Evidence of performed role | ✓ | Report only |
| 4 | Status/terminal report (extension office) | ✓ | ✓ (activity report) |

**Subcap:** ISR group max **30** (head + participant combined) — `groupMax` in catalog.

---

## Criterion C — `kra3-c-satisfaction`

| # | Annex (p. 96) | §35 (pp. 34–35) | Catalog |
|---|---------------|-----------------|---------|
| 1 | CSR summary / Extension Project CSS Report (period-dependent) | CMO 18 s. 2025 phasing | One generic line |
| 2 | Certified by extension head/director | ✓ | **Not explicit** |
| 3 | **Mandatory:** same projects declared under Criterion B ISR | §35e | ✓ (condition text) |

**Evaluation periods (Annex):**

- 1st Sem AY 2023–24 → 2nd Sem AY 2024–25: legacy instrument summary.  
- 1st Sem AY 2025–26: old or CMO 18 CSS report.  
- 2nd Sem AY 2025–26 onward: CMO 18 CSS report only.

---

## Criterion D — administrative designations (20 bonus)

**Annex p. 96:** Criterion D header only in extract — **no evidence table rows** in pp. 92–96 render.

**§36 + catalog (each `kra3-d-*`):**

| Evidence (catalog) | Typical official need |
|--------------------|------------------------|
| Appointment/designation with effectivity | Per-year eligibility |
| Accomplishment report | Performance while in role |
| Regent: faculty association annual report | `kra3-d-regent` only |

**Conditional:** Committee designations — Governing Board approval of **committee creation** (§36c).

---

## Implementation vs matrix

| Capability | KRA II (reference) | KRA III today |
|------------|-------------------|---------------|
| `requiredEvidenceSlots` API | Yes (`kra2_*_evidence_slots.py`) | **Missing** |
| Multi-slot upload UI | `kra2_review_submit_screen.dart` | **Missing** |
| Reviewer slot verify/reject | `kra2-a-workspace-ui.js` | **Missing** |
| Evidence text in Admin | `indicatorMeta` / rules seed | **Narrative only** in `rules.js` |

See `docs/KRA3_IMPLEMENTATION_GAP_REPORT.md`.
