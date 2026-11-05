# KRA III & IV — Metadata Forms and OCR Integration Fix

**Date:** 2026-11-05

## Root cause

The Reviewer Evidence Workspace reuses `FL.kra2AWorkspaceUi` (built for KRA II research/creative outputs). For KRA III and IV indicators, `metadataFormFields()` and `compactReviewPageHtml()` fell through to the **publication/research** field set (authors, venue, DOI, publication date). `workflowFamily()` only understands `kra2-*` tokens, so e.g. `kra4-a-member` was treated like a generic publication.

Backend metadata schemas in `kra3_workflow.py` / `kra4_workflow.py` and OCR hint parsing were already indicator-aware; the **reviewer web UI did not consume them**.

## Files modified

| Area | Files |
|------|--------|
| Reviewer UI | `web/js/kra34-workspace-metadata.js` (new), `web/js/kra2-a-workspace-ui.js`, `web/js/kra2-a-review.js` |
| Page scripts | `web/pages/reviewer/document-review.html`, `web/pages/reviewer/documents.html`, `web/pages/admin/document-view.html` |
| Validation | `backend/documents/kra3_evidence/validation.py`, `backend/documents/kra4_evidence/validation.py` |
| Labels | `backend/kra_configuration/kra3_workflow.py`, `backend/kra_configuration/kra4_workflow.py` |
| OCR | `backend/documents/kra4_evidence/ocr_extraction.py` (reads `extracted_text`; unchanged hints logic) |
| Tests | `backend/tests/documents/test_kra34_validation_metadata.py` (new) |

## Indicator metadata mapping

- **Source of truth:** `metadata_field_ids()` + `metadata_field_label()` in `kra3_workflow.py` / `kra4_workflow.py`, exposed on API as `metadataFields` in evidence-bundle payloads.
- **UI:** `FL.kra34Metadata.formFields()` prefers API `metadataFields`; fallback lists mirror workflow families (linkage, extension project, organization, education, training, paper, award, prior experience, etc.).
- **KRA IV Criterion A (membership):** organization name, participation role, membership dates — **no** authors/venue/DOI.
- **KRA III:** per-family fields (linkage, CSR, designation, resource person, …) — **no** research output fields.

## OCR integration

- Unchanged pipeline: upload → OCR job → `Document.extracted_text` → `ensure_kra3/kra4_ocr_extraction()` → `hints` → `merge_ocr_into_bundle()`.
- Reviewer UI reads `payload.ocrExtraction.hints` (and legacy `kra3OcrExtraction` / `kra4OcrExtraction` keys).
- **Extracted document information** table: Field | OCR value | Source | OCR status | Reviewer correction.
- Missing OCR values show **“Not detected”** (no fabrication).
- **Apply OCR to corrections** / **Save corrections** PATCH bundle fields via existing `_apply_bundle_metadata_fields` (reviewer actor).

## Reviewer UI changes

- Removed large **“Confirm accomplishment metadata”** panel for KRA III/IV (`metadataPanelNeeded` → false).
- Replaced research **Accomplishment details** block with indicator-specific key/value rows.
- Save Assessment / Approve / Reject flows unchanged; metadata confirmation is **not** a separate approval gate.
- KRA II behavior unchanged (still uses confirm-metadata panel when validation flags require it).

## API changes

- None (no new routes). Validation only: dropped `metadata_not_confirmed` from KRA III/IV **approval blockers** when values are present; missing required fields still block via existing `missing_*` checks.

## Tests executed

| Test | Result |
|------|--------|
| `pytest tests/documents/test_kra34_validation_metadata.py` | **PASS** (2) |
| `pytest tests/documents/test_kra4_qa_sandbox_scoring.py tests/kra_configuration/test_kra4_*.py` | **PASS** (12, prior suite) |

Not re-run this pass: full live QA, Playwright browser, Flutter device, rank simulation.

## Reviewer back navigation (KRA III & IV)

**Problem:** Back from accomplishment review used `documents.html?...&indicator=...`, which opened the per-indicator document grid instead of the criterion overview (stats + accomplishment list).

**Fix:** `reviewContextBackHref` returns criterion-only URLs for KRA III/IV; evidence workspace strips legacy `indicator` query params for `kra3-*` / `kra4-*` routes (same pattern as KRA II). Scroll position before “Open Review” is stored in `sessionStorage` and restored on return when practical.

## Remaining limitations

1. Faculty mobile “Check your work” screens may still use older layouts — reviewer web is fixed; align mobile in a follow-up if needed.
2. OCR confidence scores are shown as status (pending/completed/failed), not per-field confidence (backend does not expose per-field scores yet).
3. Approval still requires evidence checklist verification and remarks — intentionally stricter than metadata alone.
