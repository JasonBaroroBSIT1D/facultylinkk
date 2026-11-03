"""Phase C5: scoring configuration version binding (additive, non-destructive)."""

from alembic import op
import sqlalchemy as sa

revision = "20261103_scoring_version_lock"
down_revision = "20261030_teach_eval"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "documents",
        sa.Column("scoring_kra_configuration_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_documents_scoring_kra_configuration",
        "documents",
        "kra_configuration",
        ["scoring_kra_configuration_id"],
        ["id"],
    )
    op.create_index(
        "ix_documents_scoring_kra_configuration_id",
        "documents",
        ["scoring_kra_configuration_id"],
        unique=False,
    )

    op.add_column(
        "evaluation_periods",
        sa.Column("kra_configuration_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_evaluation_periods_kra_configuration",
        "evaluation_periods",
        "kra_configuration",
        ["kra_configuration_id"],
        ["id"],
    )
    op.create_index(
        "ix_evaluation_periods_kra_configuration_id",
        "evaluation_periods",
        ["kra_configuration_id"],
        unique=False,
    )


def downgrade():
    op.drop_index("ix_evaluation_periods_kra_configuration_id", table_name="evaluation_periods")
    op.drop_constraint("fk_evaluation_periods_kra_configuration", "evaluation_periods", type_="foreignkey")
    op.drop_column("evaluation_periods", "kra_configuration_id")

    op.drop_index("ix_documents_scoring_kra_configuration_id", table_name="documents")
    op.drop_constraint("fk_documents_scoring_kra_configuration", "documents", type_="foreignkey")
    op.drop_column("documents", "scoring_kra_configuration_id")
