"""Initial shared schema

Revision ID: 20260327_initial
Revises:
Create Date: 2026-03-27

"""

from alembic import op
import sqlalchemy as sa

revision = "20260327_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("public_id", sa.String(length=40), nullable=False),
        sa.Column("email", sa.String(length=180), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("full_name", sa.String(length=160), nullable=False),
        sa.Column("office", sa.String(length=200), nullable=True),
        sa.Column("contact", sa.String(length=80), nullable=True),
        sa.Column("specialization", sa.String(length=200), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("must_change_password", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_role", "users", ["role"])

    op.create_table(
        "kra_scoring_rules",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("kra_key", sa.String(length=40), nullable=False),
        sa.Column("label", sa.String(length=120), nullable=False),
        sa.Column("base_points", sa.Float(), nullable=True),
        sa.Column("max_points", sa.Float(), nullable=True),
        sa.Column("keywords", sa.JSON(), nullable=True),
        sa.Column("config_json", sa.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("kra_key"),
    )

    op.create_table(
        "kra_configuration",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("guideline_label", sa.String(length=200), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rank_weights", sa.JSON(), nullable=False),
        sa.Column("settings_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "evaluation_periods",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("public_id", sa.String(length=40), nullable=False),
        sa.Column("period_type", sa.String(length=40), nullable=False),
        sa.Column("label", sa.String(length=200), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("submission_open", sa.Date(), nullable=True),
        sa.Column("submission_close", sa.Date(), nullable=True),
        sa.Column("review_open", sa.Date(), nullable=True),
        sa.Column("review_close", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("timezone", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_id"),
    )

    op.create_table(
        "faculty_profiles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("public_id", sa.String(length=40), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("employee_no", sa.String(length=40), nullable=False),
        sa.Column("current_rank", sa.String(length=80), nullable=False),
        sa.Column("target_rank", sa.String(length=80), nullable=True),
        sa.Column("department", sa.String(length=160), nullable=False),
        sa.Column("college", sa.String(length=160), nullable=False),
        sa.Column("campus", sa.String(length=80), nullable=False),
        sa.Column("years_of_service", sa.Integer(), nullable=False),
        sa.Column("employment_status", sa.String(length=40), nullable=False),
        sa.Column("reviewer_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["reviewer_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("employee_no"),
        sa.UniqueConstraint("public_id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index("ix_faculty_profiles_reviewer_user_id", "faculty_profiles", ["reviewer_user_id"])

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("public_id", sa.String(length=40), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(length=200), nullable=False),
        sa.Column("target_id", sa.String(length=80), nullable=True),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_id"),
    )
    op.create_index("ix_audit_logs_actor_user_id", "audit_logs", ["actor_user_id"])

    op.create_table(
        "documents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("public_id", sa.String(length=40), nullable=False),
        sa.Column("faculty_profile_id", sa.Integer(), nullable=False),
        sa.Column("reviewer_user_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=True),
        sa.Column("mime_type", sa.String(length=120), nullable=True),
        sa.Column("file_size", sa.Integer(), nullable=True),
        sa.Column("file_hash", sa.String(length=64), nullable=True),
        sa.Column("kra_id", sa.String(length=40), nullable=True),
        sa.Column("criterion_id", sa.String(length=80), nullable=True),
        sa.Column("indicator_id", sa.String(length=80), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("extracted_info", sa.JSON(), nullable=False),
        sa.Column("extracted_text", sa.Text(), nullable=True),
        sa.Column("ocr_confidence", sa.Float(), nullable=True),
        sa.Column("ocr_status", sa.String(length=40), nullable=True),
        sa.Column("validation_result", sa.Text(), nullable=True),
        sa.Column("reviewer_remarks", sa.Text(), nullable=True),
        sa.Column("reviewer_score", sa.Float(), nullable=True),
        sa.Column("estimated_points", sa.Float(), nullable=True),
        sa.Column("verified_points", sa.Float(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["faculty_profile_id"], ["faculty_profiles.id"]),
        sa.ForeignKeyConstraint(["reviewer_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_id"),
    )
    op.create_index("ix_documents_faculty_profile_id", "documents", ["faculty_profile_id"])
    op.create_index("ix_documents_kra_id", "documents", ["kra_id"])
    op.create_index("ix_documents_reviewer_user_id", "documents", ["reviewer_user_id"])
    op.create_index("ix_documents_status", "documents", ["status"])

    op.create_table(
        "kra_scores",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("faculty_profile_id", sa.Integer(), nullable=False),
        sa.Column("kra_key", sa.String(length=40), nullable=False),
        sa.Column("estimated_points", sa.Float(), nullable=False),
        sa.Column("verified_points", sa.Float(), nullable=False),
        sa.Column("target_points", sa.Float(), nullable=True),
        sa.Column("document_count", sa.Integer(), nullable=False),
        sa.Column("status_label", sa.String(length=80), nullable=True),
        sa.Column("breakdown_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["faculty_profile_id"], ["faculty_profiles.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("faculty_profile_id", "kra_key", name="uq_kra_score_faculty_kra"),
    )

    op.create_table(
        "rank_simulations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("faculty_profile_id", sa.Integer(), nullable=False),
        sa.Column("current_rank", sa.String(length=80), nullable=False),
        sa.Column("target_rank", sa.String(length=80), nullable=False),
        sa.Column("estimated_total_points", sa.Float(), nullable=False),
        sa.Column("verified_total_points", sa.Float(), nullable=False),
        sa.Column("readiness_label", sa.String(length=120), nullable=True),
        sa.Column("missing_requirements", sa.Text(), nullable=True),
        sa.Column("snapshot_json", sa.JSON(), nullable=True),
        sa.Column("simulated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["faculty_profile_id"], ["faculty_profiles.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("faculty_profile_id"),
    )

    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("public_id", sa.String(length=40), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("read", sa.Boolean(), nullable=False),
        sa.Column("kind", sa.String(length=60), nullable=True),
        sa.Column("related_document_id", sa.String(length=40), nullable=True),
        sa.Column("related_faculty_id", sa.String(length=40), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_id"),
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])


def downgrade():
    op.drop_index("ix_notifications_user_id", table_name="notifications")
    op.drop_table("notifications")
    op.drop_table("rank_simulations")
    op.drop_table("kra_scores")
    op.drop_index("ix_documents_status", table_name="documents")
    op.drop_index("ix_documents_reviewer_user_id", table_name="documents")
    op.drop_index("ix_documents_kra_id", table_name="documents")
    op.drop_index("ix_documents_faculty_profile_id", table_name="documents")
    op.drop_table("documents")
    op.drop_index("ix_audit_logs_actor_user_id", table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_index("ix_faculty_profiles_reviewer_user_id", table_name="faculty_profiles")
    op.drop_table("faculty_profiles")
    op.drop_table("evaluation_periods")
    op.drop_table("kra_configuration")
    op.drop_table("kra_scoring_rules")
    op.drop_index("ix_users_role", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
