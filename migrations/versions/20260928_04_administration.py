"""Add application-level users and durable administrative settings.

Revision ID: 20260928_04
Revises: 20260928_03
Create Date: 2026-09-28
"""

from alembic import op
import sqlalchemy as sa


revision = "20260928_04"
down_revision = "20260928_03"
branch_labels = None
depends_on = None


def upgrade() -> None:
    role = sa.Enum("ADMINISTRATOR", "RECRUITER", name="userrole")
    role.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "application_users",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("username", sa.String(255), nullable=False, unique=True),
        sa.Column("role", role, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_application_users_username", "application_users", ["username"])
    op.create_table(
        "application_settings",
        sa.Column("key", sa.String(120), primary_key=True),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )


def downgrade() -> None:
    op.drop_table("application_settings")
    op.drop_index("ix_application_users_username", table_name="application_users")
    op.drop_table("application_users")
    sa.Enum(name="userrole").drop(op.get_bind(), checkfirst=True)
