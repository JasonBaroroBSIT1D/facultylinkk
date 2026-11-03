"""
Pre-activation backup verification (read-only on facultylink; optional disposable restore DB).

Does NOT activate Criterion B adapter or mutate live data.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
BACKUPS = ROOT / "backups"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

PG_BIN = Path(r"C:\Program Files\PostgreSQL\18\bin")
JASON_HINT = "Jason Baroro"


def _pg_tool(name: str) -> Path:
    p = PG_BIN / f"{name}.exe"
    if p.is_file():
        return p
    found = os.environ.get("PATH", "")
    return Path(name)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _db_conn_parts() -> dict[str, str]:
    from config import Config

    url = Config.database_url().replace("postgresql+psycopg", "postgresql")
    p = urlparse(url)
    return {
        "host": p.hostname or "127.0.0.1",
        "port": str(p.port or 5432),
        "user": p.username or "postgres",
        "password": p.password or "",
        "dbname": p.path.lstrip("/").split("?")[0],
    }


def _run_pg_dump(out_path: Path) -> dict[str, Any]:
    conn = _db_conn_parts()
    if conn["dbname"] != "facultylink":
        return {"ok": False, "error": f"Refusing dump: dbname is {conn['dbname']!r}"}
    env = os.environ.copy()
    if conn["password"]:
        env["PGPASSWORD"] = conn["password"]
    cmd = [
        str(_pg_tool("pg_dump")),
        "-Fc",
        "--no-owner",
        "--no-privileges",
        "-h",
        conn["host"],
        "-p",
        conn["port"],
        "-U",
        conn["user"],
        "-f",
        str(out_path),
        conn["dbname"],
    ]
    proc = subprocess.run(cmd, env=env, capture_output=True, text=True)
    return {
        "ok": proc.returncode == 0,
        "exitCode": proc.returncode,
        "stderr": (proc.stderr or "")[-1500:] if proc.returncode else "",
        "path": str(out_path),
    }


def _pg_restore_list(dump_path: Path) -> dict[str, Any]:
    proc = subprocess.run(
        [str(_pg_tool("pg_restore")), "--list", str(dump_path)],
        capture_output=True,
        text=True,
    )
    lines = (proc.stdout or "").splitlines()
    header = [ln for ln in lines[:15] if ln.strip()]
    tables = [ln for ln in lines if " TABLE " in ln and "public" in ln]
    return {
        "ok": proc.returncode == 0,
        "exitCode": proc.returncode,
        "header": header,
        "tableCount": len(tables),
        "tablesSample": tables[:25],
        "stderr": (proc.stderr or "")[-500:],
    }


def _inspect_existing_backups() -> list[dict[str, Any]]:
    rows = []
    for pattern in ("*.dump", "*.sql"):
        for path in sorted(BACKUPS.glob(f"facultylink*{pattern}"), key=lambda p: p.stat().st_mtime, reverse=True):
            item: dict[str, Any] = {
                "name": path.name,
                "sizeBytes": path.stat().st_size,
                "sizeMb": round(path.stat().st_size / (1024 * 1024), 3),
                "modifiedUtc": datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat(),
            }
            if path.suffix == ".dump":
                item["toc"] = _pg_restore_list(path)
            rows.append(item)
    return rows


def _live_db_inventory() -> dict[str, Any]:
    from factory import create_app
    from config import Config
    from sqlalchemy import text
    from extensions import db

    app = create_app(Config)
    inv: dict[str, Any] = {"tables": {}, "jason": {}}
    with app.app_context():
        tables = [
            "users",
            "faculty_profiles",
            "documents",
            "document_ocr_jobs",
            "document_teaching_evaluations",
            "kra_scores",
            "rank_simulations",
            "kra_configuration",
            "kra_scoring_rules",
            "evaluation_periods",
            "notifications",
            "audit_logs",
            "alembic_version",
        ]
        for t in tables:
            try:
                n = db.session.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar()
                inv["tables"][t] = int(n)
            except Exception as exc:  # noqa: BLE001
                db.session.rollback()
                inv["tables"][t] = f"error:{type(exc).__name__}"

        rev = db.session.execute(
            text(
                """
                SELECT d.public_id, d.title, d.status, d.criterion_id, d.file_path,
                       d.ocr_status, d.file_size, d.deleted_at IS NOT NULL AS deleted
                FROM documents d
                JOIN faculty_profiles fp ON fp.id = d.faculty_profile_id
                JOIN users u ON u.id = fp.user_id
                WHERE u.full_name ILIKE :name
                ORDER BY d.criterion_id, d.public_id
                """
            ),
            {"name": f"%{JASON_HINT}%"},
        ).mappings().all()
        inv["jason"]["documents"] = [dict(r) for r in rev]

        primary = None
        for row in inv["jason"]["documents"]:
            if row.get("criterion_id") == "kra1-b" and not row.get("deleted"):
                info_q = db.session.execute(
                    text("SELECT extracted_info FROM documents WHERE public_id = :pid"),
                    {"pid": row["public_id"]},
                ).scalar()
                info = info_q if isinstance(info_q, dict) else {}
                bundle = info.get("criterionBEvidenceBundle") or info.get("criterion_b_evidence_bundle")
                link = info.get("criterionBEvidenceLink")
                role = (link or {}).get("role") if isinstance(link, dict) else None
                if role != "supporting" and isinstance(bundle, dict):
                    primary = row["public_id"]
                    assessment = (bundle.get("reviewerProposedAssessment") or {}) if bundle else {}
                    inv["jason"]["primary"] = {
                        "documentId": primary,
                        "title": row.get("title"),
                        "status": row.get("status"),
                        "reviewerPoints": assessment.get("points"),
                        "hasJustification": bool((assessment.get("justification") or "").strip()),
                        "readyBundle": bool(bundle),
                    }
                    break

        if primary:
            linked = []
            for row in inv["jason"]["documents"]:
                if row.get("criterion_id") != "kra1-b" or row.get("deleted"):
                    continue
                info_q = db.session.execute(
                    text("SELECT extracted_info FROM documents WHERE public_id = :pid"),
                    {"pid": row["public_id"]},
                ).scalar()
                info = info_q if isinstance(info_q, dict) else {}
                link = info.get("criterionBEvidenceLink")
                if isinstance(link, dict) and link.get("role") == "supporting":
                    if link.get("primaryDocumentId") == primary:
                        linked.append(
                            {
                                "documentId": row["public_id"],
                                "title": row.get("title"),
                                "slot": link.get("evidenceSlot"),
                            }
                        )
            inv["jason"]["supportingLinked"] = linked

        inv["alembic"] = db.session.execute(text("SELECT version_num FROM alembic_version")).scalar()

    return inv


def _upload_inventory() -> dict[str, Any]:
    from config import Config

    upload_root = Path(Config.UPLOAD_FOLDER)
    manifest = []
    missing_paths = []
    from factory import create_app
    from sqlalchemy import text
    from extensions import db

    app = create_app(Config)
    with app.app_context():
        rows = db.session.execute(
            text(
                """
                SELECT public_id, file_path, file_name, mime_type, file_size, deleted_at IS NOT NULL AS deleted
                FROM documents
                WHERE file_path IS NOT NULL AND file_path <> ''
                """
            )
        ).mappings().all()

    for row in rows:
        rel = row["file_path"]
        abs_path = upload_root / rel if not Path(rel).is_absolute() else Path(rel)
        exists = abs_path.is_file()
        entry = {
            "documentId": row["public_id"],
            "relativePath": str(rel).replace("\\", "/"),
            "fileName": row["file_name"],
            "mimeType": row["mime_type"],
            "dbFileSize": row["file_size"],
            "deleted": row["deleted"],
            "existsOnDisk": exists,
        }
        if exists:
            entry["diskSize"] = abs_path.stat().st_size
            entry["sha256"] = _sha256(abs_path)
        else:
            missing_paths.append(entry["relativePath"])
        manifest.append(entry)

    # Files on disk not referenced (informational)
    disk_orphans = []
    if upload_root.is_dir():
        for path in upload_root.rglob("*"):
            if path.is_file():
                rel = path.relative_to(upload_root).as_posix()
                if not any(m["relativePath"].replace("\\", "/") == rel for m in manifest if m["existsOnDisk"]):
                    disk_orphans.append(rel)

    return {
        "uploadRoot": str(upload_root),
        "referencedFiles": len(manifest),
        "missingOnDisk": missing_paths,
        "diskOrphans": disk_orphans[:50],
        "manifest": manifest,
    }


def _try_disposable_restore(dump_path: Path) -> dict[str, Any]:
    """Restore into a uniquely named temporary DB; drop only that DB on success."""
    conn = _db_conn_parts()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    temp_db = f"facultylink_restore_verify_{stamp}"
    env = os.environ.copy()
    if conn["password"]:
        env["PGPASSWORD"] = conn["password"]
    psql_base = [
        str(_pg_tool("psql")),
        "-h",
        conn["host"],
        "-p",
        conn["port"],
        "-U",
        conn["user"],
        "-v",
        "ON_ERROR_STOP=1",
    ]

    def psql(db: str, sql: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            psql_base + ["-d", db, "-c", sql],
            env=env,
            capture_output=True,
            text=True,
        )

    result: dict[str, Any] = {"tempDatabase": temp_db, "status": "NOT TESTED", "steps": []}
    forbidden = {"facultylink", "facultylink_test", "postgres", "template0", "template1"}
    if temp_db in forbidden or not temp_db.startswith("facultylink_restore_verify_"):
        result["error"] = "Refused unsafe temp database name"
        return result

    create = psql("postgres", f'CREATE DATABASE "{temp_db}";')
    result["steps"].append({"create": create.returncode, "stderr": (create.stderr or "")[-300:]})
    if create.returncode != 0:
        result["status"] = "FAIL"
        return result

    restore = subprocess.run(
        [
            str(_pg_tool("pg_restore")),
            "-h",
            conn["host"],
            "-p",
            conn["port"],
            "-U",
            conn["user"],
            "-d",
            temp_db,
            "--no-owner",
            "--no-privileges",
            str(dump_path),
        ],
        env=env,
        capture_output=True,
        text=True,
    )
    result["steps"].append(
        {
            "restoreExitCode": restore.returncode,
            "restoreStderr": (restore.stderr or "")[-2000:],
        }
    )
    if restore.returncode != 0:
        psql("postgres", f'DROP DATABASE IF EXISTS "{temp_db}";')
        result["status"] = "FAIL"
        return result

    counts = psql(
        temp_db,
        "SELECT 'documents' t, COUNT(*) FROM documents UNION ALL SELECT 'users', COUNT(*) FROM users;",
    )
    result["steps"].append({"counts": counts.stdout, "countsErr": (counts.stderr or "")[-200:]})

    jason = psql(
        temp_db,
        """
        SELECT d.public_id, d.title,
               (d.extracted_info->'criterionBEvidenceBundle'->'reviewerProposedAssessment'->>'points') AS pts
        FROM documents d
        JOIN faculty_profiles fp ON fp.id = d.faculty_profile_id
        JOIN users u ON u.id = fp.user_id
        WHERE u.full_name ILIKE '%Jason Baroro%'
          AND d.criterion_id = 'kra1-b'
          AND d.deleted_at IS NULL
        LIMIT 5;
        """,
    )
    result["steps"].append({"jasonSample": jason.stdout})

    drop = psql("postgres", f'DROP DATABASE IF EXISTS "{temp_db}";')
    result["steps"].append({"drop": drop.returncode})
    result["status"] = "PASS" if restore.returncode == 0 and drop.returncode == 0 else "FAIL"
    return result


def _file_backup_manifest(out_dir: Path, upload_inv: dict[str, Any]) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = out_dir / "uploads_manifest.json"
    manifest_path.write_text(json.dumps(upload_inv, indent=2), encoding="utf-8")
    return manifest_path


def main() -> int:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    report: dict[str, Any] = {
        "tag": "CRITERION-B-PRE-ACTIVATION-BACKUP-VERIFY",
        "startedAt": datetime.now(timezone.utc).isoformat(),
        "adapterEnabled": None,
        "sections": {},
        "summary": {},
    }

    from documents.scoring.criterion_b_simulation_adapter import CRITERION_B_SIMULATION_ADAPTER_ENABLED

    report["adapterEnabled"] = CRITERION_B_SIMULATION_ADAPTER_ENABLED
    report["sections"]["existingBackups"] = {"status": "PASS", "items": _inspect_existing_backups()}

    fresh_name = f"facultylink_pre_criterion_b_activation_{stamp}.dump"
    fresh_path = BACKUPS / fresh_name
    dump_result = _run_pg_dump(fresh_path)
    if dump_result.get("ok"):
        toc = _pg_restore_list(fresh_path)
        checksum = _sha256(fresh_path)
        report["sections"]["freshBackup"] = {
            "status": "PASS" if toc.get("ok") else "WARNING",
            "filename": fresh_name,
            "sizeBytes": fresh_path.stat().st_size,
            "sizeMb": round(fresh_path.stat().st_size / (1024 * 1024), 3),
            "sha256": checksum,
            "toc": toc,
        }
        (BACKUPS / "LATEST_PRE_CRITERION_B_ACTIVATION_BACKUP.txt").write_text(fresh_name + "\n", encoding="utf-8")
    else:
        report["sections"]["freshBackup"] = {"status": "FAIL", **dump_result}

    report["sections"]["liveDatabase"] = {"status": "PASS", "inventory": _live_db_inventory()}

    upload_inv = _upload_inventory()
    file_backup_dir = BACKUPS / f"uploads_pre_criterion_b_activation_{stamp}"
    manifest_path = _file_backup_manifest(file_backup_dir, upload_inv)
    # Copy existing files to backup folder (no move)
    from config import Config

    upload_root = Path(Config.UPLOAD_FOLDER)
    copied = 0
    if upload_root.is_dir():
        for entry in upload_inv["manifest"]:
            if not entry.get("existsOnDisk"):
                continue
            src = upload_root / entry["relativePath"]
            dst = file_backup_dir / "files" / entry["relativePath"]
            dst.parent.mkdir(parents=True, exist_ok=True)
            if not dst.exists():
                dst.write_bytes(src.read_bytes())
                copied += 1
    upload_status = "PASS" if not upload_inv["missingOnDisk"] else "WARNING"
    report["sections"]["uploadedFiles"] = {
        "status": upload_status,
        "manifestPath": str(manifest_path),
        "backupCopyDir": str(file_backup_dir / "files"),
        "filesCopied": copied,
        "missingOnDiskCount": len(upload_inv["missingOnDisk"]),
        "missingSample": upload_inv["missingOnDisk"][:20],
    }

    if dump_result.get("ok"):
        report["sections"]["restoreTest"] = _try_disposable_restore(fresh_path)
    else:
        report["sections"]["restoreTest"] = {"status": "NOT TESTED", "reason": "Fresh backup failed"}

    preflight = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "criterion_b_activation_preflight.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    report["sections"]["activationPreflight"] = {
        "status": "PASS" if preflight.returncode == 0 else "FAIL",
        "stdout": (preflight.stdout or "")[-1000:],
    }

    # Overall GO/NO-GO
    fails = []
    for key, sec in report["sections"].items():
        if isinstance(sec, dict) and sec.get("status") == "FAIL":
            fails.append(key)
    if report["adapterEnabled"]:
        fails.append("adapter_must_stay_off")
    go = len(fails) == 0 and report["sections"].get("restoreTest", {}).get("status") == "PASS"
    if report["sections"].get("uploadedFiles", {}).get("status") == "WARNING":
        go = False
    report["summary"] = {
        "recommendation": "GO" if go else "NO-GO",
        "failures": fails,
        "note": "Adapter not activated; await explicit user approval.",
    }

    json_path = BACKUPS / f"criterion_b_pre_activation_backup_verify_{stamp}.json"
    json_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    _write_markdown(report, stamp, json_path)
    print(json.dumps(report["summary"], indent=2))
    print(f"JSON: {json_path}")
    return 0 if go else 1


def _write_markdown(report: dict, stamp: str, json_path: Path) -> None:
    md_path = BACKUPS / "CRITERION_B_PRE_ACTIVATION_BACKUP_VERIFICATION.md"
    fb = report["sections"].get("freshBackup", {})
    rt = report["sections"].get("restoreTest", {})
    uf = report["sections"].get("uploadedFiles", {})
    live = report["sections"].get("liveDatabase", {}).get("inventory", {})
    jason = live.get("jason", {})

    lines = [
        "# Criterion B pre-activation backup verification",
        "",
        f"Generated (UTC): {report.get('startedAt')}",
        "",
        f"**Recommendation:** {report['summary']['recommendation']} — {report['summary']['note']}",
        "",
        f"Machine-readable report: `{json_path.name}`",
        "",
        "## Fresh PostgreSQL backup",
        "",
        f"- **File:** `{fb.get('filename', 'n/a')}`",
        f"- **Size:** {fb.get('sizeMb', 'n/a')} MB ({fb.get('sizeBytes', 'n/a')} bytes)",
        f"- **SHA-256:** `{fb.get('sha256', 'n/a')}`",
        f"- **TOC tables (public):** {fb.get('toc', {}).get('tableCount', 'n/a')}",
        f"- **Status:** {fb.get('status', 'n/a')}",
        "",
        "## Existing backups inspected",
        "",
    ]
    for item in report["sections"].get("existingBackups", {}).get("items", [])[:8]:
        lines.append(f"- `{item['name']}` — {item['sizeMb']} MB — modified {item['modifiedUtc']}")

    lines.extend(
        [
            "",
            "## Live database (read-only)",
            "",
            f"- Alembic: `{live.get('alembic')}`",
            f"- Table counts: `{json.dumps(live.get('tables', {}))}`",
            "",
            "### Jason Baroro Criterion B",
            "",
            f"```json\n{json.dumps(jason, indent=2)}\n```",
            "",
            "## Uploaded files",
            "",
            f"- **Status:** {uf.get('status')}",
            f"- **Upload backup copies:** `{uf.get('backupCopyDir')}` ({uf.get('filesCopied')} files copied)",
            f"- **Missing on disk:** {uf.get('missingOnDiskCount')}",
            "",
            "## Restore test (disposable DB)",
            "",
            f"- **Status:** {rt.get('status')}",
            f"- **Temp database:** `{rt.get('tempDatabase', 'n/a')}`",
            "",
            "## Criterion B adapter",
            "",
            f"- **Effective at verification time:** `{report.get('adapterEnabled')}` (must remain `False` until approval)",
            "",
            "## Restore test detail",
            "",
            f"```json\n{json.dumps(rt, indent=2)[:4000]}\n```",
        ]
    )
    md_path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
