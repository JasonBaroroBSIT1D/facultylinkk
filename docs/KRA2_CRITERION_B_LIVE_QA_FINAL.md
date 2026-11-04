# KRA II Criterion B — Live QA final verification

**Criterion B status: NOT COMPLETE** — see **`docs/KRA2_CRITERION_B_GAP_CLOSURE_FINAL.md`** for the authoritative PASS/FAIL/NOT TESTED matrix.

## Latest live harness

| Field | Value |
|-------|--------|
| Run ID | `20261104T042202Z` |
| Overall | **PASS** (all 7 families) |
| Report | `docs/KRA2_CRITERION_B_LIVE_QA_REPORT.json` |

## Quick status

| Area | Result |
|------|--------|
| Service-layer 7 families | **PASS** |
| Playwright reviewer web | **NOT TESTED** (no `QA_REVIEWER_*` in env) |
| Flutter integration_test | **NOT TESTED** (toolchain / credentials) |
| OCR + Annex F advisory % | **PASS** (pytest + harness edge cases) |
| Software multi-slot upload fix | **PASS** (pytest) |
| QA sandbox scoring isolation | **PASS** (pytest) |

## Run commands

```bash
# Backend live QA (creates [KRA2-B-QA] rows only)
FACULTYLINK_KRA2_QA_RUN=1 python backend/scripts/kra2_criterion_b_live_qa.py

# Reviewer Playwright (credentials via env or backend/.env — never commit)
cd web/e2e && npm install && npx playwright install chromium && npm run test:kra2-b

# Flutter API integration (Windows desktop needs VS toolchain)
flutter test -d windows integration_test/kra2_b_faculty_api_flow_test.dart \
  --dart-define=QA_FACULTY_EMAIL=... --dart-define=QA_FACULTY_PASSWORD=...
```
