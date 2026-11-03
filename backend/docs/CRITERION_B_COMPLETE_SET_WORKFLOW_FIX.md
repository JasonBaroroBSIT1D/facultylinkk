# Criterion B — Complete-set workflow fix (implementation report)

**Date:** 2026-11-03  
**Basis:** `CRITERION_B_COMPLETE_SET_WORKFLOW_AUDIT.md`  
**Scope:** Faculty Mobile wizard/upload, Reviewer Web readiness labels only — **no** backend validation, scoring, DB, or adapter changes.

---

## Files modified

| File | Change |
|------|--------|
| `mobile/lib/data/criterion_b_teaching_wizard_flow.dart` | **New** — testable step sequence for teaching wizard. |
| `mobile/lib/screens/criterion_b/criterion_b_add_work_screen.dart` | Dynamic steps; co module/manual get complete-set step; new copy; `bool?` declaration (no silent false). |
| `mobile/lib/screens/documents/upload_document_screen.dart` | Skip duplicate complete-set UI when wizard captured declaration; PATCH only on explicit user touch (non-draft). |
| `web/js/criterion-b-workspace-ui.js` | Distinct readiness labels; faculty confirmation row always shown for module/manual. |
| `mobile/test/criterion_b_teaching_wizard_flow_test.dart` | **New** — four material/authorship combinations. |
| `mobile/test/criterion_b_add_work_test.dart` | Widget tests for co module, sole manual, confirmation gate. |
| `web/tests/complete-set-readiness-labels.test.js` | **New** — reviewer label separation. |

---

## Root causes fixed

1. **Wizard branch at index 3** — co-author path showed contribution only and skipped complete-set (`_withOthers == true` branch).
2. **Silent `completeSetDeclared: false`** — draft always sent `_completeSet` default `false` for module/manual.
3. **Reviewer duplicate title** — same label used for checklist file row and faculty boolean row.

---

## Updated wizard flows (teaching)

| Flow | Steps after title |
|------|-------------------|
| Sole module / manual | Authorship → **Complete Instructional Material** → Ready to upload |
| Co module / manual | Authorship → Contribution % → **Complete Instructional Material** → Ready to upload |
| Sole/co textbook or multimedia | Unchanged (no complete-set step) |

Faculty must turn **Yes, I confirm** on before **Next** on the complete-set step. Draft/API includes `completeSetDeclared` only after the faculty toggles the switch (true or explicit false).

Guided upload **does not** show the upload-form switch when the wizard already set `completeSetDeclared`.

---

## Updated Reviewer Web labels

| Check | Label | Status examples |
|-------|--------|-----------------|
| Checklist slot `complete_set_attestation` | **Complete Set Supporting Document** | Uploaded / Verified / Missing / Pending review |
| Bundle `completeSetDeclared` | **Faculty Completeness Confirmation** | Confirmed / Not yet confirmed |

Verified supporting document does **not** set faculty row to Confirmed. Claim detail KV row renamed to **Faculty completeness confirmation**.

Backend requirements unchanged (both still required for `readyForScoring`).

---

## Test results

| Suite | Result |
|-------|--------|
| `flutter test test/criterion_b_teaching_wizard_flow_test.dart test/criterion_b_add_work_test.dart test/contribution_verification_display_test.dart` | **13 passed** |
| `node web/tests/complete-set-readiness-labels.test.js` | **passed** |
| `node web/tests/contribution-verification-readiness.test.js` | **passed** |
| `pytest tests/documents/test_contribution_confirmation.py tests/documents/test_criterion_b_evidence.py tests/staging/test_criterion_b_activation_scenarios.py` | **28 passed** |

**Live browser / device testing:** Not performed in this session (automated tests only).

---

## Remaining issues

1. **Separate attestation PDF slot** vs official “copy of instructional material” — policy review still pending (audit Option A/B).
2. **Legacy bundles** with `completeSetDeclared: false` from old silent PATCH — not auto-corrected (data preservation).
3. **Mobile evidence panel** still shows generic “Complete set declared” (unchanged this task).
4. **Backend scoring blocker text** still references “Complete set attestation” in API messages — reviewer UI labels clarified; API strings unchanged.

---

## Manual verification steps

1. **Mobile — co module:** Add work → Module → title → with others → 50% → confirm complete → upload; verify no second complete-set question on upload screen.
2. **Mobile — sole manual:** Complete-set step appears; cannot proceed until switch on.
3. **Reviewer Web:** Module claim with verified attestation file but `completeSetDeclared` false → two **different** row titles; faculty row blocks finalize.
4. **Reviewer Web:** After faculty confirms → faculty row **Confirmed**; file row still requires separate verification.
5. **Regression:** Co-author Annex C contribution confirmation flow unchanged.

---

*No PostgreSQL changes, no scoring changes, no adapter toggle.*
