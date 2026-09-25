# ruff: noqa: E501
"""Initial ATS schema.

Revision ID: 20260925_01
Revises:
Create Date: 2026-09-25
"""

from alembic import op
import sqlalchemy as sa


revision = "20260925_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    job_status = sa.Enum("DRAFT", "PUBLISHED", "CLOSED", "ARCHIVED", name="jobstatus")
    pipeline_stage = sa.Enum("NEW", "QUALIFYING", "INTERVIEW", "OFFER", "HIRED", "REJECTED", name="pipelinestage")
    op.create_table("jobs", sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("slug", sa.String(160), nullable=False, unique=True), sa.Column("title", sa.String(200), nullable=False), sa.Column("location", sa.String(200), nullable=False), sa.Column("contract_type", sa.String(100), nullable=False), sa.Column("summary", sa.Text(), nullable=False), sa.Column("description", sa.Text(), nullable=False), sa.Column("status", job_status, nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False))
    op.create_index("ix_jobs_slug", "jobs", ["slug"])
    op.create_table("candidates", sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("email", sa.String(320), nullable=False, unique=True), sa.Column("first_name", sa.String(100), nullable=False), sa.Column("last_name", sa.String(100), nullable=False), sa.Column("location", sa.String(200)), sa.Column("skills", sa.Text()), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False))
    op.create_index("ix_candidates_email", "candidates", ["email"])
    op.create_table("applications", sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("candidate_id", sa.Uuid(), sa.ForeignKey("candidates.id"), nullable=False), sa.Column("job_id", sa.Uuid(), sa.ForeignKey("jobs.id")), sa.Column("stage", pipeline_stage, nullable=False), sa.Column("cover_letter", sa.Text()), sa.Column("consent_at", sa.DateTime(timezone=True), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False))
    op.create_table("documents", sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("candidate_id", sa.Uuid(), sa.ForeignKey("candidates.id"), nullable=False), sa.Column("original_filename", sa.String(255), nullable=False), sa.Column("storage_key", sa.String(255), nullable=False, unique=True), sa.Column("media_type", sa.String(100), nullable=False), sa.Column("byte_size", sa.Integer(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False))
    op.create_table("audit_events", sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("actor", sa.String(255), nullable=False), sa.Column("action", sa.String(100), nullable=False), sa.Column("subject_type", sa.String(100), nullable=False), sa.Column("subject_id", sa.Uuid(), nullable=False), sa.Column("occurred_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False))


def downgrade() -> None:
    op.drop_table("audit_events")
    op.drop_table("documents")
    op.drop_table("applications")
    op.drop_table("candidates")
    op.drop_table("jobs")
    op.execute("DROP TYPE IF EXISTS pipelinestage")
    op.execute("DROP TYPE IF EXISTS jobstatus")
