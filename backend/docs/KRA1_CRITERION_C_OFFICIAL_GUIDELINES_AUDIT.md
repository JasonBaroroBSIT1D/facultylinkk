# KRA I — Criterion C: Research Advising and Mentorship (Phase 1 audit)

**Date:** 2026-11-03 (UTC+8)  
**Type:** Read-only — no code, database, scoring, or configuration changes  
**Authority:** `backend/docs/2026-DBM-CHED-JC-01-Enhanced-Implementing-Guidelines-of-JC3-series-of-2022 (1).pdf`  
**FacultyLink reference rules:** `web/js/rules.js` (Annex A matrix, JC 01 s. 2026)

---

## PDF access method

- Automated text extraction (PyPDF / PyMuPDF) returned **no usable text** (image-only scan).
- **Visual inspection** of rendered pages was used for this audit.
- **Human re-verification** of page numbers and fine print is still recommended before certification.

**Key PDF locations (1-based page numbers as printed on the document):**

| Content | Printed page(s) |
|---------|-----------------|
| KRA I point split (A=60, B=30, **C=10**) | **3** (Section 5) |
| **Section 15** — Criterion C narrative rules | **10–11** |
| **Annex A** — KRA I start | **74** (Annex A page 1) |
| **Annex A — Criterion C** table (points + evidence) | **77–78** |

---

## 1. Official indicators and points

### Criterion cap

| Source | Rule |
|--------|------|
| Section 5, p. 3 | KRA I Instruction: Criterion A **60** + B **30** + **C 10** = **100** |
| Section 15, p. 10 | **“Criterion C – Research-Related and Mentorship Services (10 points)”** |
| Annex A, p. 77 | **“Criterion C – Research Advising and Mentorship Services (Max = 10)”** |

**Naming note:** Body text uses *“Research-Related and Mentorship Services”*; Annex A uses *“Research Advising and Mentorship Services.”* FacultyLink uses the Annex A-style name in `rules.js` / catalog.

### Annex A — Indicator 1: Research-related services (adviser / panel)

**Official wording (Annex A, p. 77):** *“For every service rendered as an adviser or panel member in undergraduate and master’s theses, special/capstone projects, or doctoral dissertations.”*  
Cross-reference: *Item 1, Section 15*.

| Activity (official) | Abbrev. | **Adviser pts** | **Panel pts** |
|---------------------|---------|-----------------|---------------|
| Special Project / Capstone Project | SP/CP | **3** | **1** |
| Undergraduate Thesis | UT | **5** | **1** |
| Master’s Thesis | MT | **8** | **2** |
| Doctoral Dissertation | DD | **10** | **2** |

FacultyLink maps these to **eight** indicator IDs (`kra1-c-adviser-*`, `kra1-c-panel-*`) with the same point values in `web/js/rules.js` and Admin-published `indicators` config (when synced from rules defaults).

### Annex A — Indicator 2: Mentorship services

| Official | Points |
|----------|--------|
| *“For every service rendered to a student/group of students as a coach/mentor”* (Item 2, Section 15) | **3** (Annex A, p. 77–78) |

FacultyLink: `kra1-c-mentor` — **3** points, max **3**.

### Section 15 — Eligibility and conditions (narrative)

**1. Research-related services rendered**

| # | Official requirement (paraphrased from p. 10–11) |
|---|--------------------------------------------------|
| 1.a | Adviser and/or panel for special/capstone projects, UG/graduate theses, doctoral dissertations; advising load **generally up to five (5) students per academic year**. |
| 1.b | Topic within or closely related to faculty **field of specialization**. |
| 1.c | Project/thesis/dissertation **successfully completed and defended**. Evidence: **duly signed approval sheet**. |
| 1.d | Credited only if program has valid **RRPA** or **COPC**. |

**2. Mentorship services**

| # | Official requirement |
|---|----------------------|
| 2.a | Mentor/coach at **higher education level** (academic, technology/innovation, creative, research, etc.). |
| 2.b | **Official designation or appointment** as mentor/coach from the **SUC president**. |
| 2.c | Points only if students win **major prize** (Champion, 1st, 2nd, 3rd) in **regional, national, or international** competitions; **local** competitions and **consolation** prizes **not** eligible. |
| 2.d | Competition aligned with faculty **specialization**. |
| 2.e | Mechanics and winners **publicly available**. |
| 2.f | Eligible sponsors: reputable private entities / professional orgs with national membership; national government agencies (incl. SUC consortia); recognized international/intergovernmental orgs. |

### Annex A — Required evidence

**Research-related (Annex A, p. 77):**

1. Copy of **approval sheet** showing: title; student name(s); adviser name; panel member names; date of approval.  
2. Copy of **RRPA or COPC** for the program in which the faculty served the student(s).

**Mentorship (Annex A, p. 77–78):**

1. Copy of **designation as mentor/coach** (for student or group).  
2. Copy of **award/certificate** or photo of trophy/plaque/medal.  
3. Copy of **mechanics** of the award/competition (major awards/winners).  
4. Document on **award-giving organization** (profile, mandate, history, list of previous awardees/winners).

### Scoring frequency and accumulation (official)

| Topic | Official basis | Audit reading |
|-------|----------------|---------------|
| Evaluation period | Section 3; `rules.js` global conditions | **Aug 1, 2023 – Jul 31, 2026** (and succeeding 3-year cycles) |
| Multiple instances | Annex A *“for every service rendered”* | **Multiple distinct advising/panel/mentor acts** may earn points **until Criterion C max (10)** — **not** stated as “one indicator once only.” |
| KRA I total | Section 5 | A + B + C capped at **100** (via `cap_kra1_instruction_total` in backend) |
| Double counting | Article III Item 8 (p. 3 area) / `rules.js` global | Same document **cannot** be used for two indicators unless explicitly permitted; **adviser + panel on the same thesis** — **UNCERTAIN** in circular (not explicitly allowed or forbidden in Section 15 text reviewed) |
| Adviser load | Section 15.1.a | **5 students / AY** — guideline load; **no numeric cap formula** in Annex A point table |

### Items marked UNCERTAIN / unreadable

- Exact JC **indicator numbering** beyond Annex A rows 1–2 (FacultyLink uses synthetic IDs, not official numeric codes).  
- Whether **adviser and panel** credit for the **same** student/project is allowed in one evaluation cycle (needs legal/policy confirmation).  
- Whether **multiple documents** for the **same indicator ID** (e.g. two UT advisories) should **sum** or **replace** — Annex A wording favors **summation to 10**; FacultyLink legacy aggregation does **not** (see §4).  
- Full text of any **SUC-specific** stricter rules (Section 10 / board authority).

---

## 2. Existing FacultyLink implementation inventory

| Layer | Criterion C status |
|-------|-------------------|
| **Official rules mirror** | `web/js/rules.js` — 9 indicators, evidence bullets, conditions (aligned with Annex A / Section 15 at high level) |
| **Mobile catalog** | `mobile/assets/kra_catalog.json` — criterion + indicator **names only** (no points, no evidence text) |
| **Dedicated Criterion C module** | **None** (no `criterion_c_evidence/`, no bundles, no checklist validation) |
| **Criterion B-style adapter** | **None** for `kra1-c` |
| **Document upload** | Generic KRA explorer → upload with `criterionId=kra1-c` + `indicatorId` (same path as other non-A/B criteria) |
| **Mobile special UX** | **None** (no Criterion C hub; unlike Criterion B hub / Criterion A SET/SEF) |
| **Reviewer Web** | Generic **document review** (`document-review.html`, `evidence-workspace.js`) — **no** Criterion C accomplishment workspace |
| **Scoring on document row** | `Document.estimated_points`, `verified_points`, `reviewer_score`; OCR fields `System-calculated score` / `Provisional score` in `extracted_info` |
| **Effective points** | `documents/scoring/document_evidence_points.py` → `effective_document_points()` |
| **Criterion aggregation** | `faculty/kra_document_aggregate.py` → `_legacy_aggregate_criterion_from_documents()` for `kra1-c` |
| **KRA I cap** | `kra_configuration/criterion_b_scoring.py` → `cap_kra1_instruction_total()` includes `kra1-c` at published max **10** |
| **Rank simulation** | `rank_simulation_engine.py` → `aggregate_criterion_documents(..., "kra1-c")` same legacy path as pre-adapter Criterion B |
| **Admin config** | Published `kraSettings` — criterion max **10**, per-indicator points from rules defaults / edits via `web/js/kra-config.js` |
| **Automated tests** | KRA I cap tests reference `kra1-c`; **no** Criterion C evidence or aggregation policy tests |

---

## 3. Guideline-to-code comparison matrix

| Official requirement | Guideline ref. | FacultyLink implementation | Compliance | Required correction |
|----------------------|----------------|----------------------------|------------|---------------------|
| Criterion C max **10** | §5 p.3; §15; Annex A | `published_criterion_max_points("kra1-c")`; aggregation `min(sum, 10)` | **Partial** | Enforce after **correct** per-service summation |
| Nine activity types with Annex A points | Annex A p.77 | `rules.js` + Admin `indicators` | **Pass** (config) | Keep in sync with Annex A on publish |
| Approval sheet evidence | §15.1.c; Annex A | Listed in `rules.js`; **not** enforced in backend checklist | **Fail** | Structured evidence slots + validation |
| RRPA/COPC for program | §15.1.d; Annex A | Listed in `rules.js`; **not** enforced | **Fail** | Slot + reviewer verification (cf. Criterion B RRPA pattern) |
| Successful completion / defense | §15.1.c | In `rules.js` conditions only | **Fail** | Reviewer attestation field |
| Specialization alignment | §15.1.b, 2.d | Not C-specific in code | **Fail** | Claim metadata + reviewer confirm |
| Mentorship: president designation | §15.2.b; Annex A | `rules.js` evidence text | **Fail** | Required upload + verify |
| Mentorship: prize level / no local / no consolation | §15.2.c | `rules.js` conditions | **Fail** | Reviewer eligibility checklist |
| Mentorship: public mechanics + org profile | §15.2.e–f; Annex A | `rules.js` evidence list | **Fail** | Multi-document checklist |
| **Multiple services** sum toward 10 | Annex A “every service” | **`best_by_indicator` then sum** — **one doc per indicator ID** | **Fail** | Sum **distinct accomplishments** with dedupe keys (student+role+term), cap 10 |
| Adviser load ~5 students/AY | §15.1.a | Not implemented | **Gap** | Optional advisory flag / reviewer note |
| No double counting (documents) | Art. III §8 | Duplicate hash in uploads (general); **no C-specific** adviser/panel same-project rule | **Uncertain** | Policy + dedupe rules after legal clarification |
| Reviewer-assessed final score | Implicit in JC process | `verified_points` / approve document | **Partial** | Dedicated **reviewer-proposed assessment** + justification (mirror Criterion B pattern) |
| Rank simulation integration | KRA I structure | Included in `_build_kra1_criteria_scores` | **Pass** (wiring) | Feeds **legacy** aggregation until C adapter exists |
| OCR auto-score | Not in JC for C | `effective_document_points` may use OCR provisional scores | **Risk** | OCR **advisory only** for C; reviewer gates points |

---

## 4. Does Criterion C use “generic document scoring”?

**Yes.** Today Criterion C is treated like other non–Criterion-A/B criteria:

1. Faculty uploads a file tagged with `kra1-c` and an indicator ID.  
2. Points may come from `estimated_points`, OCR-extracted provisional scores, or reviewer-set `verified_points` / `reviewer_score`.  
3. `aggregate_criterion_documents_from_list` uses **`_legacy_aggregate_criterion_from_documents`**: for each `indicator_id`, keep the **single highest** document score, **add** those bests, then **cap at 10**.

**This is not equivalent to Criterion B’s** evidence-bundle + `readyForScoring` + reviewer-proposed assessment + (optional) simulation adapter.

**Critical difference from Annex A:** Official language supports **multiple** “services rendered” (e.g. two UT advisories at 5 + 5 = 10). Legacy **one winner per indicator ID** yields **max 5** for two UT advisories under `kra1-c-adviser-ut` — **under-counting**.

**Criterion B logic must not be copied blindly** (no contribution %, no Annex C, no instructional-material types), but **reviewer-gated, checklist-based accomplishments** are the appropriate analogy.

---

## 5. Recommended workflow (proposed — pending approval)

### Faculty Mobile

1. **Choose Criterion C** → pick indicator (Adviser UT, Panel MT, Mentor, etc.) or guided “Add advising/mentorship” wizard.  
2. **Accomplishment details:** student name(s), project title, program, AY/term, role (if combined flow), specialization alignment self-declaration.  
3. **Upload checklist:** approval sheet (required); RRPA/COPC (required for advising/panel); mentorship designation + award + mechanics + org profile as applicable.  
4. **Status:** validation flags (missing RRPA, incomplete approval sheet OCR, pending reviewer) — **no auto-final points from OCR**.

### Reviewer Web

1. Open faculty → **Criterion C workspace** (per accomplishment, not only flat document list).  
2. Verify each evidence slot; confirm **completion/defense**, **specialization**, **RRPA/COPC**, mentorship eligibility.  
3. View **published indicator points** (read-only from Admin config).  
4. Enter **reviewer assessment** (points ≤ indicator max, ≤ remaining room under C total 10) with **justification**.  
5. Save → audit history on bundle JSON (same pattern as Criterion B `reviewerProposedAssessment`).

### Backend

1. **`criterion_c_evidence` bundle** in `extracted_info` (no migration required initially).  
2. **`criterion_c_scoring.py` / annex map** — indicator → official points; **sum accomplishments** with dedupe; **`cap_criterion_c_total(10)`**.  
3. **Canonical current score** resolver for simulation (optional adapter flag later, mirroring Criterion B).  
4. Integrate into `aggregate_criterion_documents` when adapter enabled; preserve legacy path for old rows.

---

## 6. Missing features (summary)

- Evidence bundles and checklist validation for Criterion C  
- RRPA/COPC and approval-sheet structured requirements  
- Multi-accomplishment aggregation under one indicator type  
- Criterion C reviewer workspace UI  
- Mobile guided flow (optional but aligned with B)  
- OCR advisory-only policy for C  
- Automated tests for C aggregation, caps, and eligibility  
- Explicit policy for adviser **and** panel on same project  
- Adviser load (5/AY) reviewer guidance  

---

## 7. Recommended architecture

```
documents/criterion_c_evidence/
  bundle.py          # claim metadata (student, title, program, role, term)
  checklist.py       # approval_sheet, rrpa_copc, mentorship_* slots
  validation.py      # readyForReviewer, readyForScoring, blockers
  reviewer_assessment.py
  current_score.py   # reviewer assessment vs estimate
documents/scoring/
  criterion_c_simulation_adapter.py  # optional env flag (mirror B)
kra_configuration/
  criterion_c_annex.py   # indicator → points (from published config)
faculty/kra_document_aggregate.py  # branch for kra1-c when adapter on
web/js/criterion-c-workspace-ui.js
mobile/lib/... criterion_c_* (catalog, track screen)
```

**Storage:** JSON in `extracted_info` (`criterionCEvidenceBundle`) — consistent with Criterion B Phase 2 approach.

---

## 8. Suggested implementation phases

| Phase | Scope | Deliverable |
|-------|--------|-------------|
| **C0** | Policy sign-off | Aggregation (sum vs best-per-indicator), adviser+panel same project, OCR role |
| **C1** | Annex map + aggregation unit tests | `criterion_c_annex.py`, fix KRA C total math, cap 10 |
| **C2** | Evidence bundle + API | PATCH/GET routes, validation, no UI |
| **C3** | Reviewer Web workspace | Checklist, assessment save, readiness rows |
| **C4** | Faculty Mobile | Upload checklist + accomplishment metadata |
| **C5** | Simulation adapter + rank sim | Env-gated integration tests |
| **C6** | Staging regression | Sample advisories + mentor bundle E2E |

**Stop gates:** After C0 approval; before enabling simulation adapter in production; before any Alembic (if ever needed).

---

## 9. Risks and unresolved questions

1. **Under-counting** today for multiple UT/SP services under one indicator ID.  
2. **Over-counting** if duplicate uploads are not deduped by student+project hash.  
3. **OCR provisional scores** may inflate estimates without eligibility checks.  
4. **Adviser + panel** double credit on one thesis — official rule unclear.  
5. **Doctoral adviser (10 pts)** fills entire Criterion C — correct per table; reviewer must not exceed criterion cap on combined accomplishments.  
6. **Catalog vs rules** — mobile lacks inline evidence hints (depends on API/rules fetch).  
7. **Published Admin overrides** — edited indicator points must remain traceable to Annex A defaults.

---

## 10. Approval checkpoints

| # | Decision | Owner |
|---|----------|--------|
| 1 | Adopt **sum of distinct accomplishments** (deduped) vs keep **best per indicator** | Product / registrar policy |
| 2 | Allow **adviser and panel** points for same student/project? | CHED/SUC policy interpretation |
| 3 | Build **Criterion C evidence bundles** (JSON) vs extend generic documents only | Engineering |
| 4 | **Simulation adapter** for C (mirror B env flag) vs direct `verified_points` | Engineering |
| 5 | **OCR**: advisory-only for C (recommended) | Engineering + reviewers |
| 6 | **Migration**: JSON-only vs normalized tables | DBA / engineering |
| 7 | **Phased rollout** without changing historical `verified_points` on existing C uploads | Ops |

---

## Conclusion

| Verdict | Statement |
|---------|-----------|
| **Catalog / rules** | **Largely aligned** with Annex A point values and evidence lists (in-repo `rules.js`). |
| **Operational workflow** | **Generic document path** — **not** aligned with evidence-heavy, reviewer-gated JC process. |
| **Aggregation** | **Likely non-compliant** with “every service rendered” multi-instance counting. |
| **Criterion B parity** | Criterion C **needs its own** checklist + reviewer assessment workflow; **do not reuse** B formulas or Annex C contribution logic. |

**Phase 1 complete.** No implementation performed. Await approval on §10 before Phase C1+.

---

*Temporary PDF page renders used for this audit were deleted from the repo after inspection; re-render from the official PDF if re-verification is needed.*
