# KRA II Criterion C — all-25 workflow status

**Date:** 2025-11-04  
**Verdict:** **NOT COMPLETE** — shared workflows and automated tests cover all 25 indicators; live Faculty Mobile and Reviewer Web QA per indicator remain **NOT TESTED**.

## What was delivered

| Area | Status | Notes |
|---|---|---|
| 25-indicator audit matrix | **PASS** | `docs/KRA2_CRITERION_C_COVERAGE_MATRIX.md` (generated) |
| Reusable Check screen (API slots) | **PASS** | `kra2_review_submit_screen.dart` — all C indicators |
| Indicator-aware metadata | **PASS** | `kra2_c_workflow.py`, mobile `Kra2Catalog`, reviewer `kra2-a-workspace-ui.js` |
| OCR routing (families) | **PASS** | literary, film, exhibition, music_work, performance, creative |
| Evidence checklist (backend authority) | **PASS** | `requiredEvidenceSlots` / `slotLabels` from API |
| Submission validation | **PASS** | Backend validation + mobile `_canSubmitForReview` |
| Admin scoring | **PASS** | Unchanged; published config only |
| Reviewer metadata + slots | **PASS** | C-specific form fields; no `publicationReference` on C |

## Automated test matrix

| Suite | Result |
|---|---|
| `test_kra2_criterion_c_workflow_matrix.py` (×25 metadata/slots/OCR profile) | **PASS** |
| `test_kra2_criterion_c_ocr_routing.py` (family samples + acting invention guard) | **PASS** |
| `test_kra2_criterion_c_checklist_sync.py` (backend ↔ web ↔ mobile slots) | **PASS** |
| `mobile/test/kra2_criterion_c_all_indicators_test.dart` | **PASS** (after `ensureLoaded`) |
| `mobile/test/kra2_criterion_c_acting_test.dart` | **PASS** |

## Live QA (NOT TESTED)

| Workflow | Faculty Mobile | Reviewer Web |
|---|---|---|
| Upload / Replace / View per slot | NOT TESTED | NOT TESTED |
| OCR advisory + faculty edit | NOT TESTED | NOT TESTED |
| Send for Review blockers | NOT TESTED | NOT TESTED |
| Approval + scoring + Rank Simulation | NOT TESTED | NOT TESTED |

## Remaining gaps

1. Device/browser E2E with real PDFs/images per creative family (music, dance, theater, visual, film, literary).
2. Optional: expose `criterion_c_subfamily` via API so mobile/web do not duplicate prefix rules (today kept in sync by pytest label parity tests).
3. Playwright reviewer spec for Criterion C (mirror Criterion B pattern) — not added in this pass.

## Key files

- Backend workflow: `backend/kra_configuration/kra2_c_workflow.py`
- OCR: `backend/documents/kra2_evidence/ocr_extraction.py`, `ocr_profiles.py`
- Evidence slots: `backend/documents/kra2_evidence/kra2_c_evidence_slots.py`
- Mobile: `mobile/lib/data/kra2_catalog.dart`, `mobile/lib/screens/kra2/kra2_review_submit_screen.dart`
- Reviewer: `web/js/kra2-a-workspace-ui.js`

Regenerate coverage doc:

```bash
cd backend && python scripts/generate_kra2_c_coverage_matrix.py
```
