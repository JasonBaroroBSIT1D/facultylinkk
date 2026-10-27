"""Add document version chain columns."""

from alembic import op
import sqlalchemy as sa

revision = "20261027_document_versions"
down_revision = "20261028_email"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "documents",
        sa.Column("version_number", sa.Integer(), nullable=False, server_default="1"),
    )
    op.add_column(
        "documents",
        sa.Column("replaces_document_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_documents_replaces_document_id",
        "documents",
        "documents",
        ["replaces_document_id"],
        ["id"],
    )
    op.create_index("ix_documents_replaces_document_id", "documents", ["replaces_document_id"])


def downgrade():
    op.drop_index("ix_documents_replaces_document_id", table_name="documents")
    op.drop_constraint("fk_documents_replaces_document_id", "documents", type_="foreignkey")
    op.drop_column("documents", "replaces_document_id")
    op.drop_column("documents", "version_number")
