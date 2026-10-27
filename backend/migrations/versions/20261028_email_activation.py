"""Account activation tokens, auth epoch, rate limit events

Revision ID: 20261028_email
Revises: 20261027_auth
Create Date: 2026-10-27

"""

from alembic import op
import sqlalchemy as sa

revision = "20261028_email"
down_revision = "20261027_auth"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "users",
        sa.Column("auth_epoch", sa.Integer(), nullable=False, server_default="0"),
    )
    op.alter_column("users", "auth_epoch", server_default=None)

    op.create_table(
        "account_activation_tokens",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(length=255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_account_activation_tokens_user_id",
        "account_activation_tokens",
        ["user_id"],
    )

    op.create_table(
        "auth_rate_limit_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("bucket", sa.String(length=200), nullable=False),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_auth_rate_limit_events_bucket", "auth_rate_limit_events", ["bucket"])
    op.create_index("ix_auth_rate_limit_events_action", "auth_rate_limit_events", ["action"])


def downgrade():
    op.drop_index("ix_auth_rate_limit_events_action", table_name="auth_rate_limit_events")
    op.drop_index("ix_auth_rate_limit_events_bucket", table_name="auth_rate_limit_events")
    op.drop_table("auth_rate_limit_events")
    op.drop_index("ix_account_activation_tokens_user_id", table_name="account_activation_tokens")
    op.drop_table("account_activation_tokens")
    op.drop_column("users", "auth_epoch")
