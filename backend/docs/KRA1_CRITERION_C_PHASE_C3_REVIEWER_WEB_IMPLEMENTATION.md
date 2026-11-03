# KRA I Criterion C — Phase C3 Reviewer Web Implementation

**Scope:** Reviewer Web workspace for Research Advising and Mentorship Services, integrated with Phase C1 backend and Phase C2 mobile accomplishments.

## Files created

| Path | Purpose |
|------|---------|
| `web/js/criterion-c-workspace-ui.js` | Labels, primary/supporting detection, list cards, summary header |
| `web/js/criterion-c-evidence.js` | Reviewer API paths (bundle, faculty summary) |
| `web/js/criterion-c-review.js` | Accomplishment list mount + three-panel review UI |
| `web/tests/criterion-c-workspace-ui.test.js` | Node unit tests |

## Files modified

| Path | Change |
|------|--------|
| `web/js/evidence-workspace.js` | Route `kra1-c` to Criterion C workspace |
| `web/js/documents.js` | Criterion C review page + back navigation |
| `web/css/evidence-workspace.css` | `.cc-*` responsive review grid |
| `web/pages/reviewer/documents.html` | Script includes |
| `web/pages/reviewer/document-review.html` | Script includes |
| `web/pages/reviewer/review-queue.html` | Script includes |
| `web/pages/admin/documents.html` | Script includes (read-only list) |
| `web/pages/admin/document-view.html` | Script includes (embedded bundle read-only) |
| `backend/documents/routes.py` | Reviewer GET summary + accomplishments for assigned faculty |
| `backend/documents/criterion_c_evidence/service.py` | Richer accomplishment rows + `reviewCounts` on summary |

## Workspace design

- **Entry:** Evidence Workspace → KRA I → Criterion C (no indicator folders; one row per accomplishment).
- **Summary bar:** Max 10, reviewer-assessed total, raw sum before cap, pending/approved/rejected counts.
- **List:** Search filter; each card shows category, research type, role, title, AY, estimated/assessed points, review status.
- **Review page:** Three columns (stacked on narrow view):
  - Left: accomplishment metadata + Annex A reference points from `rules.js` / published config
  - Center: required slots, preview links, OCR status (advisory), slot verification PATCH
  - Right: validation flags/blockers, remarks, assessed points, approve/reject (backend-gated)

## API endpoints integrated

**Existing (Phase C1):**

- `GET|PATCH /api/reviewer/documents/:id/criterion-c/evidence-bundle`

**Added for reviewer faculty context (assigned reviewer only):**

- `GET /api/reviewer/me/faculty/:facultyPublicId/criterion-c/summary`
- `GET /api/reviewer/me/faculty/:facultyPublicId/criterion-c/accomplishments`

PATCH body fields unchanged: `evidenceSlot`, `status`, `reviewStatus`, `remarks`, `assessedPoints`.

## Evidence verification workflow

1. Reviewer opens accomplishment from workspace list.
2. Verifies each checklist slot (`verified` / `present_unverified` / `reviewer_required`) via PATCH.
3. OCR status shown per linked file; copy states OCR is not approval.
4. When backend `readyForReviewer` is true and no blockers, Approve enabled (disabled if policy flags present).
5. Approve/reject sends `reviewStatus` + remarks (≥10 chars) + optional `assessedPoints` ≤ Annex max.

## Rule-based validation

Displays Phase C1 `validation.flags`, `blockers`, `checklistSummary` with mapped labels:

| Backend-ish status | Display |
|--------------------|---------|
| `verified` | Verified |
| `present_unverified` | Pending Verification |
| `missing` | Missing |
| `reviewer_required` | Needs Clarification |
| `duplicate_service_suspected` / `adviser_panel_same_thesis_review` | Needs Policy Review |

## Scoring and cap

- Authoritative totals from summary API (`aggregate_criterion_c_from_documents`): per-service sum, cap 10.
- UI shows `rawServiceSum` vs capped `estimatedPoints`.
- No client-side scoring engine; Annex reference on detail panel from `FL.rules.findIndicator`.

## Authorization

- Faculty summary/accomplishments: `profile.reviewer_user_id == reviewer.id` (404 otherwise).
- Document bundle PATCH/GET: existing `reviewer_can_access(doc)`.
- Admin: read-only via embedded `criterionCEvidence` on document payload (no PATCH).

## Test results

```text
node web/tests/criterion-c-workspace-ui.test.js  → passed
python -m pytest tests/documents/test_criterion_c_phase_c1.py --noconftest  → 20 passed
```

Live browser verification was not run in this environment; steps below are for manual QA.

## Known limitations

- OCR extracted text preview not expanded beyond existing document preview links (same as other criteria).
- Rank Simulation display on workspace relies on summary API, not a separate simulation endpoint.
- Legacy `kra1-c` documents without bundles do not appear as accomplishments until bundle-backed uploads exist.

## Manual browser verification

1. Sign in as **reviewer** assigned to a faculty member with Criterion C uploads.
2. Open **Documents → Evidence Workspace → faculty → KRA I → Criterion C**.
3. Confirm summary counts and multiple accomplishments (including same indicator twice).
4. Open **Review accomplishment**; verify three panels and slot save.
5. Attempt **Approve** with missing verification — backend should reject; UI should show error.
6. Verify all slots, approve with remarks; confirm assessed points and summary total update (refresh).
7. Confirm **Reject** requires remarks.
8. Regression: open Criterion B workspace and one Criterion A flow.

**Phase C3 complete.**
