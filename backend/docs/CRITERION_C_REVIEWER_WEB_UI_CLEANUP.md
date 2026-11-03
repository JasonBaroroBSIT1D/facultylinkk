# Criterion C Reviewer Web UI cleanup

## 1. Executive summary

Reviewer Web for KRA I Criterion C was simplified to align with the Criterion B evidence workspace: fewer instructional blocks, no list search/filter controls, and no full published scoring comparison table on the review flow. Accomplishment-level scoring (applicable points, criterion maximum, configuration banner) remains driven by the live scoring configuration API and locked bundle snapshots. Backend contracts, validation, and guided review steps are unchanged.

## 2. Files modified

| File | Change |
|------|--------|
| `web/js/criterion-c-workspace-ui.js` | Workspace header/summary labels; simplified cards; removed intro + toolbar; `accomplishmentScoringContextHtml` |
| `web/js/criterion-c-review.js` | Removed list filter bindings; per-accomplishment scoring context; removed annex reference table from decision step |
| `web/js/scoring-configuration.js` | Deprecated `criterionCReferenceTableHtml` for reviewer UI (function retained) |
| `web/css/evidence-workspace.css` | Removed unused toolbar styles; scoring context spacing |
| `web/tests/criterion-c-workspace-ui.test.js` | Tests for removed controls and scoring context |
| `web/tests/criterion-c-guided-review.test.js` | Assert no full reference table on decision step |

## 3. Removed UI components

- Workspace paragraph: “Each card is one research advising or mentorship accomplishment…”
- Search input (`#cc-accomplishment-filter`) and status dropdown (`#cc-accomplishment-status-filter`)
- `_bindAccomplishmentListFilters` and its event listeners
- Decision-step render of `criterionCReferenceTableHtml` (“Published Criterion C point reference” table)
- Extra accomplishment card rows (evidence completeness blurb, duplicate validation badges)

## 4. Updated workspace layout

**Header:** Criterion C — Research Advising and Mentorship Services; faculty name; applicable scoring banner (version/effective date via shared `bannerHtml`); criterion maximum.

**Compact summary:** Accomplishments, Under review, Approved, Rejected, Reviewer-assessed total, Estimated (unverified).

**Cards:** Title, research type, role (when applicable), academic year, workflow status, estimated (unverified) points, **Open Review** (or View draft).

Cards render directly under the summary with no filter bar.

## 5. Scoring reference page removal

The full adviser/panel comparison table is no longer injected into the reviewer accomplishment review. There was no separate HTML route file; the table appeared at the bottom of step 3. That block is removed. `criterionCReferenceTableHtml` remains in `scoring-configuration.js` for potential non-reviewer use but is marked deprecated for Reviewer Web.

## 6. Preserved dynamic scoring integration

- `FL.scoringConfiguration.refresh`, `bannerHtml`, `indicatorPoints`, `criterionCMax`, `lockedSnapshotLabel`, `fetchByConfigurationId`
- Backend `estimatedPoints`, reviewer-assessed points, and PATCH approve/reject payloads
- Per-accomplishment **Applicable points** and **Criterion C maximum** via `officialPointsForIndicator` / `maxCriterionCPoints` (not hardcoded)

## 7. Reviewer workflow verification

Guided steps unchanged:

1. Accomplishment details (faculty-confirmed metadata + scoring context)
2. Supporting evidence (preview, slot verification PATCH)
3. Final assessment (summary, validation, remarks, approve/reject with backend gate)

## 8. Regression test results

```text
node --test web/tests/criterion-c-workspace-ui.test.js
         web/tests/criterion-c-guided-review.test.js
         web/tests/criterion-c-metadata.test.js
         web/tests/criterion-b-workspace-ui.test.js
```

Run after each change; all suites passed at implementation time.

Browser QA: **not performed** in this session (requires live reviewer login).

## 9. Remaining limitations

- Faculty draft section still lists drafts without search (by design).
- `filterAccomplishments` remains in workspace UI for unit tests only; no reviewer UI calls it.
- Full Criterion C matrix is available in Admin scoring configuration, not in Reviewer Web.
