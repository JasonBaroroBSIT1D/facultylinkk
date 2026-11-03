# Criterion C upload evidence slot fix (Flutter)

## Root cause

`UploadDocumentScreen` treated **Criterion C guided primary uploads** the same as **Criterion B** via a shared `_guidedPrimaryUpload` flag. Multi-file matching always called `CriterionBBulkUpload` (instructional material, IMDC, syllabus, library certification) and the form showed Criterion B headings and banners.

Criterion C research accomplishments use checklist slots `approval_sheet` and `rrpa_copc` (backend `documents/criterion_c_evidence/checklist.py`). The primary upload is already linked to `approval_sheet` on the server when the bundle initializes.

## Fix

| File | Change |
|------|--------|
| `mobile/lib/data/criterion_c_bulk_upload.dart` | Criterion C slot lists, filename hints, validation (mirrors B bulk helper) |
| `mobile/lib/screens/documents/upload_document_screen.dart` | Split B vs C guided flows; C-specific copy, assign UI, and `_submitGuidedBulkCriterionC` using `bundlePrimaryDocumentId` / `evidenceSlot` |

Criterion B behavior unchanged. OCR-first confirm, requirements screen, and backend bundle linking unchanged.

## Tests

| Command | Result |
|---------|--------|
| `flutter test` | **87 passed** |
| `pytest tests/documents/test_criterion_c_ocr_research.py tests/documents/test_criterion_c_phase_c1.py -q --noconftest` | **26 passed** |

## Manual checks

1. Research adviser/panel upload UI shows approval sheet messaging only.
2. Multi-file match dropdown lists `Signed approval sheet` and `RRPA or COPC…` only.
3. Single-file primary upload → OCR confirm → RRPA via checklist (`evidenceSlot: rrpa_copc`).
4. Criterion B add-work upload still shows instructional material requirements.
