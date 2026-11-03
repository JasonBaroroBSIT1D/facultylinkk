"""
Staging preflight — confirms dedicated DB and adapter env before UI verification.

Does not write to PostgreSQL or enable production adapter.

Exit 0 = staging prerequisites met.
Exit 1 = missing facultylink_staging or other blocker.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    from config import Config
    from sqlalchemy import create_engine, text

    report: dict = {"checks": [], "blockers": []}

    db_name = urlparse(Config.database_url().replace("postgresql+psycopg", "postgresql")).path.lstrip("/")
    report["configuredDatabase"] = db_name
    report["adapterEnv"] = os.environ.get("CRITERION_B_SIMULATION_ADAPTER_ENABLED")

    if "staging" not in db_name.lower():
        report["blockers"].append(
            f"DATABASE_URL points to {db_name!r}, not a dedicated staging database "
            "(expected name containing 'staging', e.g. facultylink_staging)."
        )
    else:
        report["checks"].append("staging_database_name")

    try:
        base = Config.database_url()
        admin_url = base.rsplit("/", 1)[0] + "/postgres"
        eng = create_engine(admin_url)
        with eng.connect() as conn:
            rows = conn.execute(
                text("SELECT datname FROM pg_database WHERE datistemplate = false ORDER BY 1")
            ).fetchall()
        names = [r[0] for r in rows]
        report["postgresDatabases"] = names
        if not any("staging" in n.lower() for n in names):
            report["blockers"].append(
                "No PostgreSQL database with 'staging' in the name exists on this host."
            )
    except Exception as exc:  # noqa: BLE001
        report["blockers"].append(f"Could not list PostgreSQL databases: {exc}")

    adapter_on = (os.environ.get("CRITERION_B_SIMULATION_ADAPTER_ENABLED") or "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )
    if not adapter_on:
        report["blockers"].append(
            "CRITERION_B_SIMULATION_ADAPTER_ENABLED is not set for the staging process."
        )
    else:
        report["checks"].append("adapter_env_staging")

    if db_name == "facultylink":
        report["blockers"].append(
            "Refusing to treat production facultylink as staging. Restore/copy to facultylink_staging first."
        )

    report["ready"] = len(report["blockers"]) == 0
    print(json.dumps(report, indent=2))
    return 0 if report["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
