# FacultyLink API contract (Phase 1)

Maps existing **web mock routes** and **Flutter workflows** to the shared Flask REST API.  
Guideline reference in UI: **DBM–CHED Joint Circular No. 01, s. 2026** (configuration only until official rules are validated).

Legend: **Mock today** → **Planned REST** → **Phase**

---

## Authentication (Phase 3)

| Web / mobile operation | Mock (web) | Planned endpoint | Roles |
|------------------------|------------|------------------|-------|
| Sign in | `POST /api/login` | `POST /api/auth/login` `{ email, password }` | admin, reviewer, faculty |
| Session restore | `GET /api/session` | `GET /api/auth/session` (Bearer JWT) | all |
| Sign out | `POST /api/logout` | `POST /api/auth/logout` | all |
| Change password | `POST /api/account/password` | `POST /api/auth/change-password` | all |
| Forgot password | `POST /api/forgot-password` | `POST /api/auth/forgot-password/*` | faculty + staff |
| Staff-only web login | (same form) | Same endpoint; **403** if role is faculty on web | admin, reviewer |
| Faculty mobile login | (simulated) | Same endpoint; **403** if role is not faculty on mobile | faculty |

JWT: `Authorization: Bearer <accessToken>`. Role checks enforced **on the server** for every mutating route.

---

## Web portal — shared state (Phase 4–5)

| Operation | Mock | Planned endpoint | Phase |
|-----------|------|------------------|-------|
| Load admin/reviewer workspace | `GET /api/state` | Split into resource endpoints below | 4 |
| Profile update | `PATCH /api/profile` | `PATCH /api/me/profile` | 3 |

### Administrator

| Module (page) | Operations | Planned endpoints |
|---------------|------------|-------------------|
| Dashboard | KPIs, activity | `GET /api/admin/dashboard` |
| Faculty | list, create, delete, assign reviewer, send credentials | `GET/POST/DELETE /api/admin/faculty`, `POST .../reviewer`, `POST .../credentials` |
| Reviewers | list, create, delete, credentials | `GET/POST/DELETE /api/admin/reviewers`, `POST .../credentials` |
| Documents | monitor all | `GET /api/admin/documents`, `GET /api/admin/documents/:id` |
| KRA configuration | publish weights/rules | `GET/PUT /api/admin/kra-configuration`, `GET/PATCH /api/admin/scoring-rules` |
| Evaluation schedule | CRUD periods | `GET/PUT /api/admin/evaluation-periods` |
| Reports | analytics | `GET /api/admin/reports` |
| Notifications | list, mark read | `GET/PATCH /api/notifications` |
| Audit log | append, list | `GET/POST /api/admin/audit-logs` |

### Reviewer

| Module | Operations | Planned endpoints |
|--------|------------|-------------------|
| Dashboard | queue counts | `GET /api/reviewer/dashboard` |
| Assigned faculty | list | `GET /api/reviewer/faculty` |
| Faculty detail | profile + docs | `GET /api/reviewer/faculty/:id` |
| Review queue | pending docs | `GET /api/reviewer/review-queue` |
| Document review | view, validate, reject, remarks, score | `GET /api/reviewer/documents/:id`, `POST .../review` |
| Documents list | scoped | `GET /api/reviewer/documents` |
| KRA reference / schedule | read-only config | `GET /api/reviewer/kra-configuration`, `GET /api/reviewer/evaluation-periods` |
| Notifications / profile | same as admin scoped | `GET/PATCH /api/me/*` |

Reviewers **must only** receive faculty/documents where `faculty_profiles.reviewer_user_id` matches the authenticated reviewer.

---

## Flutter faculty app (Phase 6–8)

| Screen | Data needed | Planned endpoints |
|--------|-------------|-------------------|
| Login / forgot password | auth | `/api/auth/*` |
| Dashboard | snapshot, prep period | `GET /api/faculty/dashboard`, `GET /api/faculty/preparation-period` |
| Documents | list, upload, replace, delete, view file | `GET/POST /api/faculty/documents`, `GET .../:id/file`, etc. |
| Assessment | KRA scores, requirements | `GET /api/faculty/assessment/kra-scores`, `GET .../requirements` |
| Simulation | rank preview (estimated vs verified) | `GET /api/faculty/simulation` |
| Notifications | list, read | `GET/PATCH /api/faculty/notifications` |
| Profile | read/update | `GET/PATCH /api/faculty/me` |

Upload flow (Phase 7–8):

1. `POST /api/faculty/documents` (multipart) → store file + metadata  
2. Background/process: OCR + classification → update `documents.ocr_status`, `extracted_info`  
3. Reviewer web lists document → `POST review`  
4. Faculty polls or refresh → updated `status`, `reviewer_remarks`, `verified_points`

---

## Scoring & simulation (Phase 7)

| Concern | Storage | Notes |
|---------|---------|--------|
| Configurable rules | `kra_scoring_rules`, `kra_configuration` | Admin-managed; no invented official point tables in code without validation |
| Estimated (self-assessment) | `kra_scores.estimated_points`, `documents.estimated_points` | Faculty-facing |
| Verified (reviewer) | `kra_scores.verified_points`, `documents.verified_points` | After review |
| Rank simulation | `rank_simulations` | Separate estimated vs verified totals; preparatory only |

---

## Web pages inventory

**Public:** `login.html`, `forgot-password.html`  
**Admin (12):** dashboard, faculty, faculty-detail, reviewers, documents, document-view, kra-configuration, evaluation-schedule, reports, notifications, profile, audit-log  
**Reviewer (10):** dashboard, assigned-faculty, faculty-detail, documents, document-review, review-queue, kra-reference, evaluation-schedule, notifications, profile  

**Mobile screens:** splash, login, forgot password, main shell (dashboard, documents, simulation, notifications, profile), assessment, upload, document details/viewer.

---

## Implementation status

| Phase | Status |
|-------|--------|
| 1 — Inspection + contract | **This document** |
| 2 — Flask + PostgreSQL + models + migrations | **In progress** (`/api/health` + schema) |
| 3 — Auth JWT | Not started |
| 4–8 — Integrations | Not started |
