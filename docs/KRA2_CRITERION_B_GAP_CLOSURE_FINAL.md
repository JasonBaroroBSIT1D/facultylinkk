# KRA II Criterion B — Gap closure final report

**Date:** 2026-11-04  
**Criterion B status: NOT COMPLETE** — service-layer live QA and backend regressions pass; **reviewer Playwright** and **Flutter integration_test** did not run with authenticated credentials / runnable device toolchain in this session.

Official scoring configuration was **not** modified.

---

## Summary matrix

| # | Area | Result | Evidence |
|---|------|--------|----------|
| 1 | Seven Criterion B families (live harness) | **PASS** | `docs/KRA2_CRITERION_B_LIVE_QA_REPORT.json` — `overallStatus: PASS`, all seven `families.*.status: PASS` (run `20261104T042202Z`) |
| 2 | Reviewer web (Playwright) | **NOT TESTED** | `web/e2e/kra2-b-reviewer.spec.js` — 7 tests **skipped** (no `QA_REVIEWER_EMAIL` / `QA_REVIEWER_PASSWORD` or `QA_REVIEWER_TOKEN` in env or `backend/.env`) |
| 3 | Flutter integration tests | **NOT TESTED** | `integration_test/kra2_b_faculty_api_flow_test.dart` — load failed (Windows desktop: missing Visual Studio toolchain); no `--dart-define=QA_FACULTY_*` |
| 4 | OCR extraction (B families) | **PASS** | Live QA `ocrFields` per family; pytest `test_kra2_ocr_extraction`, `test_kra2_contribution_ocr`; IPOPHL venue normalization fixed |
| 5 | Contribution % (Annex F/G/H advisory) | **PASS** | `edgeCases.annex_f_ocr_contribution_percent: "40"`, `annex_f_contribution_ocr_missing: false`; faculty/reviewer confirm still required |
| 6 | Database persistence | **PASS** | Harness checks: submit, slot verify, approval points, document status; rejection doc `rejectAccomplishmentDocumentId` |
| 7 | Reviewer approval & rank simulation | **PASS** | Per-family `approved_points_persisted`, `document_status_approved`; `rankSimulation.status: PASS` |
| 8 | Software multi-slot upload reliability | **PASS** | Root cause: duplicate hash blocked second slot — fixed in `documents/service.py`; `test_kra2_software_multi_slot_upload.py` (2 passed) |

---

## Priority 1 — Reviewer web E2E

**Result: NOT TESTED**

- Playwright suite expanded: bundle slots, per-family PDF preview, UI document review, approval/blocker API checks, rejected accomplishment persistence, 404 non-HTML error.
- `npm install` in `web/e2e` (includes `dotenv`); global setup loads optional `QA_*` from `backend/.env` only — **no secrets in repo**.
- To execute: set `QA_REVIEWER_EMAIL` and `QA_REVIEWER_PASSWORD` (authorized reviewer, e.g. assigned to QA faculty), ensure API `:5000` and web `:8080`, then:

  `cd web/e2e && npm run test:kra2-b`

- Screenshots (when UI test runs): `docs/qa-screenshots/kra2-b/reviewer-document-review.png`

---

## Priority 2 — Flutter E2E

**Result: NOT TESTED** (harness present)

- Added `integration_test` dependency and `mobile/integration_test/kra2_b_faculty_api_flow_test.dart` (API login + draft/submit semantics; skips with `markTestSkipped` when credentials absent).
- **Not executed:** Windows integration build requires Visual Studio C++ toolchain; Chrome target does not support integration tests.
- Contract tests **PASS**: `mobile/test/kra2_criterion_b_qa_contract_test.dart`, `kra2_criterion_b_faculty_labels_test.dart`.
- Full UI journey (choose indicator → upload → OCR → confirm → send for review) remains a follow-up when device + `QA_FACULTY_EMAIL` / `QA_FACULTY_PASSWORD` are available.

---

## Priority 3 — OCR improvements

**Result: PASS** (text-layer PDFs; scanned layouts **NOT TESTED**)

- IPOPHL / issuing-organization: `_normalize_issuing_venue` no longer treats `(IPOPHL)` fragments as final venue.
- Advisory `declaredContributionPercent` flows through `filter_extracted_fields` for co-authored indicators; `build_extraction_payload` marks advisory partial status.
- No fabrication when percent line absent (unit test enforced).

---

## Priority 4 — Software upload reliability

**Result: PASS**

- **Cause:** `_duplicate_upload_for_profile` treated identical file hash as duplicate across **different** checklist slots on the same bundle.
- **Fix:** Allow same hash on distinct slots of one KRA II primary bundle; still block same slot / other bundles.
- Regression: `backend/tests/documents/test_kra2_software_multi_slot_upload.py`.

---

## Priority 5 — Test data safety

**Result: PASS** (mechanism); **NOT TESTED** (dedicated `facultylink_qa` DB in this session)

- `[KRA2-B-QA]` titles excluded from rank/scoring aggregation (`is_qa_sandbox_accomplishment`).
- Harness respects `FACULTYLINK_QA_DATABASE_URL` when set; live runs used existing PostgreSQL with tagged rows only.
- Existing approved non-QA accomplishments were not modified by harness design.

---

## Seven families (detail)

| Family | Indicator (QA) | Harness |
|--------|----------------|---------|
| Patent | `kra2-b-patent-g-sole` | PASS |
| Patent co / Annex F | `kra2-b-patent-g-co` | PASS |
| Commercialization | `kra2-b-comm-local` | PASS |
| Utility model | `kra2-b-um-sole` | PASS |
| Industrial design | `kra2-b-id-sole` | PASS |
| Software | `kra2-b-sw-new-sole` | PASS (intermittent slot fill if run aborts mid-upload — re-run harness) |
| Variety | `kra2-b-variety-sole` | PASS |

**Re-run harness:** `FACULTYLINK_KRA2_QA_RUN=1 python backend/scripts/kra2_criterion_b_live_qa.py`

---

## Conclusion

Implementation gaps addressed in code and **verified via Flask + PostgreSQL live QA** and targeted pytest. **COMPLETE** for Criterion B QA still requires:

1. Playwright reviewer tests **executed and passing** with real reviewer credentials.
2. Flutter **integration_test** on a supported device with faculty credentials (and ideally full upload/OCR UI flow).

Do **not** treat skipped Playwright/Flutter tests as PASS.
