# Criterion C OCR-first research advising workflow

## Summary

Faculty **no longer enter** project title, student names, group, academic year, or approval date **before** uploading evidence for **research advising / panel** accomplishments. Mentorship flow is unchanged (manual details before upload).

New research flow:

1. Choose research type and role (existing wizard).
2. Upload the **signed approval sheet** as the primary document.
3. Existing Tesseract OCR runs via the document OCR queue.
4. Backend parses OCR text into advisory `criterionCOcrExtraction` and merges empty bundle fields.
5. Mobile shows an **editable confirmation** screen (`CriterionCResearchConfirmScreen`).
6. Faculty confirm or correct; PATCH sets `metadataConfirmed` so later OCR cannot overwrite corrections.
7. Faculty upload remaining checklist items (RRPA/COPC, etc.) via the existing requirements screen.
8. Existing bundle validation and reviewer scoring are unchanged.

## Backend

| Area | Change |
|------|--------|
| `documents/criterion_c_evidence/ocr_research.py` | Parse approval-sheet OCR; merge into bundle; link primary doc to `approval_sheet` slot; hook after OCR success |
| `documents/criterion_c_evidence/metadata_merge.py` | Preserve faculty-confirmed bundle fields across OCR merges (mirrors Criterion B pattern) |
| `documents/ocr/queue.py` | After OCR success, call `apply_criterion_c_research_ocr` and preserve Criterion C JSON |
| `documents/criterion_c_evidence/service.py` | Research bundle init links approval sheet; PATCH marks `metadataConfirmed`; evidence-bundle API exposes `ocrStatus` and `ocrExtraction` |

OCR is **advisory only** — no auto-verification of slots or review approval.

## Mobile

| File | Change |
|------|--------|
| `criterion_c_add_work_screen.dart` | Removed pre-upload research details step; ready step directs approval-sheet upload |
| `document_flow_args.dart` | `criterionCOcrFirstResearch`, optional `projectTitle` on draft |
| `upload_document_screen.dart` | Skip pre-OCR metadata PATCH for OCR-first research; navigate to confirm screen |
| `criterion_c_research_confirm_screen.dart` | OCR status, retry, editable fields, PATCH with `confirmMetadata` |
| `criterion_c_evidence.dart` | API fields + `CriterionCResearchMetadataForm` |
| `api_client.dart` / `app_state.dart` | `retryFacultyDocumentOcr` |

## Tests

| Suite | Command | Result |
|-------|---------|--------|
| Backend OCR + C1 regression | `pytest tests/documents/test_criterion_c_ocr_research.py tests/documents/test_criterion_c_phase_c1.py -q --noconftest` | **26 passed** |
| Flutter Criterion C | `flutter test test/criterion_c_mobile_test.dart` | **15 passed** |

Coverage includes: extraction accuracy, missing fields (no fabrication), confirmed-metadata preservation on re-OCR, incomplete validation blockers, evidence-bundle regression (phase C1), confirmation UI mapping, and PATCH confirm flag.

## Out of scope (unchanged)

- Admin scoring configuration
- Criterion A and B flows
- Reviewer workspace field requirements (metadata still stored on bundle)
- Mock production data
