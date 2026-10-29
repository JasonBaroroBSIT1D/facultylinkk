"""document OCR job queue

Revision ID: 20261028_document_ocr_jobs
Revises: 20261028_email_activation
Create Date: 2026-10-28
"""

from alembic import op
import sqlalchemy as sa


revision = "20261028_document_ocr_jobs"
down_revision = "20261027_document_versions"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "document_ocr_jobs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("file_hash", sa.String(length=64), nullable=False),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("locked_by", sa.String(length=64), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_document_ocr_jobs_document_id", "document_ocr_jobs", ["document_id"])
    op.create_index("ix_document_ocr_jobs_status", "document_ocr_jobs", ["status"])


def downgrade():
    op.drop_index("ix_document_ocr_jobs_status", table_name="document_ocr_jobs")
    op.drop_index("ix_document_ocr_jobs_document_id", table_name="document_ocr_jobs")
    op.drop_table("document_ocr_jobs")
