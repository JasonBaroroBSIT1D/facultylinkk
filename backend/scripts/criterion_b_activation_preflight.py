"""
Single-system Criterion B adapter preflight (facultylink + port 5000).

Read-only on PostgreSQL. Does not enable the adapter or mutate data.

Run before you add CRITERION_B_SIMULATION_ADAPTER_ENABLED=1 to backend/.env:

  cd backend
  python scripts/criterion_b_activation_preflight.py
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKUPS = ROOT / "backups"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _latest_backup() -> tuple[Path | None, str]:
    pointer = BACKUPS / "LATEST_PHASE6B2_BACKUP.txt"
    if pointer.is_file():
        name = pointer.read_text(encoding="utf-8").strip()
        path = BACKUPS / name
        if path.is_file():
            return path, "LATEST_PHASE6B2_BACKUP.txt"
    dumps = sorted(BACKUPS.glob("facultylink_*.dump"), key=lambda p: p.stat().st_mtime, reverse=True)
    if dumps:
        return dumps[0], "newest facultylink_*.dump"
    sql = sorted(BACKUPS.glob("facultylink_*.sql"), key=lambda p: p.stat().st_mtime, reverse=True)
    if sql:
        return sql[0], "newest facultylink_*.sql"
    return None, "none found"


def _run_pytest() -> dict:
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/staging/test_criterion_b_activation_scenarios.py",
        "tests/documents/test_criterion_b_current_score_integration.py",
        "tests/faculty/test_rank_simulation_criterion_b_wiring.py",
        "tests/documents/test_criterion_b_simulation_adapter.py",
        "-q",
    ]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    return {
        "exitCode": proc.returncode,
        "stdout": (proc.stdout or "")[-2000:],
        "stderr": (proc.stderr or "")[-1000:],
    }


def main() -> int:
    import os
    from urllib.parse import urlparse

    from config import Config

    report: dict = {
        "tag": "CRITERION-B-ACTIVATION-PREFLIGHT",
        "startedAt": datetime.now(timezone.utc).isoformat(),
        "system": "single_database_single_backend",
        "checks": [],
        "warnings": [],
        "blockers": [],
    }

    db_name = urlparse(Config.database_url().replace("postgresql+psycopg", "postgresql")).path.lstrip("/")
    report["database"] = db_name
    report["adapterEnvRaw"] = os.environ.get("CRITERION_B_SIMULATION_ADAPTER_ENABLED")
    from documents.scoring.criterion_b_simulation_adapter import CRITERION_B_SIMULATION_ADAPTER_ENABLED

    report["adapterEnabledAtImport"] = CRITERION_B_SIMULATION_ADAPTER_ENABLED

    if db_name != "facultylink":
        report["warnings"].append(f"Expected database name facultylink, got {db_name!r}.")

    backup_path, backup_source = _latest_backup()
    if backup_path is None:
        report["blockers"].append(
            "No restorable backup found under backend/backups/ (facultylink_*.dump or .sql)."
        )
    else:
        size_mb = round(backup_path.stat().st_size / (1024 * 1024), 2)
        report["backup"] = {
            "path": str(backup_path),
            "source": backup_source,
            "sizeMb": size_mb,
        }
        report["checks"].append("restorable_backup_present")
        if size_mb < 0.01:
            report["warnings"].append("Backup file is very small — confirm it is valid.")

    if CRITERION_B_SIMULATION_ADAPTER_ENABLED:
        report["warnings"].append(
            "Adapter is already ON in this process. For pre-activation checklist, restart Flask with env unset."
        )
    else:
        report["checks"].append("adapter_off_until_env_set")

    pytest_result = _run_pytest()
    report["pytest"] = pytest_result
    if pytest_result["exitCode"] == 0:
        report["checks"].append("automated_regression_passed")
    else:
        report["blockers"].append("Automated regression pytest failed (see report pytest stdout).")

    # Read-only Jason / Criterion B snapshot (adapter simulated in-process, no DB writes)
    try:
        import importlib.util

        verify_path = ROOT / "scripts" / "criterion_b_staging_activation_verify.py"
        spec = importlib.util.spec_from_file_location("cb_verify", verify_path)
        ro = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(ro)

        from factory import create_app

        app = create_app(Config)
        with app.app_context():
            hits = ro._find_jason_primary_docs(None)
            if not hits:
                report["warnings"].append("No Jason Baroro Criterion B primary found for live read-only check.")
            else:
                hit = hits[0]
                snap = ro._accomplishment_snapshot(hit["document"])
                before = ro._kra1_sim_block(hit["profile"], adapter_on=False)
                after = ro._kra1_sim_block(hit["profile"], adapter_on=True)
                report["liveReadOnly"] = {
                    "accomplishment": snap,
                    "beforeAdapterEnvOff": before,
                    "afterAdapterSimulatedOn": after,
                }
                cur = snap.get("currentScorePoints")
                agg = after.get("criterionBEstimatedPoints")
                if cur is not None and agg is not None and float(cur) != float(agg):
                    report["blockers"].append(
                        "Simulated adapter-on aggregate does not match accomplishment current score."
                    )
                elif cur is not None and agg is not None:
                    report["checks"].append("jason_current_score_matches_aggregate_when_adapter_on")
    except Exception as exc:  # noqa: BLE001
        report["warnings"].append(f"Live read-only check skipped or failed: {exc}")

    report["readyForActivationApproval"] = len(report["blockers"]) == 0
    report["activationSteps"] = (
        "See backend/docs/CRITERION_B_SINGLE_SYSTEM_ACTIVATION.md — add env var to backend/.env, restart Flask :5000."
    )
    report["finishedAt"] = datetime.now(timezone.utc).isoformat()

    out = BACKUPS / f"criterion_b_activation_preflight_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"ready": report["readyForActivationApproval"], "report": str(out)}, indent=2))
    return 0 if report["readyForActivationApproval"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
