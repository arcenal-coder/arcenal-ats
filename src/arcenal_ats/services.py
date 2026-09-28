"""Application services keep state changes explicit and auditable."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from arcenal_ats.domain import JobStatus, PipelineStage, UserRole
from arcenal_ats.models import (
    Application,
    ApplicationNote,
    ApplicationSetting,
    ApplicationUser,
    AuditEvent,
    Candidate,
    Document,
    Job,
)
from arcenal_ats.schemas import JobCreate, JobUpdate, PublicApplicationCreate


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
    latest_note: str | None


@dataclass(frozen=True)
class CandidateDocumentOverview:
    document_id: UUID
    original_filename: str
    media_type: str
    byte_size: int


@dataclass(frozen=True)
class ApplicationHistoryItem:
    action: str
    actor: str
    previous_value: str | None
    new_value: str | None
    occurred_at: datetime


@dataclass(frozen=True)
class ApplicationDetail:
    overview: ApplicationOverview
    documents: tuple[CandidateDocumentOverview, ...]
    history: tuple[ApplicationHistoryItem, ...]


def application_user(session: Session, username: str) -> ApplicationUser:
    user = session.scalar(select(ApplicationUser).where(ApplicationUser.username == username))
    if user is not None:
        return user
    user = ApplicationUser(username=username, role=UserRole.RECRUITER)
    session.add(user)
    session.flush()
    return user


def update_application_user_role(
    session: Session,
    username: str,
    role: UserRole,
) -> ApplicationUser:
    user = application_user(session, username)
    user.role = role
    session.flush()
    return user


def application_settings(session: Session) -> dict[str, str]:
    return {item.key: item.value for item in session.scalars(select(ApplicationSetting))}


def set_application_setting(session: Session, key: str, value: str) -> ApplicationSetting:
    setting = session.get(ApplicationSetting, key)
    if setting is None:
        setting = ApplicationSetting(key=key, value=value)
        session.add(setting)
    else:
        setting.value = value
    session.flush()
    return setting


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


def update_job(session: Session, slug: str, payload: JobUpdate, actor: str) -> Job:
    job = find_internal_job(session, slug)
    job.title = payload.title
    job.location = payload.location
    job.contract_type = payload.contract_type
    job.summary = payload.summary
    job.description = payload.description
    session.flush()
    record_audit_event(session, actor, "job.updated", "job", job.id)
    return job


def archive_job(session: Session, slug: str, actor: str) -> Job:
    job = find_internal_job(session, slug)
    previous_status = job.status.value
    job.status = JobStatus.ARCHIVED
    session.flush()
    record_audit_event(
        session,
        actor,
        "job.archived",
        "job",
        job.id,
        previous_status,
        JobStatus.ARCHIVED.value,
    )
    return job


def find_internal_job(session: Session, slug: str) -> Job:
    job = session.scalar(select(Job).where(Job.slug == slug))
    if job is None:
        raise LookupError("Job not found.")
    return job


def internal_jobs(
    session: Session,
    query: str = "",
    include_archived: bool = False,
) -> list[Job]:
    statement = select(Job)
    if not include_archived:
        statement = statement.where(Job.status != JobStatus.ARCHIVED)
    normalized_query = query.strip()
    if normalized_query:
        pattern = f"%{normalized_query}%"
        statement = statement.where(Job.title.ilike(pattern) | Job.location.ilike(pattern))
    return list(session.scalars(statement.order_by(Job.created_at.desc())))


def move_application(
    session: Session,
    application_id: UUID,
    stage: PipelineStage,
    actor: str = "system",
) -> Application:
    application = session.get(Application, application_id)
    if application is None:
        raise LookupError("Application not found.")
    previous_stage = application.stage.value
    application.stage = stage
    session.flush()
    record_audit_event(
        session,
        actor,
        "application.stage_changed",
        "application",
        application.id,
        previous_stage,
        stage.value,
    )
    return application


def application_overviews(session: Session) -> list[ApplicationOverview]:
    statement = (
        select(Application, Candidate, Job)
        .join(Candidate, Application.candidate_id == Candidate.id)
        .outerjoin(Job, Application.job_id == Job.id)
        .order_by(Application.created_at.desc())
    )
    return [application_overview(session, *row) for row in session.execute(statement).all()]


def application_overview(
    session: Session,
    application: Application,
    candidate: Candidate,
    job: Job | None,
) -> ApplicationOverview:
    latest_note = session.scalar(
        select(ApplicationNote.content)
        .where(ApplicationNote.application_id == application.id)
        .order_by(ApplicationNote.created_at.desc())
        .limit(1)
    )
    return ApplicationOverview(
        application.id,
        f"{candidate.first_name} {candidate.last_name}",
        candidate.email,
        job.title if job else "Candidature spontanée",
        application.stage,
        application.cover_letter,
        latest_note,
    )


def application_detail(session: Session, application_id: UUID) -> ApplicationDetail:
    row = session.execute(
        select(Application, Candidate, Job)
        .join(Candidate, Application.candidate_id == Candidate.id)
        .outerjoin(Job, Application.job_id == Job.id)
        .where(Application.id == application_id)
    ).one_or_none()
    if row is None:
        raise LookupError("Application not found.")
    application, candidate, job = row
    return ApplicationDetail(
        application_overview(session, application, candidate, job),
        candidate_documents(session, candidate.id),
        application_history(session, application.id),
    )


def candidate_documents(
    session: Session,
    candidate_id: UUID,
) -> tuple[CandidateDocumentOverview, ...]:
    statement = (
        select(Document)
        .where(Document.candidate_id == candidate_id)
        .order_by(Document.created_at.desc())
    )
    return tuple(
        CandidateDocumentOverview(
            document.id,
            document.original_filename,
            document.media_type,
            document.byte_size,
        )
        for document in session.scalars(statement)
    )


def application_history(
    session: Session,
    application_id: UUID,
) -> tuple[ApplicationHistoryItem, ...]:
    statement = (
        select(AuditEvent)
        .where(AuditEvent.subject_type == "application", AuditEvent.subject_id == application_id)
        .order_by(AuditEvent.occurred_at.desc())
    )
    return tuple(
        ApplicationHistoryItem(
            event.action,
            event.actor,
            event.previous_value,
            event.new_value,
            event.occurred_at,
        )
        for event in session.scalars(statement)
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
    previous_value: str | None = None,
    new_value: str | None = None,
) -> None:
    session.add(
        AuditEvent(
            actor=actor,
            action=action,
            subject_type=subject_type,
            subject_id=subject_id,
            previous_value=previous_value,
            new_value=new_value,
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


def private_document(session: Session, document_id: UUID) -> Document:
    document = session.get(Document, document_id)
    if document is None:
        raise LookupError("Document not found.")
    return document
