"""Read-only schema inspection (no DDL/DML). Safe to run anytime."""

from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from urllib.parse import urlparse

_BACKEND = Path(__file__).resolve().parents[1]
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

load_dotenv(_BACKEND / ".env")

from config import Config  # noqa: E402


def main() -> None:
    url = Config.database_url()
    parsed = urlparse(url.replace("postgresql+psycopg", "postgresql"))
    print(f"host={parsed.hostname} port={parsed.port} database={parsed.path.lstrip('/')}")
    engine = create_engine(url)
    with engine.connect() as conn:
        tables = [
            row[0]
            for row in conn.execute(
                text(
                    "SELECT tablename FROM pg_tables "
                    "WHERE schemaname = 'public' ORDER BY tablename"
                )
            )
        ]
        print("public_tables:", tables)
        if "alembic_version" in tables:
            versions = [
                row[0]
                for row in conn.execute(text("SELECT version_num FROM alembic_version"))
            ]
            print("alembic_version:", versions)


if __name__ == "__main__":
    main()
