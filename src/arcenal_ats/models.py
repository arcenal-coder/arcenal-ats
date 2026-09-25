"""SQLAlchemy tables. Documents store metadata only; bytes never live in the web root."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from arcenal_ats.database import Base
from arcenal_ats.domain import JobStatus, PipelineStage


class TimestampedEntity:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class Job(TimestampedEntity, Base):
    __tablename__ = "jobs"
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    slug: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(200))
    location: Mapped[str] = mapped_column(String(200))
    contract_type: Mapped[str] = mapped_column(String(100))
    summary: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[JobStatus] = mapped_column(Enum(JobStatus), default=JobStatus.DRAFT)


class Candidate(TimestampedEntity, Base):
    __tablename__ = "candidates"
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    location: Mapped[str | None] = mapped_column(String(200), nullable=True)
    skills: Mapped[str | None] = mapped_column(Text, nullable=True)


class Application(TimestampedEntity, Base):
    __tablename__ = "applications"
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    candidate_id: Mapped[UUID] = mapped_column(ForeignKey("candidates.id"), index=True)
    job_id: Mapped[UUID | None] = mapped_column(ForeignKey("jobs.id"), nullable=True, index=True)
    stage: Mapped[PipelineStage] = mapped_column(Enum(PipelineStage), default=PipelineStage.NEW)
    cover_letter: Mapped[str | None] = mapped_column(Text, nullable=True)
    consent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Document(TimestampedEntity, Base):
    __tablename__ = "documents"
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    candidate_id: Mapped[UUID] = mapped_column(ForeignKey("candidates.id"), index=True)
    original_filename: Mapped[str] = mapped_column(String(255))
    storage_key: Mapped[str] = mapped_column(String(255), unique=True)
    media_type: Mapped[str] = mapped_column(String(100))
    byte_size: Mapped[int] = mapped_column()


class AuditEvent(Base):
    __tablename__ = "audit_events"
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    actor: Mapped[str] = mapped_column(String(255))
    action: Mapped[str] = mapped_column(String(100))
    subject_type: Mapped[str] = mapped_column(String(100))
    subject_id: Mapped[UUID] = mapped_column(Uuid)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
