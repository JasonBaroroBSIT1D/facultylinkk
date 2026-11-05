# Reviewer — Direct Accomplishment Navigation

**Date:** 2026-11-05

## Problems addressed

1. **Navigation from Evidence Workspace** — Document table links must land on the correct criterion accomplishment list without replacing that UI with an in-workspace review panel.
2. **Criterion B — Inventions empty list** — Reviewer API used `submitted_only=True`, hiding primary PDFs that exist in PostgreSQL but lack `submittedForReviewAt` on the KRA II bundle.
3. **Document vs accomplishment drift** — Files visible in Evidence Workspace but absent from accomplishment list.
4. **Infinite loading (“Loading submission…” / “Preparing this view.”)** — In-workspace review called `paintReviewPage`, which replaced **`#page`** with a spinner and **detached** `#evidence-body`. Subsequent renders wrote to a disconnected node while the user still saw the spinner on `#page`.

### Infinite loading — fix

- Review details run on **`document-review.html`** only (`paintReviewPage` + `_resolveMountEl`); never replace Evidence Workspace `#page` while mounting inside `#evidence-body`.

### UI restoration

- Accomplishment **list** (summary stat tiles + cards + **Open Review**) stays in Evidence Workspace.
- **`highlightDoc`** (legacy **`focusDoc`**) scrolls to a card from document-table navigation; it does not open compact review in-place.

## Root cause (Criterion B / KRA II)

`GET /api/reviewer/me/faculty/:id/kra2-b/accomplishments` called `list_faculty_accomplishments(..., submitted_only=True)`. Uploads without a faculty “submit for review” timestamp were excluded even though `Document` rows exist for `criterion_id=kra2-b`.

## Solution

### Navigation (`web/js/reviewer-nav.js`)

- **`documentReviewUrl(doc)`** → `document-review.html?…` (Open Review, review queue).
- **`reviewUrlFromDoc(doc)`** → criterion workspace + `highlightDoc=` (document table navigation).
- **`FL.portal.reviewHref`** uses `documentReviewUrl`.

### Backend

- Reviewer accomplishments endpoints for **KRA II, III, IV** now use **`submitted_only=False`** (`backend/documents/routes.py`, `backend/documents/kra4_routes.py`).
- List rows include **`submittedForReview`** and **`needsClassification`** (`backend/documents/kra2_evidence/service.py`).

### Orphan / needs classification

- After loading accomplishments, UI compares API rows to in-memory criterion documents and shows a **Needs classification** list for PDFs not in the accomplishment list (no invented accomplishments).

## Files modified

| File |
|------|
| `web/js/reviewer-nav.js` (new) |
| `web/js/kra2-a-review.js`, `kra2-a-workspace-ui.js` |
| `web/js/criterion-b-simple-review.js`, `criterion-c-review.js` |
| `web/js/evidence-workspace.js`, `portal.js`, `documents.js` |
| `web/pages/reviewer/documents.html`, `document-review.html` |
| `backend/documents/routes.py`, `kra4_routes.py`, `kra2_evidence/service.py` |

## Tests

| Test | Result |
|------|--------|
| `backend/tests/documents/test_document_status_breakdown.py` | PASS (prior) |
| `node web/tests/evidence-doc-status-filter.test.js` | PASS (prior) |
| `node web/tests/reviewer-evidence-focus-mount.test.js` | PASS |
| Browser E2E (all KRAs) | **NOT RUN** |

## Remaining / limitations

- **KRA I-A (SET/SEF)** still uses teaching-evaluation drawers in criterion workspace (not accomplishment cards).
- **Admin** `document-view.html` unchanged (monitoring role).
- **Expandable list UI** — Accomplishment review opens in-place via `focusDoc`; full accordion-on-same-screen without URL focus is not added (same components, less navigation).
- Documents that are **supporting-only** KRA II rows remain excluded from accomplishment list by design; they appear under **Needs classification** or parent accomplishment review.

## Verification checklist

1. Assigned Faculty → Evidence workspace → KRA II → Criterion B — accomplishments list populated (including not-yet-submitted with badge).
2. Click **Review** on a workspace table row → URL contains `focusDoc=` → compact review UI inside workspace.
3. Old `document-review.html?id=…` → redirects to workspace.
4. **Back to accomplishments** → list view, no standalone review tabs page.
