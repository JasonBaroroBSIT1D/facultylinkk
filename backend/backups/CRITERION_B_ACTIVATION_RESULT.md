# Criterion B scoring integration — activation result

**Activation timestamp (UTC):** 2026-11-02T19:51:34Z  
**Live verification pass (UTC):** 2026-11-02T20:05:00Z (approx.)  
**System:** Single PostgreSQL `facultylink`, single Flask backend on port **5000**  
**Rollback executed:** No  

---

## Final activation status: **PARTIAL**

| Area | Status |
|------|--------|
| Env: `.env` adapter wins over shell `=0` | **SUCCESS** (code fix + verified) |
| Flask `:5000` health + adapter ON after normal restart | **SUCCESS** |
| Jason integrated scores (read-only handlers) | **SUCCESS** — 14 pts |
| Regression tests (38 pytest + JS + Flutter unit) | **SUCCESS** |
| Live HTTP JWT `estimated-assessment` | **NOT TESTED** — no reviewer password supplied to automation |
| Reviewer Web KRA UI (logged-in) | **NOT TESTED** — login required; automation has no reviewer session |
| Flutter device/emulator live UI | **NOT TESTED** — handler parity only; device not driven in this pass |

Adapter remains **ON**. Full **SUCCESS** requires you to sign in on Reviewer Web and Faculty Mobile once (see below).

---

## Task 1 — Environment configuration (fixed)

**Cause:** `load_dotenv()` does not override existing process environment. Cursor/agent shells often set `CRITERION_B_SIMULATION_ADAPTER_ENABLED=0`, which masked `backend/.env=1`.

**Fix (minimal):**

- `backend/config.py` — after loading `.env`, apply `CRITERION_B_SIMULATION_ADAPTER_ENABLED` from `backend/.env` when present.
- `backend/app.py` and `backend/factory.py` — import `config` before other modules so precedence runs early.

**Verification (shell forced to `0`, `.env` = `1`):**

- Fresh Python import: adapter **True**
- `GET http://127.0.0.1:5000/api/health` → **200**, database connected
- In-process reviewer assessment payload: Criterion B / KRA I / sim total **14**

Restart Flask with only `python app.py` from `backend/` (no need to export adapter in the shell).

---

## Task 2 — Reviewer Web

**404 root cause:** Port **8080** on this machine is **Apache `httpd`**, not the FacultyLink `web/` tree (`index.html` could respond while `pages/public/login.html` returned 404).

**Fix:** Serve static files from `web/` on **8081**:

```powershell
cd web
.\serve-dev.ps1          # default port 8081
# Login URL: http://127.0.0.1:8081/pages/public/login.html
```

**Automation browser:** Login page loads at **8081**; deep link to Jason faculty detail redirects to login (no stored reviewer JWT in the automation browser profile).

**Assigned reviewer account (for manual login):** `jaso.jary@gmail.com` (password not available to automation — do not reset).

**Manual checklist after you sign in:**

1. Assigned Faculty → **Jason Baroro** → KRA Scores → KRA I → Criterion B **14**
2. KRA I total **14/100** (if no other eligible points)
3. **Reviewer Assessed** active; no “(preview)” / preview-only footnote
4. Refresh page — values unchanged
5. Supporting PDFs not listed as separate Criterion B accomplishments

---

## Task 3 — Authenticated live API

| Check | Result |
|-------|--------|
| `GET /api/health` | **PASS** |
| `GET /api/reviewer/faculty/fac_6047265f5ce9/estimated-assessment` (Bearer JWT) | **NOT TESTED** — blocker: no authorized reviewer session/password in automation |

**Handler parity (same code as live endpoint, read-only, no JWT logged):**

| Field | Value |
|-------|--------|
| `kra1-b` estimatedPoints | **14** |
| KRA I estimatedPoints | **14** |
| estimatedTotalKraPoints | **14** |
| simulationAdapterEnabled (criterion B row) | **true** |

Optional live JWT check (session-only, not committed):

```powershell
cd backend
$env:ACTIVATION_VERIFY_REVIEWER_EMAIL = "jaso.jary@gmail.com"
$env:ACTIVATION_VERIFY_REVIEWER_PASSWORD = "<your reviewer password>"
python scripts/criterion_b_post_activation_live_check.py
```

---

## Task 4 — Faculty Flutter mobile

**Faculty account (Jason):** `jasonbaroro5@gmail.com`  
**API target:** same Flask `:5000` (emulator `10.0.2.2:5000`; USB `adb reverse` + `127.0.0.1:5000`; Wi‑Fi `--dart-define=FL_API_BASE_URL=http://<LAN-IP>:5000`).

**Automation:** Did not drive the running Flutter app UI in this pass.

**Handler parity for `GET /api/faculty/me/rank-simulation` (Jason profile, adapter ON):**

| Field | Value |
|-------|--------|
| Criterion B (`kra1-b`) | **14** |
| Rank simulation total KRA | **14** |
| `simulationAdapterEnabled` on Criterion B | **true** |

**Manual:** Sign in as Jason → My Saved Work → Criterion B accomplishment **14 pts — Reviewer Assessed** → Dashboard KRA I **14** → Rank Simulation **14**.

---

## Task 5 — Regression and safety

| Check | Result |
|-------|--------|
| Pytest Criterion B suites | **PASS** (23 + prior 38 full suite) |
| Web JS integration test | **PASS** |
| Flutter display unit tests | **PASS** (3/3) |
| DB writes / migrations / SMTP | **None** |
| Uploaded files | **Not modified** |
| Adapter after restart with shell `=0` | **ON** (via `.env` precedence) |

---

## Jason Baroro reference

| Item | Value |
|------|--------|
| Faculty public ID | `fac_6047265f5ce9` |
| Primary document | `doc_64d33454ab0f` |
| System estimate (audit) | **15** |
| Reviewer / current score | **14** |

---

## Rollback (not executed)

1. `CRITERION_B_SIMULATION_ADAPTER_ENABLED=0` in `backend/.env`
2. Restart Flask on **5000**
3. No database restore unless explicitly approved

---

## Artifacts

| File | Purpose |
|------|---------|
| `web/serve-dev.ps1` | Static server on **8081** (avoids Apache on 8080) |
| `backend/scripts/criterion_b_post_activation_live_check.py` | Health + optional JWT + in-process parity |
| `backend/backups/criterion_b_staging_activation_report_20261102_195202.json` | Read-only Jason verify |

---

## Summary

- **One DB, one backend:** unchanged  
- **Adapter:** **ON**, `.env` is authoritative for restarts  
- **Scoring:** **14** integrated in backend handlers  
- **Remaining for SUCCESS:** Reviewer Web + Flutter **manual login** verification; optional JWT script with your reviewer password  
