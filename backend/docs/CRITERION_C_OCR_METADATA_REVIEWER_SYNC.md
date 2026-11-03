# Criterion C OCR metadata & reviewer synchronization

## Root cause (by layer)

| Layer | Issue |
|-------|--------|
| Bundle init | Research accomplishments copied `doc.title` (upload filename) into `projectTitle`, blocking OCR merge and polluting faculty/reviewer UI. |
| OCR parser | Fallback used early document lines as title; no rejection of filename/heading patterns (`Signed Approval Sheet`, `SAMPLE`, numeric prefixes). |
| Merge | OCR only filled empty `projectTitle`; junk filename values were treated as populated. |
| Faculty PATCH | Response omitted `bundle`; Flutter could not verify persistence without a second fetch (now refetches bundle). |
| Flutter form | Display preferred bundle filename over OCR when both present. |
| Reviewer Web | `accomplishmentTitle` fell back to document filename when bundle title was junk. |

## Fix summary

- **`research_metadata.py`**: Shared unreliable-title detection.
- **`ocr_research.py`**: Label-based extraction only; expanded labels/dates; scrub junk titles on merge.
- **`service.py`**: Empty research `projectTitle` on init; validate PATCH titles; `metadataFacultyConfirmedAt`; accomplishments API includes student names + confirmation flags.
- **`routes.py`**: Faculty PATCH returns full bundle payload fields.
- **Flutter**: `criterion_c_research_metadata.dart`, improved form resolution, save verification, dirty-field protection during OCR polling.
- **Reviewer Web**: `displayProjectTitle`, `metadataConfirmationLabel`, accomplishment list uses bundle metadata.

## Before / after extraction (representative)

| Field | Before | After (same OCR text) |
|-------|--------|------------------------|
| Title | `01 Signed Approval Sheet SAMPLE` | `Adaptive Learning Platform for Engineering Students` |
| Students | empty | `Lee, Kim and Santos, Ana` |
| AY | `2025-2026` | `2025-2026` |
| Date | empty | `2025-03-15` (when labeled in OCR text) |

## Tests

| Suite | Command | Result (2026-11-03) |
|-------|---------|------------------------|
| Backend OCR + metadata | `pytest tests/documents/test_criterion_c_ocr_research.py tests/documents/test_criterion_c_metadata_sync.py tests/documents/test_criterion_c_phase_c1.py -q --noconftest` | **30 passed** |
| Criterion B regression | `pytest tests/documents/test_criterion_b_evidence.py -q --noconftest` | **11 passed** |
| Flutter metadata | `flutter test test/criterion_c_research_metadata_test.dart` | **3 passed** |
| Flutter full suite | `flutter test` | **90 passed** |
| Reviewer JS | `node --test web/tests/criterion-c-metadata.test.js` | **3 passed** |

Coverage highlights:

1. Research title from labeled OCR text (not filename).
2. Multiple student names, academic year, approval date.
3. Optional group label omitted when absent.
4. Filename / “Signed Approval Sheet SAMPLE” rejected as title.
5. OCR merge replaces unreliable bundle title.
6. Confirmed metadata retained on `persist_bundle`.
7. Flutter form prefers OCR over junk bundle title; optional group not flagged empty.
8. Reviewer helpers prefer confirmed bundle title and show metadata confirmation label.

## Backend persistence verification

- Faculty `confirmMetadata: true` PATCH persists `projectTitle`, `studentNames`, `studentGroupLabel`, `academicYear`, `completionDate`, `metadataConfirmed`, and `metadataFacultyConfirmedAt` on the Criterion C evidence bundle (same accomplishment record).
- PATCH response includes `bundle`, `scoring`, `ocrStatus`, and `ocrExtraction`; mobile refetches the bundle after save.
- OCR re-run does not overwrite fields after faculty confirmation (existing merge guards + unreliable-title scrub).

## Reviewer API synchronization

- Accomplishments list and evidence-bundle payloads expose bundle research fields and confirmation flags (not document filename as title when bundle title is reliable).
- Reviewer Web reads API `bundle` only; `displayProjectTitle` and accomplishment details use confirmed values.

## Files modified (this fix)

| Area | Files |
|------|--------|
| Backend | `documents/criterion_c_evidence/research_metadata.py`, `ocr_research.py`, `service.py`, `documents/routes.py` |
| Tests | `tests/documents/test_criterion_c_ocr_research.py`, `tests/documents/test_criterion_c_metadata_sync.py` |
| Flutter | `lib/data/criterion_c_research_metadata.dart`, `criterion_c_evidence.dart`, `app_state.dart`, `screens/criterion_c/criterion_c_research_confirm_screen.dart`, `test/criterion_c_research_metadata_test.dart` |
| Reviewer Web | `web/js/criterion-c-workspace-ui.js`, `web/js/criterion-c-review.js`, `web/tests/criterion-c-metadata.test.js` |
| Docs | `backend/docs/CRITERION_C_OCR_METADATA_REVIEWER_SYNC.md` |

## Remaining limitations

- OCR quality depends on scan/PDF text layer; handwritten or poor scans may still require full manual entry.
- Group label is only extracted when explicitly labeled on the sheet.
- Reviewer Web shows bundle fields only (no independent PDF parsing by design).
