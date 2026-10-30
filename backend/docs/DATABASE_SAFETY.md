# FacultyLink database safety

FacultyLink uses **one** PostgreSQL database: `facultylink` on `127.0.0.1:5432`.

## Rules

1. **Never** call `db.drop_all()` or `db.create_all()` in tests or application startup.
2. **Never** use SQLite or `:memory:` URIs for this project.
3. **Never** run pytest integration tests that INSERT/UPDATE/DELETE against `facultylink` unless you have restored a **copy** and set `FACULTYLINK_ALLOW_DB_WRITES=1`.
4. Schema changes use **Alembic only** (`flask db upgrade`), after review and backup.
5. Uploaded files under `backend/uploads/` are independent of PostgreSQL; rebuilding tables does not restore document **rows** or re-link files automatically.

## Pytest guards

- `tests/db_safety.py` blocks `db.create_all()` / `db.drop_all()` while pytest is running.
- Tests marked `@pytest.mark.db_write` are **skipped** unless `FACULTYLINK_ALLOW_DB_WRITES=1`.
- The `app` fixture refuses non-`facultylink` database names and SQLite URIs.

## Read-only schema check

```powershell
cd backend
$env:PYTHONPATH = "."
python scripts/inspect_schema_readonly.py
```

## First administrator (after schema exists)

```powershell
cd backend
python -m flask --app app create-administrator
```

Interactive prompts; does not run automatically.
