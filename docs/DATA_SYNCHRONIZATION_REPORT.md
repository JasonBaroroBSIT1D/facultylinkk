# FacultyLink — Data Synchronization Report

**Date:** 2026-11-05  
**Scope:** Admin Web, Reviewer Web, Faculty Mobile vs one PostgreSQL backend

---

## 1. Root causes of inconsistent information

| Symptom | Root cause |
|--------|------------|
| Admin dashboard / reports show **0** faculty and **0** documents while **Faculty Records** lists Jason Baroro | With a live JWT, `FL.store.load()` **does not** load mock faculty/documents. Pages that still used `FL.store.faculty` / `FL.store.documents` (legacy dashboard path) showed empty counts. Live dashboards must call **`GET /api/admin/dashboard`** and **`GET /api/admin/reports`** (implemented earlier; this pass clears mock residue on **all** admin pages and keeps aggregates authoritative). |
| Reviewer dashboard **“No published schedule”** while mobile shows a preparation period | **Boot-order bug:** `reviewer-dashboard` used a fast path (`loadReviewerAssignedFaculty` only) that **skipped** `loadEvaluationPeriods`. Mobile uses **`GET /api/faculty/me/dashboard`** → `faculty_preparation_period_api()` (published row). Reviewer UI now loads periods on boot **and** receives **`evaluationPeriods`** inside **`GET /api/reviewer/me/dashboard`**. |
| Reviewer **0 submitted documents** vs mobile **65 files** | Often **different API base URL or database** (e.g. web `http://127.0.0.1:5000` vs Flask on **5001**, or `facultylink` vs `facultylink_qa`). Less often: metrics differ by definition (mobile dashboard counts **workflow PDF rows**; reviewer “submitted documents” is the same PDF set for **assigned** faculty only). |
| Admin **0 KRA** averages | `KraScore` averages over faculty with score rows; empty or single-faculty DB can show **—** / low averages. Not a separate client formula — **`portal/dashboard_service._kra_averages`**. |
| Faculty Records vs dashboard mismatch after login | Mock seed cleared only on faculty/reviewer admin pages; dashboard could still mix stale mock until refresh. **Fix:** `clearAccountMocksForLiveAdmin()` on **every** administrator boot when JWT is present. |

**Not a root cause (by design):** Pending document reviews can keep the **document-level** reviewer id after reassignment (see admin “Change reviewer” note). Directory and reviewer lists are scoped by **`FacultyProfile.reviewer_user_id`**, not document.reviewer_id.

---

## 2. Authoritative data source

- **Single backend:** Flask + SQLAlchemy → PostgreSQL (`DATABASE_URL` in `backend/.env`).
- **Aggregates:** `backend/documents/directory.py` → `workspace_stats()`, `paginated_faculty_directory()`.
- **Portals:** `backend/portal/dashboard_service.py` (admin/reviewer dashboard, reports, notifications, audit).
- **Mobile:** `GET /api/faculty/me`, `/me/dashboard`, `/me/rank-simulation`, document APIs under `/api/faculty/documents/...`.
- **Web default API:** `web/js/api-config.js` → `http://127.0.0.1:5000` (override with `window.FL_API_BASE` before scripts load).
- **Mobile default API:** `mobile/lib/data/api_config.dart` → `127.0.0.1:5000` / `10.0.2.2:5000` (override `--dart-define=FL_API_BASE_URL=...`).

---

## 3. Diagnostic endpoints (Phase 1)

| Client | Endpoint | Purpose |
|--------|----------|---------|
| Unauthenticated | `GET /api/health` | `databaseIdentity.databaseName`, `databaseCategory` (`production` / `qa` / `test` / `other`) — **no credentials** |
| Admin JWT | `GET /api/admin/sync-health` | Actor + `workspaceStats` |
| Reviewer JWT | `GET /api/reviewer/me/sync-health` | Assigned faculty count + scoped stats |
| Faculty JWT | `GET /api/faculty/me/sync-health` | Document count + preparation period flag + reviewer id |

**Web helper:** `FL.portal.loadSyncHealth(session)` in `web/js/portal.js`.

**Alignment checklist**

1. Open `GET /api/health` from the same host/port as each client’s API base.
2. Compare `databaseName` across admin sync-health, reviewer sync-health, and faculty sync-health (after login).
3. Confirm `FL_API_BASE` / `FL_API_BASE_URL` match the running Flask process.

---

## 4. Backend changes (this pass)

| File | Change |
|------|--------|
| `backend/portal/sync_health.py` | **New** — database identity + role-aware sync payloads |
| `backend/portal/dashboard_service.py` | Reviewer dashboard includes **`evaluationPeriods`** |
| `backend/auth/admin_routes.py` | `GET /api/admin/sync-health` |
| `backend/reviewer_routes.py` | `GET /api/reviewer/me/sync-health` |
| `backend/faculty_routes.py` | `GET /api/faculty/me/sync-health` |
| `backend/factory.py` | `/api/health` adds **`databaseIdentity`** |

*(Prior work: `GET /api/admin/dashboard`, `/reports`, `/api/reviewer/me/dashboard` — see `docs/ADMIN_REVIEWER_PORTAL_REPORT.md`.)*

---

## 5. Admin Web changes

| File | Change |
|------|--------|
| `web/js/main.js` | Load evaluation periods on **admin-dashboard** and **reviewer-dashboard**; fix reviewer fast-boot path; clear account mocks on all admin pages with JWT |
| `web/js/data.js` | `loadEvaluationPeriods` for reviewer token; post-mutation hooks |
| `web/js/portal.js` | `afterWorkspaceMutation`, `loadSyncHealth`, workspace version bump |
| `web/js/reviewer.js` | Apply **`evaluationPeriods`** from dashboard API payload |

---

## 6. Reviewer Web

Same files as §5; reviewer schedule card uses store periods + dashboard-embedded periods.

---

## 7. Flutter

No code changes this pass. Ensure **`ApiConfig.baseUrl`** matches Flask and the same `databaseName` as `/api/health`. Use **`AppState.refreshData()`** after uploads (already wired on upload/shell focus).

---

## 8. Database migrations

None.

---

## 9. Tests executed

| Test | Result |
|------|--------|
| `backend/tests/portal/test_sync_health.py` | **PASS** (2) |
| Full Phase 13 E2E (QA DB writes) | **NOT RUN** — use `facultylink_qa` + `FACULTYLINK_ALLOW_DB_WRITES=1` per `docs/KRA4_FINAL_QA_REPORT.md` |
| Browser manual (Admin + Reviewer + Flutter same backend) | **NOT TESTED** in this session |

---

## 10. Before / after (expected)

| Screen | Before | After |
|--------|--------|-------|
| Admin dashboard | 0 / 0 / 0 from empty mock store or wrong API | Counts from **`GET /api/admin/dashboard`** |
| Admin reports | 0 faculty totals | **`GET /api/admin/reports`** |
| Reviewer dashboard schedule | “No published schedule” despite mobile period | Published periods from API + boot load |
| Reviewer submitted docs | 0 when on wrong DB/port | Matches **`workspace_stats(reviewer_user_id=...)`** on same DB as mobile |
| After reviewer decision / assign reviewer / publish schedule | Stale dashboard until full reload | **`FL.portal.afterWorkspaceMutation`** refreshes open dashboard/report |

---

## 11. Metric definitions (consistent labeling)

| Label | Definition |
|-------|------------|
| Submitted documents (admin/reviewer portal) | Non-deleted **source PDF** workflow rows (`Document.deleted_at IS NULL`) |
| Waiting for review | `is_awaiting_review()` (pending + needs revision workflow) |
| Mobile validated / pending | Per-document **`status`** on faculty profile’s documents |
| SET/SEF semester rows | Counted separately in teaching-evaluation stats; **not** added to PDF totals |

---

## 12. Remaining limitations

1. **No push/real-time sync** — refresh-on-mutation (web) and pull-to-refresh / focus refresh (mobile).
2. **Document-level reviewer id** may differ from current assignment for in-flight reviews (documented in UI).
3. **E2E QA scenario (Phase 13)** still requires a manual or automated run against **`facultylink_qa`**.
4. **Notifications/audit** on every mutation — list APIs exist; not every faculty upload path was re-audited in this pass.
5. If Flask and static web use **different ports**, you must set **`FL_API_BASE`** explicitly (e.g. `http://127.0.0.1:5001`).

---

## 13. Quick verification commands

```powershell
# Same machine as Flask
curl http://127.0.0.1:5000/api/health

# After admin login in browser console (session must be active):
# FL.portal.loadSyncHealth(JSON.parse(sessionStorage.getItem('facultylink.session'))).then(console.log)
```

Ensure **`databaseIdentity.databaseName`** is identical for admin, reviewer, and faculty sync-health when all three clients point at the same API base URL.
