"""Linked SET/SEF teaching evaluation records per document (Phase 1 foundation)."""

from alembic import op
import sqlalchemy as sa

revision = "20261030_teach_eval"
down_revision = "20261029_eval_eligibility"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "document_teaching_evaluations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("public_id", sa.String(length=40), nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("evaluation_type", sa.String(length=8), nullable=False),
        sa.Column("indicator_id", sa.String(length=80), nullable=False),
        sa.Column("academic_year", sa.String(length=20), nullable=True),
        sa.Column("semester", sa.String(length=40), nullable=True),
        sa.Column("rating_raw", sa.String(length=120), nullable=True),
        sa.Column("rating_scale", sa.Float(), nullable=True),
        sa.Column("rating_percent", sa.Float(), nullable=True),
        sa.Column("extracted_metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("ocr_verification_status", sa.String(length=40), nullable=True),
        sa.Column("reviewer_validation_status", sa.String(length=40), nullable=True),
        sa.Column("reviewer_remarks", sa.Text(), nullable=True),
        sa.Column("correction_history_json", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("extraction_source", sa.String(length=40), nullable=False, server_default="ocr"),
        sa.Column("source_section_ref", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "evaluation_type IN ('SET', 'SEF')",
            name="ck_document_teaching_evaluations_type",
        ),
        sa.CheckConstraint(
            "(evaluation_type = 'SET' AND indicator_id = 'kra1-a-student') OR "
            "(evaluation_type = 'SEF' AND indicator_id = 'kra1-a-supervisor')",
            name="ck_document_teaching_evaluations_indicator",
        ),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_id", name="uq_document_teaching_evaluations_public_id"),
    )
    op.create_index(
        "ix_document_teaching_evaluations_document_id",
        "document_teaching_evaluations",
        ["document_id"],
        unique=False,
    )
    op.create_index(
        "ix_document_teaching_evaluations_evaluation_type",
        "document_teaching_evaluations",
        ["evaluation_type"],
        unique=False,
    )
    op.create_index(
        "ix_document_teaching_evaluations_indicator_id",
        "document_teaching_evaluations",
        ["indicator_id"],
        unique=False,
    )
    op.create_index(
        "uq_document_teaching_eval_period",
        "document_teaching_evaluations",
        ["document_id", "evaluation_type", "academic_year", "semester"],
        unique=True,
        postgresql_where=sa.text("academic_year IS NOT NULL AND semester IS NOT NULL"),
    )


def downgrade():
    op.drop_index("uq_document_teaching_eval_period", table_name="document_teaching_evaluations")
    op.drop_index("ix_document_teaching_evaluations_indicator_id", table_name="document_teaching_evaluations")
    op.drop_index("ix_document_teaching_evaluations_evaluation_type", table_name="document_teaching_evaluations")
    op.drop_index("ix_document_teaching_evaluations_document_id", table_name="document_teaching_evaluations")
    op.drop_table("document_teaching_evaluations")
