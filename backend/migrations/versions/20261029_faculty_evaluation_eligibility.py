"""Faculty Section 10 evaluation eligibility (reviewer-verified, auditable)."""

from alembic import op
import sqlalchemy as sa

revision = "20261029_eval_eligibility"
down_revision = "20261028_document_ocr_jobs"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "faculty_profiles",
        sa.Column("evaluation_eligibility_json", sa.JSON(), nullable=True),
    )


def downgrade():
    op.drop_column("faculty_profiles", "evaluation_eligibility_json")
