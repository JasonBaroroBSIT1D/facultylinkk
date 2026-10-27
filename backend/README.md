# FacultyLink API (Flask + PostgreSQL)

Shared backend for the **web** (Administrator / Reviewer) and **Flutter** (Faculty) clients.

## Stack

- Flask, Flask-SQLAlchemy, Flask-Migrate, Flask-JWT-Extended, Flask-CORS  
- PostgreSQL via `psycopg`  
- Credentials in `.env` (see `.env.example`)

## Setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

1. Create one PostgreSQL database: `facultylink`.  
2. Edit `.env` with `DATABASE_URL` (never commit `.env`).  
3. Initialize migrations (first time only):

```bash
set FLASK_APP=app.py
flask db init
flask db migrate -m "Initial schema"
flask db upgrade
```

**Do not run `flask db upgrade` against a database that already contains production data without reviewing the migration SQL first.**

## Run

```bash
python app.py
```

- Health: [http://127.0.0.1:5000/api/health](http://127.0.0.1:5000/api/health)  
- When PostgreSQL is reachable, health reports `"database": "connected"`.

## First administrator (one-time)

No default passwords are shipped. After migrations are applied on an empty database:

```bash
set FLASK_APP=app.py
flask create-administrator
```

You will be prompted for email, full name, and password (hidden). The command refuses to run if an administrator already exists.

## Authentication (Phase 3)

JWT endpoints under `/api/auth/` (see [API contract](docs/API_CONTRACT.md)):

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/auth/login` | Sign in (`email` or `identity`, `password`, optional `client`: `web` \| `mobile`) |
| GET | `/api/auth/session` | Current user (Bearer access token) |
| POST | `/api/auth/refresh` | New access token (Bearer refresh token) |
| POST | `/api/auth/logout` | Revoke current access token |
| POST | `/api/auth/change-password` | Authenticated password change |
| POST | `/api/auth/forgot-password` | Start reset (generic response; email delivery TBD) |
| POST | `/api/auth/forgot-password/verify` | Verify OTP → `resetToken` |
| POST | `/api/auth/forgot-password/reset` | Complete reset with `resetToken` |

Role probes for integration testing: `/api/auth/probe/administrator`, `/probe/reviewer`, `/probe/faculty`.

## Tests

FacultyLink uses **one** PostgreSQL database (`facultylink`) for the application. Pytest does **not** create or write to that database.

```bash
pytest
```

- **`test_health.py`** — read-only check against `facultylink` via `GET /api/health` (`SELECT 1` only).
- **`test_auth.py`** — skipped until an isolated PostgreSQL test database or other strategy is added (never run destructive tests against `facultylink`).

## Docs

- [API contract (Phase 1)](docs/API_CONTRACT.md)

## Guideline

UI and configuration reference **DBM–CHED Joint Circular No. 01, s. 2026**. Official scoring formulas and thresholds are loaded from admin configuration after validation—not hardcoded in application logic.
