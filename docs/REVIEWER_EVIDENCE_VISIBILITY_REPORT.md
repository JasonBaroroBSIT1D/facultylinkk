# Reviewer Evidence Workspace — All Documents Visible

**Date:** 2026-11-05

## Problem

Reviewer Evidence Workspace and faculty navigation emphasized **pending** work (default filters, KRA II load race, primary-claim-only lists). Assigned faculty metrics showed **65 source PDFs** while pending + approved summed to **63** — the remainder are **`needs_revision`**, **`rejected`**, or **`draft`** rows counted in `stats_from_documents` / `workspace_stats`.

## Changes

### Backend
- `backend/documents/directory.py` — `workspace_stats()` now includes **`documentStatusBreakdown`** from `stats_from_documents()` so UI can reconcile totals.

### Reviewer Web
- `web/js/evidence-workspace.js`
  - **Default filter:** `all` (unchanged in URL parser).
  - **In-folder filters:** Status tabs stay visible while browsing Faculty → KRA → …; filters no longer kick you out of a faculty tree.
  - **`docStatusBucket` / `applyDocStatusFilter`:** Consistent pending / revision / approved / rejected matching for DB and web statuses.
  - **Filter tab counts** from `GET …/documents?facultyId=` **`stats`** or live document rows.
  - **Removed** extra `needsAction` filter on pending tab (hid valid pending rows).
  - **Always await** `loadFacultyDocuments` when a faculty id is in the route (fixes KRA II race).
  - **Criterion B indicator list:** All source PDFs shown; supporting files labeled.
  - **Reviewer stats row:** Total PDFs + rejected count.
  - **After review refresh:** Reloads stats, faculty documents, and re-renders open workspace view.
- `web/js/data.js` — Stores per-faculty **`facultyDocumentStats`**; review submit refreshes evidence workspace.
- `web/js/faculty.js` — **Evidence workspace** link from Assigned Faculty and faculty detail header.
- `web/js/doc-folders.js` — Status filter uses shared buckets; `needs-revision` badge.
- `web/js/portal.js` — Refreshes evidence page after mutations.

## 65 = 31 + 32 + …

| Bucket | Source |
|--------|--------|
| Pending review | `pending_review`, `reviewer_required`, legacy uploaded `draft` |
| Approved | `approved`, `valid` |
| Needs revision | `needs_revision` |
| Rejected | `rejected` |
| Draft (no file) | `draft` without file (rare) |

Use **`documentStatusBreakdown`** on workspace stats or faculty document list **`stats`** to verify counts.

## Tests

| Test | Result |
|------|--------|
| `backend/tests/documents/test_document_status_breakdown.py` | Run locally against configured DB |
| `web/tests/evidence-doc-status-filter.test.js` | Static checks — run `node web/tests/evidence-doc-status-filter.test.js` |
| QA E2E (facultylink_qa writes) | **NOT RUN** in this session |

## Remaining

- Accomplishment workspaces (KRA II–IV) still center on **accomplishment** rows; linked source PDFs appear in indicator grids and review pages, not as duplicate accomplishments.
- Review queue shortcut (`review-queue.html`) still opens **Pending review** filter by design.
