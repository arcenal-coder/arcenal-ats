"""Add the recruiter workflow history and talent-pool stage.

Revision ID: 20260928_02
Revises: 20260925_01
Create Date: 2026-09-28
"""

from alembic import op
import sqlalchemy as sa


revision = "20260928_02"
down_revision = "20260925_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE pipelinestage ADD VALUE IF NOT EXISTS 'TALENT_POOL'")
    op.create_table(
        "application_notes",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "application_id",
            sa.Uuid(),
            sa.ForeignKey("applications.id"),
            nullable=False,
        ),
        sa.Column("author", sa.String(255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_application_notes_application_id",
        "application_notes",
        ["application_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_application_notes_application_id", "application_notes")
    op.drop_table("application_notes")
