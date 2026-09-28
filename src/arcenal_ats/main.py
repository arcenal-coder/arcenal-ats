"""FastAPI entry point for public and YunoHost-protected interfaces."""

from __future__ import annotations

from collections.abc import Generator
from dataclasses import dataclass
from urllib.parse import urlparse
from uuid import UUID

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from pydantic import ValidationError
from sqlalchemy.orm import Session, sessionmaker

from arcenal_ats.config import default_settings
from arcenal_ats.database import create_session_factory, session_scope
from arcenal_ats.domain import DEFAULT_UPLOAD_POLICY, DomainValidationError, PipelineStage
from arcenal_ats.presentation import (
    internal_applications_page as render_internal_applications_page,
    internal_candidate_page as render_internal_candidate_page,
    internal_dashboard_page as render_internal_dashboard_page,
    internal_jobs_page as render_internal_jobs_page,
    internal_talent_pool_page as render_internal_talent_pool_page,
    careers_page as render_careers_page,
    application_confirmation_page as render_application_confirmation_page,
    job_page as render_job_page,
    privacy_page as render_privacy_page,
    spontaneous_application_page as render_spontaneous_application_page,
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
    add_application_note,
    application_detail,
    application_candidate_id,
    application_overviews,
    create_draft_job,
    internal_jobs,
    move_application,
    publish_job,
    private_document,
    published_jobs,
    published_job,
    record_audit_event,
    register_document,
    search_talent_pool,
    talent_pool_candidates,
)
from arcenal_ats.storage import PrivateDocumentStore


@dataclass(frozen=True)
class CareersApplicationForm:
    first_name: str
    last_name: str
    email: str
    location: str
    cover_letter: str
    consent: bool
    resume: UploadFile


def create_app(factory: sessionmaker[Session] | None = None) -> FastAPI:
    app = FastAPI(title="ARCenal ATS", version="0.1.0")
    settings = default_settings()
    app.state.session_factory = factory or create_session_factory(settings)
    app.state.document_store = PrivateDocumentStore(
        settings.document_directory,
        DEFAULT_UPLOAD_POLICY,
    )
    app.state.public_base_path = urlparse(settings.public_base_url).path.rstrip("/")
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
    def careers_page(request: Request, session: Session = Depends(get_session)) -> str:
        jobs = published_jobs(session)
        job_cards = [(job.slug, job.title, job.location) for job in jobs]
        return render_careers_page(job_cards, request.app.state.public_base_path)

    @app.get("/recrutement/offres/{job_slug}", response_class=HTMLResponse, tags=["public"])
    def job_page(
        job_slug: str,
        request: Request,
        session: Session = Depends(get_session),
    ) -> str:
        try:
            job = published_job(session, job_slug)
        except LookupError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error
        return render_job_page(
            job.slug,
            job.title,
            job.location,
            job.description,
            request.app.state.public_base_path,
        )

    @app.get(
        "/recrutement/candidature-spontanee",
        response_class=HTMLResponse,
        tags=["public"],
    )
    def spontaneous_application_page(request: Request) -> str:
        return render_spontaneous_application_page(request.app.state.public_base_path)

    @app.get(
        "/recrutement/candidature-envoyee",
        response_class=HTMLResponse,
        tags=["public"],
    )
    def application_confirmation_page(request: Request) -> str:
        return render_application_confirmation_page(request.app.state.public_base_path)

    @app.get(
        "/recrutement/confidentialite",
        response_class=HTMLResponse,
        tags=["public"],
    )
    def privacy_page(request: Request) -> str:
        return render_privacy_page(request.app.state.public_base_path)

    @app.get("/interne", response_class=HTMLResponse, tags=["internal"])
    def internal_dashboard(
        request: Request,
        _: str = Depends(require_yunohost_user),
        session: Session = Depends(get_session),
    ) -> str:
        return render_internal_dashboard_page(
            len(internal_jobs(session)),
            len(application_overviews(session)),
            len(talent_pool_candidates(session)),
            request.app.state.public_base_path,
        )

    @app.get("/interne/offres", response_class=HTMLResponse, tags=["internal"])
    def internal_jobs_page(
        request: Request,
        _: str = Depends(require_yunohost_user),
        session: Session = Depends(get_session),
    ) -> str:
        jobs = internal_jobs(session)
        values = [(job.slug, job.title, job.location, job.status.value) for job in jobs]
        return render_internal_jobs_page(values, request.app.state.public_base_path)

    @app.post("/interne/offres", tags=["internal"])
    def create_internal_job(
        request: Request,
        user: str = Depends(require_yunohost_user),
        slug: str = Form(...),
        title: str = Form(...),
        location: str = Form(...),
        contract_type: str = Form(...),
        summary: str = Form(...),
        description: str = Form(...),
        session: Session = Depends(get_session),
    ) -> RedirectResponse:
        payload = internal_job_payload(slug, title, location, contract_type, summary, description)
        job = create_draft_job(session, payload)
        record_internal_job_creation(session, job.id, user)
        return internal_redirect(request, "/interne/offres")

    @app.post("/interne/offres/{job_slug}/publier", tags=["internal"])
    def publish_internal_job(
        job_slug: str,
        request: Request,
        user: str = Depends(require_yunohost_user),
        session: Session = Depends(get_session),
    ) -> RedirectResponse:
        publish_job(session, job_slug, user)
        return internal_redirect(request, "/interne/offres")

    @app.get("/interne/candidatures", response_class=HTMLResponse, tags=["internal"])
    def internal_applications_page(
        request: Request,
        _: str = Depends(require_yunohost_user),
        session: Session = Depends(get_session),
    ) -> str:
        overviews = application_overviews(session)
        values = [
            (
                str(item.application_id),
                item.candidate_name,
                item.candidate_email,
                item.job_title,
                item.stage.value,
                item.cover_letter,
                item.latest_note,
            )
            for item in overviews
        ]
        return render_internal_applications_page(values, request.app.state.public_base_path)

    @app.post("/interne/candidatures/{application_id}/pipeline", tags=["internal"])
    def update_internal_pipeline(
        application_id: UUID,
        request: Request,
        user: str = Depends(require_yunohost_user),
        stage: str = Form(...),
        note: str = Form(""),
        session: Session = Depends(get_session),
    ) -> RedirectResponse:
        try:
            move_application(session, application_id, PipelineStage(stage), user)
            add_optional_note(session, application_id, note, user)
        except (LookupError, ValueError) as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        return internal_redirect(request, "/interne/candidatures")

    @app.get(
        "/interne/candidatures/{application_id}",
        response_class=HTMLResponse,
        tags=["internal"],
    )
    def internal_candidate_page(
        application_id: UUID,
        request: Request,
        _: str = Depends(require_yunohost_user),
        session: Session = Depends(get_session),
    ) -> str:
        try:
            detail = application_detail(session, application_id)
        except LookupError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error
        overview = detail.overview
        application = (
            str(overview.application_id),
            overview.candidate_name,
            overview.candidate_email,
            overview.job_title,
            overview.stage.value,
            overview.cover_letter,
            overview.latest_note,
        )
        documents = [
            (str(item.document_id), item.original_filename, item.media_type, item.byte_size)
            for item in detail.documents
        ]
        history = [
            (
                item.action,
                item.actor,
                item.previous_value,
                item.new_value,
                item.occurred_at.isoformat(),
            )
            for item in detail.history
        ]
        return render_internal_candidate_page(
            application,
            documents,
            history,
            request.app.state.public_base_path,
        )

    @app.get("/interne/vivier", response_class=HTMLResponse, tags=["internal"])
    def internal_talent_pool_page(
        request: Request,
        _: str = Depends(require_yunohost_user),
        session: Session = Depends(get_session),
    ) -> str:
        candidates = talent_pool_candidates(session)
        values = [
            (f"{item.first_name} {item.last_name}", item.email, item.location or "—")
            for item in candidates
        ]
        return render_internal_talent_pool_page(values, request.app.state.public_base_path)

    @app.get("/api/v1/internal/documents/{document_id}", tags=["internal"])
    def download_private_document(
        document_id: UUID,
        request: Request,
        _: str = Depends(require_yunohost_user),
        session: Session = Depends(get_session),
    ) -> Response:
        try:
            document = private_document(session, document_id)
            store: PrivateDocumentStore = request.app.state.document_store
            content = store.load(document.storage_key)
        except (DomainValidationError, LookupError) as error:
            raise HTTPException(status_code=404, detail=str(error)) from error
        headers = {
            "Content-Disposition": f'attachment; filename="{document.original_filename}"',
            "Cache-Control": "private, no-store",
        }
        return Response(content=content, media_type=document.media_type, headers=headers)

    @app.post("/recrutement/offres/{job_slug}/candidater", tags=["public"])
    async def submit_job_application(
        job_slug: str,
        request: Request,
        form: CareersApplicationForm = Depends(careers_application_form),
        session: Session = Depends(get_session),
    ) -> RedirectResponse:
        return await submit_careers_application(request, session, job_slug, form)

    @app.post("/recrutement/candidature-spontanee", tags=["public"])
    async def submit_spontaneous_application(
        request: Request,
        form: CareersApplicationForm = Depends(careers_application_form),
        session: Session = Depends(get_session),
    ) -> RedirectResponse:
        return await submit_careers_application(request, session, None, form)

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


def public_application_payload(
    first_name: str,
    last_name: str,
    email: str,
    location: str,
    cover_letter: str,
    consent: bool,
) -> PublicApplicationCreate:
    try:
        return PublicApplicationCreate(
            first_name=first_name,
            last_name=last_name,
            email=email,
            location=location or None,
            cover_letter=cover_letter or None,
            consent=consent,
        )
    except ValidationError as error:
        raise HTTPException(status_code=422, detail=error.errors()) from error


def internal_job_payload(
    slug: str,
    title: str,
    location: str,
    contract_type: str,
    summary: str,
    description: str,
) -> JobCreate:
    try:
        return JobCreate(
            slug=slug,
            title=title,
            location=location,
            contract_type=contract_type,
            summary=summary,
            description=description,
        )
    except ValidationError as error:
        raise HTTPException(status_code=422, detail=error.errors()) from error


def record_internal_job_creation(session: Session, job_id: UUID, actor: str) -> None:
    record_audit_event(session, actor, "job.created", "job", job_id)


def add_optional_note(session: Session, application_id: UUID, note: str, actor: str) -> None:
    if note.strip():
        add_application_note(session, application_id, note, actor)


def internal_redirect(request: Request, path: str) -> RedirectResponse:
    base_path: str = request.app.state.public_base_path
    return RedirectResponse(f"{base_path}{path}", status_code=303)


def careers_application_form(
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
    location: str = Form(""),
    cover_letter: str = Form(""),
    consent: bool = Form(...),
    resume: UploadFile = File(...),
) -> CareersApplicationForm:
    return CareersApplicationForm(
        first_name,
        last_name,
        email,
        location,
        cover_letter,
        consent,
        resume,
    )


async def submit_careers_application(
    request: Request,
    session: Session,
    job_slug: str | None,
    form: CareersApplicationForm,
) -> RedirectResponse:
    payload = public_application_payload(
        form.first_name,
        form.last_name,
        form.email,
        form.location,
        form.cover_letter,
        form.consent,
    )
    accepted = submit_public_application(session, payload, job_slug)
    content = await form.resume.read()
    save_document(request, session, accepted.application_id, form.resume, content)
    base_path: str = request.app.state.public_base_path
    return RedirectResponse(f"{base_path}/recrutement/candidature-envoyee", status_code=303)


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
  const source = new URL(script.src);
  const publicScriptPath = '/public/arcenal-jobs.js';
  const installationPath = source.pathname.slice(0, -publicScriptPath.length);
  const base = `${source.origin}${installationPath}`;
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
