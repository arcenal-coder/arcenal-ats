"""FastAPI entry point for public and YunoHost-protected interfaces."""

from __future__ import annotations

from collections.abc import Generator
from uuid import UUID

from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, Response
from sqlalchemy.orm import Session, sessionmaker

from arcenal_ats.config import default_settings
from arcenal_ats.database import create_session_factory, session_scope
from arcenal_ats.domain import DEFAULT_UPLOAD_POLICY, DomainValidationError, PipelineStage
from arcenal_ats.presentation import (
    careers_page as render_careers_page,
    job_page as render_job_page,
    stylesheet,
)
from arcenal_ats.schemas import (
    AacpCapability,
    ApplicationAccepted,
    DocumentAccepted,
    InternalCandidate,
    JobCreate,
    PipelineMove,
    PublicApplicationCreate,
    PublicJob,
)
from arcenal_ats.services import (
    PublicApplicationService,
    application_candidate_id,
    create_draft_job,
    move_application,
    published_jobs,
    published_job,
    register_document,
    search_talent_pool,
)
from arcenal_ats.storage import PrivateDocumentStore


def create_app(factory: sessionmaker[Session] | None = None) -> FastAPI:
    app = FastAPI(title="ARCenal ATS", version="0.1.0")
    settings = default_settings()
    app.state.session_factory = factory or create_session_factory(settings)
    app.state.document_store = PrivateDocumentStore(
        settings.document_directory,
        DEFAULT_UPLOAD_POLICY,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.allowed_widget_origins),
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )
    register_routes(app)
    return app


def get_session(request: Request) -> Generator[Session, None, None]:
    factory: sessionmaker[Session] = request.app.state.session_factory
    yield from session_scope(factory)


def require_yunohost_user(request: Request) -> str:
    user = request.headers.get("remote-user")
    if not user:
        raise HTTPException(status_code=401, detail="YunoHost authentication required.")
    return user


def register_routes(app: FastAPI) -> None:
    @app.get("/healthz", tags=["system"])
    def health_check() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/recrutement", response_class=HTMLResponse, tags=["public"])
    def careers_page(session: Session = Depends(get_session)) -> str:
        jobs = published_jobs(session)
        job_cards = [(job.slug, job.title, job.location) for job in jobs]
        return render_careers_page(job_cards)

    @app.get("/recrutement/offres/{job_slug}", response_class=HTMLResponse, tags=["public"])
    def job_page(job_slug: str, session: Session = Depends(get_session)) -> str:
        try:
            job = published_job(session, job_slug)
        except LookupError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error
        return render_job_page(job.title, job.location, job.description)

    @app.get("/public/arcenal-ats.css", tags=["public"])
    def public_stylesheet() -> Response:
        return Response(content=stylesheet(), media_type="text/css")

    @app.get("/public/arcenal-jobs.js", tags=["public"])
    def jobs_widget() -> Response:
        return Response(content=widget_script(), media_type="application/javascript")

    @app.get("/public-api/v1/jobs", response_model=list[PublicJob], tags=["public-api"])
    def list_public_jobs(session: Session = Depends(get_session)) -> list[PublicJob]:
        return [
            PublicJob.model_validate(job, from_attributes=True)
            for job in published_jobs(session)
        ]

    @app.get("/public-api/v1/jobs/{job_slug}", response_model=PublicJob, tags=["public-api"])
    def get_public_job(job_slug: str, session: Session = Depends(get_session)) -> PublicJob:
        try:
            job = published_job(session, job_slug)
        except LookupError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error
        return PublicJob.model_validate(job, from_attributes=True)

    @app.post(
        "/public-api/v1/jobs/{job_slug}/applications",
        response_model=ApplicationAccepted,
        status_code=201,
        tags=["public-api"],
    )
    def apply_to_job(
        job_slug: str,
        payload: PublicApplicationCreate,
        session: Session = Depends(get_session),
    ) -> ApplicationAccepted:
        return submit_public_application(session, payload, job_slug)

    @app.post(
        "/public-api/v1/spontaneous-applications",
        response_model=ApplicationAccepted,
        status_code=201,
        tags=["public-api"],
    )
    def apply_spontaneously(
        payload: PublicApplicationCreate,
        session: Session = Depends(get_session),
    ) -> ApplicationAccepted:
        return submit_public_application(session, payload, None)

    @app.post(
        "/public-api/v1/applications/{application_id}/documents",
        response_model=DocumentAccepted,
        status_code=201,
        tags=["public-api"],
    )
    async def upload_application_document(
        application_id: UUID,
        request: Request,
        document: UploadFile = File(...),
        session: Session = Depends(get_session),
    ) -> DocumentAccepted:
        content = await document.read()
        return save_document(request, session, application_id, document, content)

    @app.post(
        "/api/v1/internal/jobs",
        response_model=PublicJob,
        status_code=201,
        tags=["internal"],
    )
    def create_job(
        payload: JobCreate,
        _: str = Depends(require_yunohost_user),
        session: Session = Depends(get_session),
    ) -> PublicJob:
        job = create_draft_job(session, payload)
        return PublicJob.model_validate(job, from_attributes=True)

    @app.get(
        "/api/v1/internal/talent-pool",
        response_model=list[InternalCandidate],
        tags=["internal"],
    )
    def search_candidates(
        query: str,
        _: str = Depends(require_yunohost_user),
        session: Session = Depends(get_session),
    ) -> list[InternalCandidate]:
        candidates = search_talent_pool(session, query)
        return [
            InternalCandidate.model_validate(candidate, from_attributes=True)
            for candidate in candidates
        ]

    @app.patch(
        "/api/v1/internal/applications/{application_id}/stage",
        tags=["internal"],
    )
    def update_pipeline_stage(
        application_id: str,
        payload: PipelineMove,
        _: str = Depends(require_yunohost_user),
        session: Session = Depends(get_session),
    ) -> dict[str, str]:
        try:
            application = move_application(
                session,
                UUID(application_id),
                PipelineStage(payload.stage),
            )
        except (LookupError, ValueError) as error:
            raise HTTPException(status_code=404, detail=str(error)) from error
        return {"application_id": str(application.id), "stage": application.stage.value}

    @app.get(
        "/aacp/1/capabilities",
        response_model=list[AacpCapability],
        tags=["aacp"],
    )
    def aacp_capabilities(
        _: str = Depends(require_yunohost_user),
    ) -> list[AacpCapability]:
        return [
            AacpCapability(
                name="candidate.search",
                description="Search the talent pool through a constrained business API.",
                requires_human_confirmation=False,
            ),
            AacpCapability(
                name="candidate.update",
                description=(
                    "Prepare a candidate update; human confirmation is required before mutation."
                ),
                requires_human_confirmation=True,
            ),
            AacpCapability(
                name="job.list",
                description="List ATS jobs available to the permitted agent.",
                requires_human_confirmation=False,
            ),
        ]


def submit_public_application(
    session: Session,
    payload: PublicApplicationCreate,
    job_slug: str | None,
) -> ApplicationAccepted:
    try:
        application = PublicApplicationService(session).submit(payload, job_slug)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except PermissionError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return ApplicationAccepted(application_id=application.id, message="Application received.")


def save_document(
    request: Request,
    session: Session,
    application_id: UUID,
    document: UploadFile,
    content: bytes,
) -> DocumentAccepted:
    if document.filename is None or document.content_type is None:
        raise HTTPException(
            status_code=422,
            detail="A named document with a media type is required.",
        )
    try:
        store: PrivateDocumentStore = request.app.state.document_store
        candidate_id = application_candidate_id(session, application_id)
        storage_key = store.save(candidate_id, document.filename, document.content_type, content)
        saved = register_document(
            session,
            application_id,
            document.filename,
            storage_key,
            document.content_type,
            len(content),
        )
    except (DomainValidationError, LookupError) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return DocumentAccepted(document_id=saved.id, message="Document received.")


def widget_script() -> str:
    return """(() => {
  const script = document.currentScript;
  const target = document.querySelector(script.dataset.target || '#arcenal-jobs');
  if (!target) return;
  const base = new URL(script.src).origin;
  fetch(`${base}/public-api/v1/jobs`).then(response => response.json()).then(jobs => {
    jobs.forEach(job => {
      const link = document.createElement('a');
      link.href = `${base}/recrutement/offres/${encodeURIComponent(job.slug)}`;
      link.textContent = `${job.title} — ${job.location}`;
      target.append(document.createElement('p')).append(link);
    });
  });
})();"""


app = create_app()
