"""Application services keep state changes explicit and auditable."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from arcenal_ats.domain import JobStatus, PipelineStage
from arcenal_ats.models import Application, ApplicationNote, AuditEvent, Candidate, Document, Job
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


@dataclass(frozen=True)
class ApplicationOverview:
    application_id: UUID
    candidate_name: str
    candidate_email: str
    job_title: str
    stage: PipelineStage
    cover_letter: str | None


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


def publish_job(session: Session, slug: str, actor: str) -> Job:
    job = session.scalar(select(Job).where(Job.slug == slug))
    if job is None:
        raise LookupError("Job not found.")
    job.status = JobStatus.PUBLISHED
    session.flush()
    record_audit_event(session, actor, "job.published", "job", job.id)
    return job


def internal_jobs(session: Session) -> list[Job]:
    return list(session.scalars(select(Job).order_by(Job.created_at.desc())))


def move_application(
    session: Session,
    application_id: UUID,
    stage: PipelineStage,
    actor: str = "system",
) -> Application:
    application = session.get(Application, application_id)
    if application is None:
        raise LookupError("Application not found.")
    application.stage = stage
    session.flush()
    record_audit_event(session, actor, "application.stage_changed", "application", application.id)
    return application


def application_overviews(session: Session) -> list[ApplicationOverview]:
    statement = (
        select(Application, Candidate, Job)
        .join(Candidate, Application.candidate_id == Candidate.id)
        .outerjoin(Job, Application.job_id == Job.id)
        .order_by(Application.created_at.desc())
    )
    return [application_overview(*row) for row in session.execute(statement).all()]


def application_overview(
    application: Application,
    candidate: Candidate,
    job: Job | None,
) -> ApplicationOverview:
    return ApplicationOverview(
        application.id,
        f"{candidate.first_name} {candidate.last_name}",
        candidate.email,
        job.title if job else "Candidature spontanée",
        application.stage,
        application.cover_letter,
    )


def add_application_note(
    session: Session,
    application_id: UUID,
    content: str,
    author: str,
) -> ApplicationNote:
    if session.get(Application, application_id) is None:
        raise LookupError("Application not found.")
    normalized_content = content.strip()
    if not normalized_content:
        raise ValueError("A note cannot be empty.")
    note = ApplicationNote(application_id=application_id, author=author, content=normalized_content)
    session.add(note)
    session.flush()
    record_audit_event(session, author, "application.note_added", "application", application_id)
    return note


def record_audit_event(
    session: Session,
    actor: str,
    action: str,
    subject_type: str,
    subject_id: UUID,
) -> None:
    session.add(
        AuditEvent(
            actor=actor,
            action=action,
            subject_type=subject_type,
            subject_id=subject_id,
        )
    )


def search_talent_pool(session: Session, query: str) -> list[Candidate]:
    text = f"%{query.strip()}%"
    statement = select(Candidate).where(
        Candidate.skills.ilike(text) | Candidate.location.ilike(text)
    )
    return list(session.scalars(statement))


def talent_pool_candidates(session: Session) -> list[Candidate]:
    return list(session.scalars(select(Candidate).order_by(Candidate.created_at.desc())))


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
