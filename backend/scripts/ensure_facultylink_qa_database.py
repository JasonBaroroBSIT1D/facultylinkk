"""Create facultylink_qa if missing (requires superuser URL to postgres maintenance DB)."""

from __future__ import annotations

import os
import sys

from sqlalchemy import create_engine, text


def main() -> int:
    maint = (os.environ.get("FACULTYLINK_PG_MAINTENANCE_URL") or "").strip()
    if not maint:
        print("Set FACULTYLINK_PG_MAINTENANCE_URL to a superuser postgres URL.", file=sys.stderr)
        return 2
    name = "facultylink_qa"
    engine = create_engine(maint, isolation_level="AUTOCOMMIT")
    with engine.connect() as conn:
        exists = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :n"),
            {"n": name},
        ).scalar()
        if exists:
            print(f"{name} already exists")
            return 0
        conn.execute(text(f'CREATE DATABASE "{name}"'))
        print(f"Created {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
