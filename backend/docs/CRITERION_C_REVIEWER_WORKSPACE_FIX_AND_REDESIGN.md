# Criterion C reviewer workspace — list fix & UI redesign

## Root cause (missing accomplishment list)

The reviewer summary (`GET …/criterion-c/summary`) counts accomplishments from PostgreSQL via `list_faculty_accomplishments`, but the workspace list was built only from in-memory documents using `buildWorkspaceModel()` → `isPrimaryClaimDocument()`.

**Bug:** `isReferencedAsSupporting()` treated **every** checklist slot (including `approval_sheet` and `mentor_designation`) as supporting evidence. Primary uploads always link the approval sheet / designation slot to **their own** document id, so every primary was classified as “referenced as supporting” and **filtered out**. Result: summary showed N accomplishments while the list rendered the empty state (“No accomplishments…”).

Secondary gap: the list did not use the reviewer **accomplishments API**, so even with a fixed primary detector, bundle metadata could diverge from the authoritative API rows until documents were reloaded.

## Fix summary

| Layer | Change |
|-------|--------|
| `criterion-c-workspace-ui.js` | Exclude primary claim slots from supporting detection; merge API accomplishment rows with store documents; Criterion B–style workspace layout (summary stat cards, search + status filter, draft section); improved review cards and document review structure |
| `criterion-c-evidence.js` | `fetchFacultyAccomplishments()` |
| `criterion-c-review.js` | Load summary + accomplishments + faculty documents; bind filters; draft disables approval; richer supporting-document panel |
| `evidence-workspace.css` | Compact stat cards, toolbar, draft section styling |

No scoring formula, evidence requirement, or PostgreSQL schema changes.

## API changes

None required. Existing endpoints:

- `GET /api/reviewer/me/faculty/:id/criterion-c/summary`
- `GET /api/reviewer/me/faculty/:id/criterion-c/accomplishments`
- `GET /api/reviewer/me/documents?facultyId=…` (document list with `criterionCEvidence`)

## Before / after UI structure

**Before**

- Summary from API (counts correct)
- List from broken client-side primary filter → always empty
- Raw “Raw service sum” / technical grid
- Single empty message conflated with genuine empty and sync errors

**After**

- Header: faculty, KRA I, Criterion C, max points, scoring config banner (when loaded)
- Summary cards: visible count, under review, approved, rejected, reviewer-assessed total, **estimated (unverified)**
- **Submitted accomplishments** list with search + status filter → Open review
- **Faculty drafts (read-only)** section when `status === draft`
- Document review: Criterion B–aligned sections (details, supporting documents with filename/upload/OCR, validation & assessment)
- Distinct empty, error, and list-sync messages

## Evidence linking verification

Unchanged backend slots: research `approval_sheet`, `rrpa_copc`; mentorship slots per checklist. Review UI reads `bundle.checklist` from the evidence-bundle API and resolves files via `FL.store.documentById` — same pattern as Criterion B. Criterion B slots are not shown for Criterion C.

## OCR metadata synchronization

List and detail views use bundle fields from the API/store (`projectTitle`, `studentNames`, etc.) via `displayProjectTitle()` and accomplishment merge — not document filenames or raw OCR suggestions. Faculty-confirmed values come from persisted bundle JSON (same as faculty PATCH).

## Tests passed

| Suite | Command | Result |
|-------|---------|--------|
| Criterion C workspace | `node --test web/tests/criterion-c-workspace-ui.test.js` | pass (primary self-link, API merge, draft split, workspace HTML) |
| Criterion C metadata | `node --test web/tests/criterion-c-metadata.test.js` | pass |
| Criterion B workspace regression | `node --test web/tests/criterion-b-workspace-ui.test.js` | pass |

## Guided document review (2026-11-03)

The accomplishment **document review** page no longer uses a three-column layout. It follows the Criterion B step flow:

1. **Accomplishment details** — faculty-confirmed metadata (read-only) → continue  
2. **Supporting evidence** — one required document at a time, authenticated preview, slot id preserved, save verification via existing PATCH  
3. **Final assessment** — verification summary, validation flags/blockers, scoring reference, remarks, approve/reject (same backend rules)

## Remaining limitations

- List cards use bundle checklist on store documents when present; if a supporting file is missing from the loaded faculty document set, filename/preview may show “No file linked” until documents are refreshed.
- Status filter “Faculty drafts only” repaints the draft list container only (by design).
- Full browser QA depends on live reviewer session and assigned faculty data.

## Files modified

- `web/js/criterion-c-workspace-ui.js`
- `web/js/criterion-c-evidence.js`
- `web/js/criterion-c-review.js`
- `web/css/evidence-workspace.css`
- `web/tests/criterion-c-workspace-ui.test.js`
- `backend/docs/CRITERION_C_REVIEWER_WORKSPACE_FIX_AND_REDESIGN.md`
