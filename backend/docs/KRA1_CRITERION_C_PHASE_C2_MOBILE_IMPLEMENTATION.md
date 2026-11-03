# KRA I Criterion C — Phase C2 Faculty Mobile Implementation

**Scope:** Flutter faculty workflow for Research Advising and Mentorship Services, wired to Phase C1 Flask APIs. Reviewer Web not included.

## Files created (mobile)

| Path | Purpose |
|------|---------|
| `lib/data/criterion_c_catalog.dart` | Indicators, slots, Annex A point table |
| `lib/data/criterion_c_evidence.dart` | API payload models (bundle, validation, summary) |
| `lib/data/criterion_c_mapper.dart` | Indicator ID + preview points (delegates to catalog, not local formula) |
| `lib/data/criterion_c_ux.dart` | Status labels, flag humanization, policy review messaging |
| `lib/screens/criterion_c/criterion_c_hub_screen.dart` | Main Criterion C screen |
| `lib/screens/criterion_c/criterion_c_add_work_screen.dart` | Guided wizard (research vs mentorship) |
| `lib/screens/criterion_c/criterion_c_track_screen.dart` | Accomplishment detail, submit, validation |
| `lib/screens/criterion_c/criterion_c_upload_requirements_screen.dart` | Evidence checklist uploads |
| `test/criterion_c_mobile_test.dart` | Unit tests (catalog, mapper, validation, checklist) |

## Files modified

| Path | Change |
|------|--------|
| `lib/data/api_client.dart` | Criterion C summary, accomplishments, bundle, link-supporting |
| `lib/data/app_state.dart` | Fetch/patch/submit helpers |
| `lib/models/models.dart` | `criterionCEvidence`, primary/supporting getters |
| `lib/navigation/app_routes.dart` | `/criterion-c-hub` |
| `lib/main.dart` | Route registration |
| `lib/screens/documents/kra_explorer_screen.dart` | Redirect KRA I → Criterion C to hub |
| `lib/screens/documents/document_flow_args.dart` | `CriterionCAddWorkDraft`, upload launch fields |
| `lib/screens/documents/upload_document_screen.dart` | Guided C primary upload + PATCH metadata |
| `lib/screens/documents/document_details_screen.dart` | Link to Criterion C track |
| `backend/documents/serializers.py` | Embed `criterionCEvidence` on document JSON (parity with B) |

## Wizard steps

1. **Hub** — scores, accomplishment list, Add Accomplishment.
2. **Choose** — Research advising/panel vs Mentorship.
3. **Research path** — type → adviser/panel → title, students, AY, date → Annex preview → upload.
4. **Mentorship path** — activity, competition, optional prize fields → preview → upload.
5. **Upload** — primary file creates bundle; PATCH metadata; checklist screen for slots.
6. **Track** — validation flags, OCR status (advisory), reviewer remarks, submit when `readyForReviewer`.

## API endpoints used

- `GET /api/faculty/me/documents/criterion-c/summary`
- `GET /api/faculty/me/documents/criterion-c/accomplishments`
- `GET|PATCH /api/faculty/me/documents/:id/criterion-c/evidence-bundle`
- `POST /api/faculty/me/documents/:id/criterion-c/link-supporting`
- `POST /api/faculty/me/documents` (upload with `bundlePrimaryId` + `evidenceSlot` for supporting)
- `POST /api/faculty/me/documents/:id/submit`
- Rank simulation refresh (existing) for KRA I Criterion C contribution display

## Evidence workflow

Supporting uploads reuse the shared upload pipeline; backend routes to Criterion C when the primary document is `kra1-c`. Faculty see slot labels matching Phase C1 (`approval_sheet`, `rrpa_copc`, mentorship four-slot set).

## Rule-based validation (UI)

- Surfaces backend `validation.flags`, `blockers`, and `checklistSummary`.
- Duplicate and adviser/panel same-thesis flags show **Needs Reviewer/Policy Review**.
- OCR status shown separately; copy states OCR is not approval.
- Submit enabled only when backend `readyForReviewer` is true (not client-invented rules).

## Scoring display

- Per-accomplishment **Estimated points** from API `scoring.estimatedPoints` / accomplishments list.
- **Reviewer-assessed** from bundle `reviewerAssessment` / summary when `assessed`.
- Hub shows cap **10** and optional rank simulation Criterion C line from Instruction KRA breakdown.
- No independent Flutter scoring engine — preview uses `CriterionCCatalog` constants aligned with Annex A (same values as backend defaults).

## Test results

**Flutter** (from `mobile/`):

```text
flutter test test/criterion_c_mobile_test.dart  → 13 passed
flutter analyze lib/screens/criterion_c …       → clean
```

**Backend regression** (from `backend/`):

```text
python -m pytest tests/documents/test_criterion_c_phase_c1.py --noconftest
```

Run full backend suite with project venv when `factory` is available.

## Remaining issues

- Widget/integration tests with live API not added (unit coverage only).
- Legacy `kra1-c` documents without bundles appear in generic document lists but not accomplishments API until migrated.
- Rank simulation breakdown title matching is heuristic (depends on API breakdown labels).

## Manual on-device verification

1. Sign in as faculty; open **KRA I → Criterion C** (redirects to hub).
2. **Add Accomplishment → Research → UT → Adviser**; complete wizard; upload primary PDF.
3. Confirm PATCH populated title/students/date on track screen.
4. Upload **approval sheet** and **RRPA/COPC** via checklist; confirm validation flags update after refresh.
5. Repeat mentorship path; confirm four mentorship slots.
6. Submit for review when blockers cleared; confirm status change.
7. Reviewer-assessed totals on hub after backend approval (Phase C3 reviewer UI optional).
8. Pull-to-refresh hub; confirm summary and simulation line update.

**Phase C2 complete — stop before Reviewer Web (Phase C3).**
