"""Read-only post-rebuild verification (tables, FKs, indexes, Alembic)."""

from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

_BACKEND = Path(__file__).resolve().parents[1]
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

load_dotenv(_BACKEND / ".env")

from config import Config  # noqa: E402

EXPECTED_TABLES = sorted(
    [
        "account_activation_tokens",
        "alembic_version",
        "audit_logs",
        "auth_rate_limit_events",
        "document_ocr_jobs",
        "document_teaching_evaluations",
        "documents",
        "evaluation_periods",
        "faculty_profiles",
        "kra_configuration",
        "kra_scores",
        "kra_scoring_rules",
        "notifications",
        "password_reset_requests",
        "rank_simulations",
        "revoked_tokens",
        "users",
    ]
)


def main() -> int:
    engine = create_engine(Config.database_url())
    with engine.connect() as conn:
        tables = sorted(
            row[0]
            for row in conn.execute(
                text(
                    "SELECT tablename FROM pg_tables "
                    "WHERE schemaname = 'public' ORDER BY tablename"
                )
            )
        )
        print("tables_count", len(tables))
        print("tables", tables)
        if tables != EXPECTED_TABLES:
            missing = set(EXPECTED_TABLES) - set(tables)
            extra = set(tables) - set(EXPECTED_TABLES)
            if missing:
                print("ERROR missing_tables", sorted(missing))
            if extra:
                print("ERROR unexpected_tables", sorted(extra))
            return 1

        version = conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
        print("alembic_version", version)
        if version != "20261030_teach_eval":
            print("ERROR expected alembic head 20261030_teach_eval")
            return 1

        fk_count = conn.execute(
            text(
                """
                SELECT COUNT(*) FROM information_schema.table_constraints
                WHERE constraint_schema = 'public' AND constraint_type = 'FOREIGN KEY'
                """
            )
        ).scalar()
        print("foreign_key_constraints", fk_count)

        idx_count = conn.execute(
            text(
                """
                SELECT COUNT(*) FROM pg_indexes
                WHERE schemaname = 'public' AND indexname NOT LIKE '%%_pkey'
                """
            )
        ).scalar()
        print("non_pkey_indexes", idx_count)

        chk_count = conn.execute(
            text(
                """
                SELECT COUNT(*) FROM information_schema.table_constraints
                WHERE constraint_schema = 'public' AND constraint_type = 'CHECK'
                """
            )
        ).scalar()
        print("check_constraints", chk_count)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
