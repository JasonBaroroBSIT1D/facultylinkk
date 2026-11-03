# Criterion B pre-activation backup verification

Generated (UTC): 2026-11-02T19:45:06.082411+00:00

**Recommendation:** GO — Adapter not activated; await explicit user approval.

Machine-readable report: `criterion_b_pre_activation_backup_verify_20261102_194506.json`

## Fresh PostgreSQL backup

- **File:** `facultylink_pre_criterion_b_activation_20261102_194506.dump`
- **Size:** 0.079 MB (82597 bytes)
- **SHA-256:** `b7534f6947370f936122bcc2152b60656b737cdc46719380d35e029a92865eb8`
- **TOC tables (public):** 34
- **Status:** PASS

## Existing backups inspected

- `facultylink_pre_criterion_b_activation_20261102_194442.dump` — 0.079 MB — modified 2026-11-02T19:44:44.910146+00:00
- `facultylink_phase6b2_20261103_003750.dump` — 0.088 MB — modified 2026-11-02T16:37:50.997502+00:00
- `facultylink_phase6b_20261103_001359.dump` — 0.078 MB — modified 2026-11-02T16:14:00.058398+00:00
- `facultylink_20261030T042745Z.sql` — 0.001 MB — modified 2026-10-30T04:27:46.339718+00:00

## Live database (read-only)

- Alembic: `20261030_teach_eval`
- Table counts: `{"users": 3, "faculty_profiles": 1, "documents": 5, "document_ocr_jobs": 5, "document_teaching_evaluations": 0, "kra_scores": 1, "rank_simulations": 0, "kra_configuration": 6, "kra_scoring_rules": 0, "evaluation_periods": 1, "notifications": 69, "audit_logs": 262, "alembic_version": 1}`

### Jason Baroro Criterion B

```json
{
  "documents": [
    {
      "public_id": "doc_4561c33e9ce6",
      "title": "04 Library Certification",
      "status": "pending_review",
      "criterion_id": "kra1-b",
      "file_path": "faculty/1/3137063f8468474ea1f06be510e5dcad.pdf",
      "ocr_status": "completed",
      "file_size": 2478,
      "deleted": false
    },
    {
      "public_id": "doc_5149570d90a2",
      "title": "06 Coauthorship And Contribution",
      "status": "pending_review",
      "criterion_id": "kra1-b",
      "file_path": "faculty/1/cfd29f3c96a547a0b4b2ca63bfb78acd.pdf",
      "ocr_status": "completed",
      "file_size": 2520,
      "deleted": false
    },
    {
      "public_id": "doc_64d33454ab0f",
      "title": "01 Primary Textbook",
      "status": "pending_review",
      "criterion_id": "kra1-b",
      "file_path": "faculty/1/eb1d2a83515247838f9dd95ff1cd566f.pdf",
      "ocr_status": "completed",
      "file_size": 2840,
      "deleted": false
    },
    {
      "public_id": "doc_946122d0bb49",
      "title": "03 Approved Course Syllabus",
      "status": "pending_review",
      "criterion_id": "kra1-b",
      "file_path": "faculty/1/5f73bee13f6146aa992bc2127992c650.pdf",
      "ocr_status": "completed",
      "file_size": 2640,
      "deleted": false
    },
    {
      "public_id": "doc_e527d4d69609",
      "title": "02 IMDC Evaluation And Approval",
      "status": "pending_review",
      "criterion_id": "kra1-b",
      "file_path": "faculty/1/c1630c7ba94b46349380155edcc37910.pdf",
      "ocr_status": "completed",
      "file_size": 2554,
      "deleted": false
    }
  ],
  "primary": {
    "documentId": "doc_64d33454ab0f",
    "title": "01 Primary Textbook",
    "status": "pending_review",
    "reviewerPoints": 14.0,
    "hasJustification": true,
    "readyBundle": true
  },
  "supportingLinked": [
    {
      "documentId": "doc_4561c33e9ce6",
      "title": "04 Library Certification",
      "slot": "library_certification"
    },
    {
      "documentId": "doc_5149570d90a2",
      "title": "06 Coauthorship And Contribution",
      "slot": "annex_c_contribution"
    },
    {
      "documentId": "doc_946122d0bb49",
      "title": "03 Approved Course Syllabus",
      "slot": "approved_syllabus"
    },
    {
      "documentId": "doc_e527d4d69609",
      "title": "02 IMDC Evaluation And Approval",
      "slot": "imdc_evaluation_approval"
    }
  ]
}
```

## Uploaded files

- **Status:** PASS
- **Upload backup copies:** `C:\Users\gumat\OneDrive\Desktop\facultylinkk\backend\backups\uploads_pre_criterion_b_activation_20261102_194506\files` (5 files copied)
- **Missing on disk:** 0

## Restore test (disposable DB)

- **Status:** PASS
- **Temp database:** `facultylink_restore_verify_20261102194509`

## Criterion B adapter

- **Effective at verification time:** `False` (must remain `False` until approval)

## Why ~0.08 MB is reasonable for this database

- PDF bytes are **not** stored in PostgreSQL; they live under `backend/uploads/` (see file backup below).
- Live counts are small: **5** documents, **3** users, **1** faculty profile, **69** notifications, **262** audit log rows.
- Custom-format dumps use **gzip** compression; metadata + JSON (`extracted_info`) compresses well.
- `pg_restore --list` shows **167 TOC entries** and **34 public tables** (schema + data) — same shape across phase6b2 and fresh dumps.
- **WARNING:** `facultylink_20261030T042745Z.sql` (~1.3 KB) is **not** a full database backup; use the `.dump` files instead.

## OCR recovery readiness

| Item | Status |
|------|--------|
| `documents.ocr_status`, `extracted_text`, `ocr_confidence`, `extracted_info` | **PASS** — in DB backup; all 5 docs `ocr_status=completed` |
| `document_ocr_jobs` table | **PASS** — 5 rows backed up |
| Source PDFs for re-OCR | **PASS** — copied to `uploads_pre_criterion_b_activation_20261102_194506/files/` with SHA-256 in manifest |

## Criterion B evidence integrity (Jason Baroro)

| Check | Status |
|------|--------|
| One primary accomplishment | **PASS** — `doc_64d33454ab0f` |
| Four supporting links with slots | **PASS** — IMDC, syllabus, library, Annex C |
| Reviewer assessment 14 + justification | **PASS** — in bundle JSON (restored DB confirms **14.0** on primary) |
| Supporting not separate accomplishments | **PASS** — linked via `criterionBEvidenceLink.role=supporting` |

## Application recovery configuration (no secrets)

| Requirement | Notes |
|-------------|--------|
| PostgreSQL | **18.3** (dump header matches) |
| Python deps | `backend/requirements.txt` |
| Migrations | Alembic revision **`20261030_teach_eval`** (in backup) |
| File storage | `UPLOAD_FOLDER` → `backend/uploads/` (paths in `documents.file_path`) |
| OCR | Tesseract + `TESSERACT_CMD` optional (`.env.example`) |
| Env vars | `DATABASE_URL`, `JWT_SECRET_KEY`, `FLASK_SECRET_KEY`, `CORS_ORIGINS`, SMTP_* (not in dump) |
| Criterion B adapter | `CRITERION_B_SIMULATION_ADAPTER_ENABLED` — **off** until admin sets in `.env` and restarts Flask |

## File backup manifest

- **Manifest:** `backend/backups/uploads_pre_criterion_b_activation_20261102_194506/uploads_manifest.json`
- **File copies:** `backend/backups/uploads_pre_criterion_b_activation_20261102_194506/files/`
- **Latest DB pointer:** `backend/backups/LATEST_PRE_CRITERION_B_ACTIVATION_BACKUP.txt` → `facultylink_pre_criterion_b_activation_20261102_194506.dump`

## Criterion B activation readiness (preflight)

- `python scripts/criterion_b_activation_preflight.py` → **ready: true** (38 pytest passed; Jason 14 = aggregate when adapter simulated ON).
- **Adapter remains OFF** on running system until explicit approval.

## Risks / warnings

| Risk | Category |
|------|----------|
| Small dev dataset — production with more faculty will produce larger dumps | **WARNING** |
| Secrets not in backup — admin must restore `.env` securely | **WARNING** |
| `rank_simulations` table empty (0 rows) — simulation computed at runtime | **WARNING** (expected) |
| Old `.sql` backup too small for full restore | **WARNING** |

## Re-run verification

```powershell
cd backend
python scripts/criterion_b_pre_activation_backup_verify.py
```

## Restore test detail

```json
{
  "tempDatabase": "facultylink_restore_verify_20261102194509",
  "status": "PASS",
  "steps": [
    {
      "create": 0,
      "stderr": ""
    },
    {
      "restoreExitCode": 0,
      "restoreStderr": ""
    },
    {
      "counts": "     t     | count \n-----------+-------\n documents |     5\n users     |     3\n(2 rows)\n\n",
      "countsErr": ""
    },
    {
      "jasonSample": "    public_id     |              title               | pts  \n------------------+----------------------------------+------\n doc_4561c33e9ce6 | 04 Library Certification         | \n doc_946122d0bb49 | 03 Approved Course Syllabus      | \n doc_e527d4d69609 | 02 IMDC Evaluation And Approval  | \n doc_5149570d90a2 | 06 Coauthorship And Contribution | \n doc_64d33454ab0f | 01 Primary Textbook              | 14.0\n(5 rows)\n\n"
    },
    {
      "drop": 0
    }
  ]
}
```