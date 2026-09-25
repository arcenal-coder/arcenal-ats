"""Application services keep state changes explicit and auditable."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from arcenal_ats.domain import JobStatus, PipelineStage
from arcenal_ats.models import Application, Candidate, Document, Job
from arcenal_ats.schemas import JobCreate, PublicApplicationCreate


class PublicApplicationService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def submit(self, payload: PublicApplicationCreate, job_slug: str | None) -> Application:
        self._require_consent(payload.consent)
        job = self._get_published_job(job_slug) if job_slug else None
        candidate = self._get_or_create_candidate(payload)
        application = Application(
            candidate_id=candidate.id,
            job_id=job.id if job else None,
            cover_letter=payload.cover_letter,
            consent_at=datetime.now(UTC),
        )
        self._session.add(application)
        self._session.flush()
        return application

    def _get_published_job(self, job_slug: str) -> Job:
        job = self._session.scalar(
            select(Job).where(Job.slug == job_slug, Job.status == JobStatus.PUBLISHED)
        )
        if job is None:
            raise LookupError("Published job not found.")
        return job

    def _get_or_create_candidate(self, payload: PublicApplicationCreate) -> Candidate:
        candidate = self._session.scalar(
            select(Candidate).where(Candidate.email == str(payload.email))
        )
        if candidate is not None:
            return candidate
        candidate = Candidate(
            email=str(payload.email),
            first_name=payload.first_name,
            last_name=payload.last_name,
            location=payload.location,
        )
        self._session.add(candidate)
        self._session.flush()
        return candidate

    def _require_consent(self, consent: bool) -> None:
        if consent is False:
            raise PermissionError("Explicit privacy consent is required.")


def published_jobs(session: Session) -> list[Job]:
    statement = select(Job).where(Job.status == JobStatus.PUBLISHED).order_by(
        Job.created_at.desc()
    )
    return list(session.scalars(statement))


def published_job(session: Session, slug: str) -> Job:
    job = session.scalar(select(Job).where(Job.slug == slug, Job.status == JobStatus.PUBLISHED))
    if job is None:
        raise LookupError("Published job not found.")
    return job


def find_candidate(session: Session, candidate_id: UUID) -> Candidate:
    candidate = session.get(Candidate, candidate_id)
    if candidate is None:
        raise LookupError("Candidate not found.")
    return candidate


def create_draft_job(session: Session, payload: JobCreate) -> Job:
    job = Job(**payload.model_dump(), status=JobStatus.DRAFT)
    session.add(job)
    session.flush()
    return job


def move_application(
    session: Session,
    application_id: UUID,
    stage: PipelineStage,
) -> Application:
    application = session.get(Application, application_id)
    if application is None:
        raise LookupError("Application not found.")
    application.stage = stage
    session.flush()
    return application


def search_talent_pool(session: Session, query: str) -> list[Candidate]:
    text = f"%{query.strip()}%"
    statement = select(Candidate).where(
        Candidate.skills.ilike(text) | Candidate.location.ilike(text)
    )
    return list(session.scalars(statement))


def register_document(
    session: Session,
    application_id: UUID,
    filename: str,
    storage_key: str,
    media_type: str,
    byte_size: int,
) -> Document:
    application = session.get(Application, application_id)
    if application is None:
        raise LookupError("Application not found.")
    document = Document(
        candidate_id=application.candidate_id,
        original_filename=filename,
        storage_key=storage_key,
        media_type=media_type,
        byte_size=byte_size,
    )
    session.add(document)
    session.flush()
    return document


def application_candidate_id(session: Session, application_id: UUID) -> UUID:
    application = session.get(Application, application_id)
    if application is None:
        raise LookupError("Application not found.")
    return application.candidate_id
