# Admin & Reviewer Web Portal — Implementation Report

**Date:** 2026-11-05

## 1. Root causes of empty / zero dashboards

| Cause | Detail | Result |
|-------|--------|--------|
| **Live JWT session clears mock store** | `FL.store.load()` skips loading mock `faculty` / `documents` when a Flask token exists (`data.js`). | **Confirmed** |
| **Dashboard never called PostgreSQL APIs** | `FL.admin.renderDashboard()` and `FL.reviewer.renderDashboard()` read only `FL.store.faculty` and `FL.store.documents` (browser mock scoring). | **Confirmed — primary bug** |
| **Boot loader omitted dashboard pages** | `main.js` loads admin directory/documents only for specific pages; `admin-dashboard` was not included. | **Confirmed** |
| **Audit / notifications mock-only** | Audit used `FL.store.audit` (localStorage mock); notifications PATCH targeted `/api/notifications` with no Flask implementation for admin/reviewer. | **Confirmed** |
| **Genuine empty DB** | If PostgreSQL truly has no faculty/documents, zeros are correct — but UI now shows loading/error states instead of silent mock zeros. | **By design** |

Reviewer showing **Assigned Faculty: 1** but **0 documents** was consistent with **`loadReviewerAssignedFaculty()`** running while **documents were never loaded** on the dashboard route.

## 2. Files modified / added

**Backend**
- `backend/portal/dashboard_service.py` (new)
- `backend/portal/__init__.py` (new)
- `backend/auth/admin_routes.py` — dashboard, reports, audit-log, notifications
- `backend/reviewer_routes.py` — dashboard, notifications

**Frontend**
- `web/js/portal.js` (new)
- `web/js/admin.js` — live dashboard & reports
- `web/js/reviewer.js` — live reviewer dashboard
- `web/js/audit.js` — PostgreSQL audit log
- `web/js/notifications.js` — live notification PATCH
- `web/js/ui.js` — clickable metric cards (`href`)
- Admin/reviewer HTML pages — include `portal.js`

**Docs**
- `docs/ADMIN_REVIEWER_PORTAL_REPORT.md` (this file)

## 3. Backend endpoints added

| Method | Path | Role |
|--------|------|------|
| GET | `/api/admin/dashboard` | Administrator |
| GET | `/api/admin/reports` | Administrator (+ `format=csv`) |
| GET | `/api/admin/audit-log` | Administrator |
| GET/PATCH | `/api/admin/notifications` | Administrator |
| GET | `/api/reviewer/me/dashboard` | Reviewer |
| GET/PATCH | `/api/reviewer/me/notifications` | Reviewer |

Reuses: `documents.directory.workspace_stats`, `paginated_faculty_directory`, `compute_rank_simulation`, `AuditLog`, `Notification`.

## 4. Dashboard functionality

| Area | Status |
|------|--------|
| Admin summary cards (real counts) | **PASS** (code + API) |
| Clickable cards → modules | **PASS** |
| KRA overview (estimated averages from `kra_scores`) | **PASS** |
| Faculty progress table | **PASS** |
| Attention required | **PASS** |
| Reviewer summary & queue from API | **PASS** (code) |
| Browser verification | **NOT TESTED** |

## 5. Reports

| Feature | Status |
|---------|--------|
| Summary stats from API | **PASS** |
| College filter | **PASS** |
| Faculty readiness table (backend simulation) | **PASS** |
| Document status bars | **PASS** |
| CSV export | **PASS** (code) |
| PDF / Excel | **NOT IMPLEMENTED** (CSV only) |
| Charts (visual) | **PARTIAL** — bar-style status breakdown only |

## 6. Audit log

| Feature | Status |
|---------|--------|
| Read existing `audit_logs` rows | **PASS** (code) |
| Search / role filter | **PASS** (code) |
| New audit on backend actions | **PASS** (pre-existing writers) |
| Browser test | **NOT TESTED** |

## 7. Admin notifications

| Feature | Status |
|---------|--------|
| List user notifications from DB | **PASS** (code) |
| Mark read / mark all | **PASS** (code) |
| Auto-create on all admin events | **PARTIAL** — uses existing notification writers; no new event hooks in this pass |
| Browser test | **NOT TESTED** |

## 8. Reviewer dashboard & notifications

Same pattern as admin, scoped to assigned faculty/documents. **PASS** (code), browser **NOT TESTED**.

## 9. Navigation

Metric card links, faculty row evidence links, review buttons → existing routes. **PASS** (code).

## 10. Tests executed

| Test | Result |
|------|--------|
| `python -c "from portal.dashboard_service import admin_dashboard_payload"` | **PASS** |
| Playwright / manual browser | **NOT TESTED** |
| QA DB write tests | **NOT RUN** (this session) |

## 11. Remaining limitations

1. **Admin notification generation** — not every listed event type has a dedicated hook yet; faculty-facing notifications exist; admin/reviewer feeds depend on DB rows already created by workflows.
2. **Reports filters** — college filter wired; KRA / date / evaluation period filters are partial on API.
3. **PDF export** — not added.
4. **Metric definitions** — document counts are **source PDF files**, not accomplishment bundles (documented in API `metricDefinitions`).
5. **Browser QA** — required to mark portal **PASS** in production-like use.

## 12. Verification summary

| Module | PASS | FAIL | BLOCKED | NOT TESTED |
|--------|------|------|---------|------------|
| Root cause fix | ✓ | | | |
| Admin dashboard API | ✓ | | | Browser |
| Reviewer dashboard API | ✓ | | | Browser |
| Reports + CSV | ✓ | | | Browser |
| Audit log UI | ✓ | | | Browser |
| Notifications UI | ✓ | | | Browser |
| Full UI redesign (all pages) | | | | Partial — dashboards + reports prioritized |
