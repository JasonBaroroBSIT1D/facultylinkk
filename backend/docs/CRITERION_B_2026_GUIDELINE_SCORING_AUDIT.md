# KRA I — Criterion B scoring audit (2026 DBM–CHED JC 01)

**Audit type:** Read-only code and data review  
**Authority:** `backend/docs/2026-DBM-CHED-JC-01-Enhanced-Implementing-Guidelines-of-JC3-series-of-2022 (1).pdf`  
**Date:** 2026-11-03 (UTC+8)  
**Scope:** Scoring math, evidence validation, reviewer assessment, KRA aggregation, rank simulation  
**Out of scope:** No database writes, score changes, formula changes, or adapter toggles  

---

## Executive verdict: **NEEDS CORRECTION** (process gaps) + **INCONCLUSIVE** (official PDF page text)

| Layer | Verdict | Summary |
|-------|---------|---------|
| Core co-author formula (`base × documented % ÷ 100`) | **PASS** | Matches JC §12 sample logic and in-repo Annex A mapping; **does not** hard-code 50% or 15 points. |
| Published caps (Criterion B 30, KRA I 100) | **PASS** | Enforced via published Admin `kraSettings` with documented fallbacks. |
| Evidence / OCR vs reviewer verification | **WARNING** | Design intent is reviewer-gated; Jason test bundle shows **verified** slots on **synthetic** Annex C text. |
| Contribution % vs Annex C content | **NEEDS CORRECTION** | No server rule compares `bundle.contributionPercent` to OCR/Annex C extracted allocation. |
| Jason Baroro official Annex C allocation | **INCONCLUSIVE** | Bundle and test PDF both say **50%**; PDF explicitly disclaims authenticity — **not** an official JC determination. |
| Rank simulation / KRA (adapter ON) | **PASS** | Uses canonical current score; supporting docs excluded. |

**Overall:** **NEEDS CORRECTION** for verification gaps that could allow self-reported % to drive estimates without Annex C reconciliation. **INCONCLUSIVE** for line-by-line PDF §§11–14 page citations (see below).

---

## PDF access limitation (Sections 11–14)

PyPDF extraction of pages 7–11 returned **no text** (image-only PDF). This matches the prior finding in `CRITERION_B_AGGREGATION_POLICY.md`.

**Human action required:** Manually confirm page numbers and wording in §§11–14 and Annex A/C tables against this audit.

**Structural mapping used in FacultyLink (in-repo, not re-invented):**

| Guideline focus | FacultyLink interpretation | Primary references |
|-----------------|----------------------------|--------------------|
| **§11 — Criterion B (Instructional materials & new/revised programs)** | Criterion `kra1-b`; combined instructional + program outputs; **criterion max 30** | `criterion_b_annex.py`, `published_criterion_b_max()` |
| **§12 — Instructional materials developed & approved for use** | Evidence checklist: primary material, IMDC approval, syllabus/course guide, library availability, specialization alignment; co-authorship requires **documented contribution** | `CRITERION_B_EVIDENCE.md`, `validation.py`, `checklist.py` |
| **§13 — Types of instructional materials** | `materialType`: textbook, module, manual, multimedia; module/manual **complete set** attestation | `checklist.required_slots()` |
| **§14 — Academic programs developed/revised & implemented** | Separate program bundle + `program_validation.py` (not Jason case) | `CRITERION_B_PROGRAM_EVIDENCE.md` |
| **Annex A point rows** | Sole/base indicator IDs in Admin config; co indicators share base | `criterion_b_annex.py` |
| **Annex C contribution allocation (§12 sample)** | Textbook **30** total; Faculty A **60% → 18**; Faculty B **40% → 12** (examples, not fixed percentages) | `test_criterion_b_scoring.py::test_co_author_percentage` |

Official sample formula (FacultyLink implementation):

```text
Contribution points = published_base × (documented_contribution_percent / 100)
```

Then apply **Criterion B ceiling** (published max, default **30**) and **KRA I ceiling** (default **100**).

---

## Task 1 — Scoring implementation map

| Concern | Module / function | Role |
|---------|-------------------|------|
| Annex row / indicator IDs | `kra_configuration/criterion_b_annex.py` | Maps 10 indicator IDs → 6 Annex A rows; co rows require contribution % |
| Base points from Admin | `published_base_points_for_annex_row()` in `criterion_b_scoring.py` | Reads **sole/base** indicator only (co uses same base) |
| Verified scoring | `compute_criterion_b_indicator_points()` | Requires `evidence_verified=True`; co uses `contribution_percent` |
| Pre-verification estimate | `compute_criterion_b_indicator_automated_estimate()` | Same math **without** requiring verification |
| Contribution validation | `validate_contribution_percent()` | 0–100; rejects missing/invalid |
| Instructional bundle validation | `validate_instructional_material_bundle()` | Checklist + co % + specialization; **OCR never sets verified** |
| Canonical current score | `resolve_criterion_b_current_score()` in `current_score.py` | Reviewer Assessed (points + justification) overrides Estimated |
| Guideline audit points | `guideline_verified_points_if_ready()` | Rule-based points when `readyForScoring` |
| Reviewer proposed score | `apply_reviewer_proposed_assessment()` in `reviewer_assessment.py` | Cap via `allowed_assessment_max_points()`; min justification length |
| API scoring context | `build_criterion_b_scoring_context()` | Separates estimate, guideline-compliant, reviewer proposed |
| Simulation adapter | `score_primary_document_for_simulation()`, `aggregate_criterion_b_simulation_from_documents()` | Uses **current score** when eligible; dedupe keys |
| KRA aggregation | `aggregate_criterion_documents_from_list()` in `kra_document_aggregate.py` | Criterion B via adapter when env ON |
| Rank simulation | `compute_rank_simulation()` in `rank_simulation_engine.py` | Calls KRA aggregation (same Criterion B path) |
| Supporting docs excluded | `is_supporting_evidence_document()`, `document_evidence_points` | Supporting rows do not score as separate accomplishments |
| Dedup / cap | `criterion_b_aggregation.py`, `cap_criterion_b_total()` | Per-output dedupe; sum capped at 30 |

**Published config (live DB, read-only):** Textbook sole/base **`kra1-b-textbook-sole`** → **30** points; Criterion B max **30**; KRA I max **100** (via `published_settings_blob()` at audit time).

---

## Task 2 — Co-author contribution scoring audit

### Does FacultyLink assume 50% or 15 points for every co-author?

**No** in backend scoring logic.

- Co score: `base × (contribution_percent / 100)` when verified (`compute_criterion_b_indicator_points`, lines 171–194).
- Unit tests explicitly use **60% → 18** and **40% → 12** on base 30 (`test_co_author_percentage`).
- **15 points** appears only when `contribution_percent=50` and base=30 (test `test_automated_estimate_before_verification`) — illustrative, not a default constant in production code.
- Default bundle template sets `contributionPercent: null` (`bundle.py`); co claims **fail** validation without a valid %.

### Where does contribution % come from?

| Source | Used for scoring? |
|--------|-------------------|
| Faculty PATCH / upload body `contributionPercent` | **Yes** — stored on `criterionBEvidenceBundle` |
| Reviewer PATCH | Can update bundle fields via evidence-bundle API |
| OCR / Annex C PDF | **No automatic write** to `contributionPercent` (no matches under `documents/ocr/`) |
| Annex C slot `verified` | Required for co `readyForScoring`, but **does not parse % from OCR into bundle** |

### Reviewer assessment cap

`allowed_assessment_max_points()`:

- Co: `base × (bundle.contributionPercent / 100)` when % valid.
- If co but % **missing**: returns **full base** (30 for textbook) — **WARNING**: reviewer could propose up to full base until % is recorded (API should still block incomplete validation for `readyForScoring`).

**Finding:** Engine math aligns with §12 **when** `contributionPercent` reflects the **official documented** Annex C allocation. FacultyLink does **not** yet enforce that the documented % equals Annex C content.

---

## Task 3 — Jason Baroro textbook (`doc_64d33454ab0f`)

Read-only snapshot (2026-11-03):

| Item | Value |
|------|--------|
| Indicator | `kra1-b-textbook-co` |
| Authorship | `co` |
| Material type | `textbook` |
| Title | Introduction to Data Literacy: A Collaborative Textbook |
| `contributionPercent` (bundle) | **50** |
| Published textbook base | **30** |
| Automated estimate (formula) | **30 × 50 / 100 = 15** |
| Guideline-compliant verified (ready) | **15** |
| Allowed reviewer max | **15** |
| Reviewer assessment | **14** (justification present; distinct from estimate) |
| Current score | **14**, source **reviewer_assessment** |
| `readyForScoring` | **true** |
| Specialization aligned | **true** |

### Authorship & contribution

- Claim is correctly filed as **co-author textbook**, not sole.
- **Recorded contribution:** **50%** on the bundle (faculty/reviewer-entered field, not a scoring-engine default).

### Annex C evidence (`doc_5149570d90a2`)

- Checklist slot `annex_c_contribution`: **verified** (reviewer action).
- OCR excerpt (stored on supporting doc) states **“Jason Baroro: 50% (fictional test percentage)”** and **“NOT A REAL CERTIFICATION” / synthetic test data**.

**Official documented contribution percentage (DBM–CHED / authentic Annex C):** **UNKNOWN** — only test/simulated documentation is on file.

**FacultyLink test-data contribution:** **50%** (bundle + synthetic Annex C text agree).

### Why 15-point estimate?

1. Published Admin base for textbook row = **30**.
2. Co-author indicator uses **50%** from bundle.
3. `compute_criterion_b_indicator_automated_estimate` → **15**.
4. With full checklist verified, `guideline_verified_points_if_ready` → **15**.

No hidden “co-author ceiling of 15” — it is exactly **half of 30** given **50%**.

### Is reviewer **14** allowable?

**Yes** within FacultyLink rules: **14 ≤ allowedReviewerMax (15)**; justification stored; estimate **15** preserved in `systemEstimatePoints` / scoring context.

### Was 50% defaulted by the system?

**No** for backend scoring. **50** is stored on the bundle. UI may offer **50** as a select option in reviewer workspace (`evidence-workspace.js`); mobile requires faculty entry for co-author flows. The value matches **synthetic** Annex C test content, not proof of official allocation.

---

## Task 4 — Document validation audit

### Required vs conditional vs reviewer judgment

| Requirement (guideline-aligned design) | Implementation | OCR role |
|----------------------------------------|----------------|----------|
| Original primary instructional material | Slot `primary_material` | Hint only; reviewer **verified** |
| IMDC evaluation & approval | `imdc_evaluation_approval` | Same |
| Approved syllabus / course guide | `approved_syllabus` | Same |
| Library availability | `library_certification` | Same |
| Specialization alignment | `specializationAligned` boolean | Reviewer/faculty; `false` blocks |
| Annex C (co-author) | `annex_c_contribution` + `contributionPercent` | Slot can be verified **without** parsing % into bundle |
| Module/manual complete set | `completeSetDeclared` + attestation slot | N/A for textbook |
| Multimedia originality / pedagogical proof | Extra slots | N/A for textbook |

Jason checklist (all **verified**): primary, IMDC, syllabus, library, Annex C.

**WARNING (Jason):** Verification flags align with **FacultyLink workflow**, but attached Annex C OCR text is **explicitly fictional**. Reviewer **verified** does not automatically mean **guideline-authentic** in the real-world sense.

**FAIL (process, not math):** No automated check that textbook-specific **publication/copyright** rules in §12–13 are satisfied beyond generic primary + IMDC + syllabus + library slots (no dedicated “copyright page / ISBN / publisher” slot in instructional checklist).

---

## Task 5 — Reviewer scoring audit

| Rule | Status |
|------|--------|
| Reviewer cap tied to published base × % (co) | **PASS** |
| Justification required (min length) | **PASS** (`MIN_JUSTIFICATION_LEN = 10`) |
| Reviewer score cannot exceed `allowed_assessment_max_points` | **PASS** (API validation) |
| Distinct from official DBM–CHED-awarded points | **PASS** (documented in scoring context notes + simulation note) |
| Automated estimate preserved | **PASS** (`systemEstimatePoints` / `preservedAutomatedEstimatePoints` = **15** while current = **14**) |
| Silent 15-point co-author ceiling | **PASS** — no such ceiling; 15 is **50% of 30** only |

Jason’s **14** is **reviewer professional assessment** under cap **15**, not a formula bug.

---

## Task 6 — KRA aggregation & rank simulation

| Check | Result |
|-------|--------|
| Criterion B max **30** | **PASS** — `published_criterion_b_max` / aggregation |
| KRA I max **100** | **PASS** — `cap_kra1_instruction_total` / rank engine |
| Supporting docs not scored as primaries | **PASS** — adapter skips supporting links |
| One current score per primary | **PASS** — `resolve_criterion_b_current_score` |
| Reviewer Assessed replaces Estimated for aggregation when complete | **PASS** — Jason aggregates **14**, not 15 |
| Adapter remains ON | **Unchanged** — no config modified in this audit |

---

## Task 7 — Findings summary (PASS / WARNING / FAIL)

| ID | Finding | Severity |
|----|---------|----------|
| F1 | Co-author math uses `base × % / 100`, not fixed 50%/15 pts | **PASS** |
| F2 | §12 example (60/40 → 18/12) covered by unit tests | **PASS** |
| F3 | Caps 30 / 100 from published config | **PASS** |
| F4 | OCR does not auto-set verified or contribution % | **PASS** |
| F5 | No reconciliation: `bundle.contributionPercent` vs Annex C OCR text | **FAIL** / **NEEDS CORRECTION** |
| F6 | Co reviewer max falls back to **full base** if % missing | **WARNING** |
| F7 | Jason Annex C is synthetic; **verified** anyway | **WARNING** (data/process) |
| F8 | Official JC PDF §§11–14 pages not machine-readable | **INCONCLUSIVE** |
| F9 | Textbook copyright/publication specifics not modeled as dedicated evidence slots | **WARNING** |
| F10 | Jason official Annex C % for real compliance | **INCONCLUSIVE** |

---

## Recommended fixes (not implemented — await approval)

1. **Annex C reconciliation:** When slot `annex_c_contribution` is verified, require reviewer confirmation (or structured extraction) that **documented %** matches bundle `contributionPercent`; flag mismatches in validation.
2. **Do not treat OCR % as authoritative** — keep reviewer attestation; optionally surface OCR-extracted % as read-only hint only.
3. **Tighten `allowed_assessment_max_points`:** If co and % missing, cap at **0** or block assessment API (align with `contribution_percent_required`).
4. **Evidence authenticity warnings:** Surface OCR/disclaimer text (e.g. “TEST DATA ONLY”) in reviewer UI when marking slots verified.
5. **Optional slots** for textbook publication/copyright evidence if §12–13 require — map to checklist after manual PDF review.
6. **Human PDF sign-off:** Complete §§11–14 page-level checklist against `2026-DBM-CHED-JC-01-...pdf`.

### Potential impact on existing accomplishments

- If (1) or (3) were implemented, some co-author claims with **unverified % alignment** might lose `readyForScoring` or lower **allowed reviewer max** until corrected — **Jason** might need bundle/Annex C reconciliation ( **14** assessment could remain valid if within corrected max).
- Recalculating estimates when **true** official % differs from bundle would change automated/guideline lines (e.g. 40% → 12 instead of 15).
- No impact from this audit run (read-only).

---

## Jason score narrative (audit conclusion)

| Score | Explanation |
|-------|-------------|
| **15** estimate | Published textbook base **30** × bundle **50%**; not an invented co-author default. |
| **15** guideline verified | Same formula with `readyForScoring=true`. |
| **14** reviewer | Valid professional adjustment ≤ cap **15**; estimate retained for audit. |
| **14** KRA / simulation | Canonical current score with adapter ON. |

---

## Sign-off

| Role | Result |
|------|--------|
| **Formula vs JC §12 sample (base × documented %)** | **COMPLIANT** in code |
| **End-to-end evidence authenticity (Jason)** | **INCONCLUSIVE** / **NEEDS CORRECTION** |
| **Implementation ready for official DBM–CHED certification without human PDF + Annex C reconciliation** | **No** |

**Do not implement corrections until explicitly approved.**
