# PostgreSQL backup procedure (facultylink)

**Do not run until you approve.** These commands only read/dump; they do not modify application data.

## Prerequisites

- PostgreSQL 18 service running
- Password for user `postgres` (from your local `.env`, not committed)
- `pg_dump` on PATH (`C:\Program Files\PostgreSQL\18\bin`)

## Full logical backup (recommended before migrations)

Replace `YOUR_PASSWORD` with your actual password, or use a `.pgpass` file.

```powershell
$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$out = "C:\Users\gumat\OneDrive\Desktop\facultylinkk\backend\backups\facultylink_$ts.sql"
New-Item -ItemType Directory -Force -Path (Split-Path $out) | Out-Null
& "C:\Program Files\PostgreSQL\18\bin\pg_dump.exe" `
  -h 127.0.0.1 -p 5432 -U postgres -d facultylink `
  -F p -f $out
```

Custom format (smaller, supports selective restore):

```powershell
& "C:\Program Files\PostgreSQL\18\bin\pg_dump.exe" `
  -h 127.0.0.1 -p 5432 -U postgres -d facultylink `
  -F c -f "...\facultylink_$ts.dump"
```

## Restore (only on empty or replacement database — requires explicit approval)

Plain SQL:

```powershell
psql -h 127.0.0.1 -p 5432 -U postgres -d facultylink -f path\to\backup.sql
```

Custom format:

```powershell
pg_restore -h 127.0.0.1 -p 5432 -U postgres -d facultylink --clean --if-exists path\to\backup.dump
```

**Warning:** `--clean` drops objects before restore. Use only when you intend to replace schema/data.

## What to back up besides PostgreSQL

- `backend/uploads/` (faculty document files on disk)
- `backend/backups/` (existing SET/SEF export folders, if any)
- `backend/.env` (store securely, not in git)
