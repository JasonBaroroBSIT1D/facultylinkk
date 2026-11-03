# Criterion B — Complete-set workflow audit (modules & instructional manuals)

**Date:** 2026-11-03 (UTC+8)  
**Type:** Read-only audit (no code, data, or scoring changes)  
**Authority:** `backend/docs/2026-DBM-CHED-JC-01-Enhanced-Implementing-Guidelines-of-JC3-series-of-2022 (1).pdf` (image-only; structural mapping via in-repo `web/js/rules.js` and `CRITERION_B_2026_GUIDELINE_SCORING_AUDIT.md`)  
**Scope:** Faculty Mobile add-work wizard, upload metadata, evidence bundle validation, Reviewer Web readiness checklist  

---

## Executive summary

| Issue | Verdict |
|-------|---------|
| Co-authored module/manual missing “I attest this is a complete set” in Mobile wizard | **CONFIRMED BUG** (UI branching) |
| Same gap for co-authored manual as co-authored module | **CONFIRMED BUG** (same code path) |
| Reviewer sees two “Complete set attestation” rows (Verified vs Not attested) | **INTENDED DUAL REQUIREMENT** with **CONFIRMED UX BUG** (duplicate label, looks contradictory) |
| Separate attestation PDF mandatory in checklist | **APPLICATION CHOICE** — not listed as its own evidence line in in-repo JC indicator copy |
| Faculty boolean `completeSetDeclared` | **APPLICATION SAFEGUARD** — supports §13 completeness concept; not a separate official form named in `rules.js` |

**Stop here:** No fixes applied. Await approval before implementation.

---

## 1. Root cause — missing Mobile complete-set step (co-author)

### Mechanism

The teaching-material wizard is a fixed **5-step** linear flow in `mobile/lib/screens/criterion_b/criterion_b_add_work_screen.dart`. Step index **3** branches on authorship:

```243:281:mobile/lib/screens/criterion_b/criterion_b_add_work_screen.dart
      case 3:
        if (_withOthers == true) {
          return _question(
            'What was your contribution?',
            ...
          );
        }
        if (_materialKind != null && CriterionBMapper.showCompleteSetQuestion(_materialKind!)) {
          return _question(
            'Complete set',
            ...
            SwitchListTile(
              title: const Text('I attest this is a complete set'),
              value: _completeSet,
              ...
            ),
          );
        }
        ...
      default:
        return _question(
          'Ready to upload',
          ...
        );
```

- **Sole-authored module/manual:** index 3 → complete-set attestation; index 4 → “Ready to upload.”
- **Co-authored module/manual:** index 3 → contribution % only; index 4 → “Ready to upload.” The complete-set UI is **never rendered**.

`CriterionBMapper.showCompleteSetQuestion()` correctly returns true for both `module` and `manual` regardless of authorship (`criterion_b_mapper.dart` lines 47–49). The skip is purely **wizard branch order** (`_withOthers == true` takes precedence).

### Secondary effect — silent `completeSetDeclared: false`

Draft build always sets `completeSetDeclared` when the material kind is module or manual:

```113:115:mobile/lib/screens/criterion_b/criterion_b_add_work_screen.dart
        completeSetDeclared: CriterionBMapper.showCompleteSetQuestion(_materialKind!)
            ? _completeSet
            : null,
```

For co-authored module/manual, `_completeSet` defaults to **`false`** and is PATCHed after primary upload (`upload_document_screen.dart` → `_patchCriterionBMetadata`), even though the faculty member never saw the toggle.

### Guided upload hides the fallback toggle

On the primary guided flow (`criterionBPrimaryFlow`), metadata fields (including the complete-set switch) are **not shown**:

```831:834:mobile/lib/screens/documents/upload_document_screen.dart
          if (_isCriterionBPrimary && !_guidedPrimaryUpload) ...[
            const SizedBox(height: 14),
            _buildCriterionBMetadataFields(),
          ],
```

So co-authors using **Add work → Upload files** never get wizard **or** upload-form attestation. Non-guided manual upload **does** show “Complete stand-alone set attestation” for any indicator whose id contains `module` or `manual` (including `-co`).

### Backend still requires declaration

For `materialType` `module` or `instructional_manual`, validation requires `completeSetDeclared === true`:

```101:107:backend/documents/criterion_b_evidence/validation.py
    complete = bundle.get("completeSetDeclared")
    if material_type in ("module", "instructional_manual"):
        if complete is not True:
            flags.append("complete_set_not_attested")
            blockers.append(
                "Stand-alone or complete set attestation is required for modules and manuals (§13)."
            )
```

Co-author claims are **not** exempt in `required_slots()` — the attestation **slot** is required for sole and co alike (`checklist.py` lines 45–46).

---

## 2. Comparison — four module/manual flows

| Flow | Wizard: contribution step | Wizard: complete-set step | Guided upload: attestation UI | Draft may send `completeSetDeclared: false` | Backend: slot `complete_set_attestation` | Backend: `completeSetDeclared` |
|------|---------------------------|---------------------------|--------------------------------|---------------------------------------------|------------------------------------------|----------------------------------|
| **1. Sole module** | N/A | Yes (step 3) | Hidden on guided; toggle on non-guided upload | Only if user leaves switch off | Required | Required `true` |
| **2. Co module** | Yes (step 3) | **No** | Hidden on guided | **Yes (default false)** | Required | Required `true` |
| **3. Sole manual** | N/A | Yes (same as module) | Same | Same as sole module | Required | Required `true` |
| **4. Co manual** | Yes | **No** | Hidden on guided | **Yes (default false)** | Required | Required `true` |

**Textbook / multimedia:** no complete-set wizard step (`showCompleteSetQuestion` false); no `complete_set_attestation` slot (except multimedia has other slots).

**Indicator IDs:** `kra1-b-module-sole|co`, `kra1-b-manual-sole|co` (`criterion_b_annex.py`).

---

## 3. Explanation — “double attestation” on Reviewer Web

### What the reviewer sees

`buildReviewReadinessRows()` in `web/js/criterion-b-workspace-ui.js` builds rows from **two independent sources**:

1. **Checklist files** (`state.items`) — one row per slot that has a linked `documentId` in the bundle checklist. For `complete_set_attestation`, a verified upload shows e.g. **Uploaded · Verified**.
2. **Bundle metadata** — if `materialType` is module or manual and `bundle.completeSetDeclared !== true`, an **additional** row is appended with the **same label** “Complete set attestation” but **documentName “—”**, **upload “Missing”**, **review “Not attested”** (lines 243–255).

So both lines can appear simultaneously: file verified **and** faculty declaration missing. That is **expected given current backend rules**, not a sync bug between OCR and checklist status.

### Backend enforces both

| Requirement | Storage | Scoring gate |
|-------------|---------|--------------|
| Uploaded file in slot `complete_set_attestation` | `checklist.complete_set_attestation` | `missing_complete_set_attestation` until linked; all required slots must be **reviewer-verified** for `readyForScoring` |
| Faculty declaration | `bundle.completeSetDeclared` (boolean) | `complete_set_not_attested` flag + scoring blocker until `true` |

Verified upload **does not** set or imply `completeSetDeclared`. Reviewer PATCH on a file slot does not update the boolean.

### Simple review file list

`criterion-b-simple-review.js` only includes checklist entries **with** `documentId` in the step-through file list. The declaration gap appears on the **readiness checklist** (and server `scoringBlockers`), not necessarily as a separate file step — another source of reviewer confusion.

---

## 4. Official guideline vs FacultyLink implementation

### PDF access

PyPDF text extraction from the supplied JC PDF returned **no extractable text** (image-only), consistent with `CRITERION_B_2026_GUIDELINE_SCORING_AUDIT.md`. Page-level §13 quotes below rely on **in-repo** indicator definitions in `web/js/rules.js`, which mirror CHED checklist language — **human verification of the PDF is still required**.

### From in-repo indicator evidence (JC-aligned copy)

For **all** module and manual indicators (sole and co), official-style evidence lists include:

- *“Copy of the instructional material developed (complete set where applicable)”*

Conditions (module/manual sole; co rows share the same material copy line):

- *“A stand-alone module … or a complete series/set … earns full points.”*
- *“Incomplete sets are not awarded points.”*

Co-author rows add **Annex C** only; they do **not** add a separate “complete set attestation PDF.”

### Mapping to FacultyLink

| Concept | Official (in-repo copy) | FacultyLink |
|---------|-------------------------|-------------|
| Completeness applies to sole **and** co module/manual | Yes — same “complete set where applicable” on material copy | Yes — same slots + declaration for `authorship` sole and co |
| Stand-alone **or** complete set as acceptable forms | Yes (conditions text) | Partially — boolean wording “I attest this is a complete set” does not explicitly offer stand-alone vs series choice in UI |
| Separate **Complete Set Attestation** upload slot | **Not listed** as its own bullet in `rules.js` evidence arrays | **Added** — `complete_set_attestation` in `checklist.required_slots()` |
| Faculty **declaration** toggle | **Not named** as separate form in `rules.js` | **Added** — `completeSetDeclared` on bundle |
| Reviewer verifies completeness | Implied via material copy + conditions | Yes — reviewer verifies primary/supporting files; declaration is metadata check |

**Conclusion:** The **completeness rule** aligns with §13 intent. Requiring **both** a dedicated attestation **PDF slot** **and** an in-app boolean is **FacultyLink policy**, not explicitly spelled out in the in-repo official evidence bullets. The primary material upload may already satisfy “copy … (complete set where applicable)” if reviewers treat the main module/manual files as that copy.

---

## 5. Recommended consistent workflow (proposal only)

### Faculty Mobile (minimal)

1. **Teaching wizard:** Use **dynamic step count** for module/manual:
   - After authorship: if co → contribution % → **complete-set attestation** → ready to upload.
   - If sole → complete-set attestation → ready to upload (unchanged order).
2. **Do not PATCH `completeSetDeclared`** until the faculty explicitly acts (omit key or use `null` until toggle/on); avoid persisting default `false` for co-authored guided flows.
3. **Guided primary upload:** Show the same complete-set question (or a single combined “Completeness” step) before or after file pick for module/manual **including co**.
4. Copy: clarify **stand-alone course module/manual** vs **complete series/set** per §13 (plain language, one attestation covering what they uploaded).

### Reviewer Web (labels)

Split readiness into distinct rows (same underlying rules, clearer labels):

| Row label (proposed) | What it checks |
|----------------------|----------------|
| **Instructional material (completeness)** | Primary (and/or linked) files reviewer accepts as stand-alone or complete set |
| **Faculty completeness declaration** | `completeSetDeclared === true` |
| **Complete set attestation document** (if slot kept) | Optional/mandatory per approved policy — only if separate PDF remains required |

Use **Supporting evidence / Faculty declaration / Reviewer verification** subtitles in the readiness panel.

### Policy choice (needs your approval)

| Option | Description |
|--------|-------------|
| **A. Keep dual requirement, fix UX** | Retain slot + boolean; fix Mobile + rename reviewer rows (lowest legal risk if institutions already upload attestation PDFs). |
| **B. Declaration + primary material only** | Drop mandatory `complete_set_attestation` **slot**; completeness judged on **primary_material** verification + `completeSetDeclared` (closer to official evidence list). |
| **C. Slot only** | Require attestation upload; drop boolean (weak faculty audit trail). **Not recommended** without policy sign-off. |
| **D. Optional slot** | Boolean required; attestation PDF optional unless reviewer requests. |

**Do not remove the mandatory PDF slot without evidence and explicit approval** (per task instructions).

---

## 6. Backend validation impact (if fixes approved)

| Change | Validation / API |
|--------|------------------|
| Mobile sends declaration | More bundles reach `completeSetDeclared: true`; fewer `complete_set_not_attested` blockers |
| Stop default `false` PATCH | Existing `null` stays incomplete until attestation — no false “attested” |
| Merge slot into primary (Option B) | `required_slots()` shrink; migration of existing checklist links; `missing_complete_set_attestation` retired or softened |
| Label-only Web fix | None |
| Grandfather legacy | Bundles with verified slot but `completeSetDeclared` null/false — need explicit legacy rule (see §7) |

`readyForScoring` remains: all required slots **verified** + no blockers + co % + specialization (`validation.py`). No scoring formula or cap changes.

---

## 7. Existing-record compatibility

| Record pattern | Today | Risk if Mobile fixed |
|----------------|-------|----------------------|
| Co module, no declaration, no attestation file | Blocked from `readyForScoring` | None — faculty prompted to attest |
| Co module, **verified attestation file**, `completeSetDeclared` false/null | Reviewer sees **dual rows**; scoring still blocked | Fix declaration only; do not unverify files |
| Sole module, attested in wizard | Works | None |
| Legacy `completeSetDeclared: false` from silent PATCH | Incorrect negative attestation | Consider treating as `null` if never shown in UI ( **policy decision** ) |

**No automatic DB rewrites** recommended without backup and approval.

---

## 8. Files that would need modification (after approval)

| Area | Files |
|------|--------|
| Mobile wizard | `mobile/lib/screens/criterion_b/criterion_b_add_work_screen.dart` |
| Mobile upload / PATCH | `mobile/lib/screens/documents/upload_document_screen.dart` |
| Mobile copy | `mobile/lib/data/criterion_b_ux.dart` (optional) |
| Reviewer readiness UI | `web/js/criterion-b-workspace-ui.js` |
| Reviewer simple review | `web/js/criterion-b-simple-review.js` (optional: declaration step) |
| Backend slots (Option B only) | `backend/documents/criterion_b_evidence/checklist.py`, `validation.py` |
| Docs | `backend/docs/CRITERION_B_EVIDENCE.md` |
| Tests | See §9 |

---

## 9. Tests to add (after implementation)

1. **Mobile widget/flow:** co module → wizard includes complete-set step after contribution; sole manual unchanged.
2. **Mobile PATCH:** co guided draft does not send `completeSetDeclared: false` without user interaction.
3. **Backend:** module co — `completeSetDeclared true` + all slots verified → `readyForScoring`; false → blocker.
4. **Backend:** sole vs co — same `required_slots` includes `complete_set_attestation`.
5. **Web JS:** readiness rows — verified file + missing declaration produces **two distinguishable labels** (post-fix).
6. **Regression:** Criterion B 30 cap, KRA 100, simulation adapter unchanged.

---

## 10. Items requiring your approval

1. **Policy:** Keep mandatory `complete_set_attestation` **PDF slot**, or move completeness to **primary material + declaration only** (Options A vs B).
2. **Legacy silent `false`:** Reset to `null` vs require faculty re-attestation.
3. **Wording:** Stand-alone vs complete **set/series** in faculty UI (align §13 language).
4. **Any schema/slot change** — forward-only bundle handling; no destructive PG ops without backup.

---

## Conclusion blocks

### CONFIRMED BUGS

1. Co-authored **module** and **manual** Add-work wizard skips the complete-set attestation step (mutually exclusive branch at wizard index 3).
2. Co-authored guided flow may PATCH **`completeSetDeclared: false`** without showing the control.
3. Reviewer readiness uses the **same label** for verified **upload** vs missing **faculty declaration**, appearing contradictory.

### INTENDED BEHAVIOR

1. Modules and manuals (sole **and** co) require **`completeSetDeclared === true`** for scoring readiness.
2. Modules and manuals require checklist slot **`complete_set_attestation`** with reviewer-verified upload (application checklist design).
3. Verified attestation **document** does **not** substitute for faculty **declaration** under current backend rules.

### GUIDELINE UNCERTAINTIES

1. Image-only PDF — exact §13 wording and Annex A table cells not machine-verified in this audit.
2. Whether a **separate** attestation PDF is required nationwide vs satisfying completeness through the **primary material copy** only.
3. Whether co-authored completeness must be attested **per co-author** or once per shared material (FacultyLink: per faculty claim bundle).

### PROPOSED FIXES (await approval)

1. **Mobile:** Add complete-set step for co module/manual; dynamic `_pageCount`; stop silent false PATCH; show attestation on guided upload.
2. **Reviewer Web:** Rename/split readiness rows (faculty declaration vs attestation document vs primary completeness).
3. **Optional policy follow-up:** Reconcile attestation **slot** with official “copy of instructional material” evidence list (Option A or B above).

---

*End of audit — no implementation performed.*
