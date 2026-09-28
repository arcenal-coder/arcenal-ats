# ruff: noqa: E501
"""Server-rendered pages using ARCenal Agent's dark Hermes visual language."""

from __future__ import annotations

from html import escape
from urllib.parse import quote


AGENT_THEME_CSS = """
:root { --arc-bg: #101014; --arc-surface: #1a1a2e; --arc-active: #333355; --arc-gold: #ffd700; --arc-amber: #ffbf00; --arc-bronze: #cd7f32; --arc-cream: #fff8dc; --arc-blue: #4dabf7; --arc-green: #8fbc8f; --arc-error: #ef5350; }
* { box-sizing: border-box; }
body { background: var(--arc-bg); color: var(--arc-cream); font-family: Inter, ui-sans-serif, system-ui, sans-serif; line-height: 1.55; margin: 0; }
a { color: var(--arc-gold); text-decoration-thickness: 1px; text-underline-offset: 3px; }
a:hover { color: var(--arc-amber); }
.arc-shell { margin: 0 auto; max-width: 1080px; padding: 2rem 1.25rem 4rem; }
.arc-header { align-items: center; border-bottom: 1px solid var(--arc-bronze); display: flex; justify-content: space-between; padding-bottom: 1.25rem; }
.arc-brand { color: var(--arc-cream); font-weight: 750; letter-spacing: .08em; text-decoration: none; text-transform: uppercase; }
.arc-brand span, .arc-kicker, .arc-meta { color: var(--arc-gold); }
.arc-kicker { font-size: .75rem; font-weight: 700; letter-spacing: .14em; text-transform: uppercase; }
.arc-hero { padding: 4.5rem 0 2.5rem; }
.arc-hero h1 { font-size: clamp(2.25rem, 6vw, 4.5rem); letter-spacing: -.04em; line-height: 1; margin: .45rem 0 1rem; }
.arc-lede { color: #ddd5bc; font-size: 1.15rem; max-width: 42rem; }
.arc-list { display: grid; gap: 1rem; list-style: none; margin: 2rem 0; padding: 0; }
.arc-card { background: var(--arc-surface); border: 1px solid #3a3652; border-radius: .75rem; padding: 1.25rem; transition: border-color .15s, transform .15s; }
.arc-card:hover { border-color: var(--arc-bronze); transform: translateY(-2px); }
.arc-card h2 { font-size: 1.2rem; margin: 0 0 .45rem; }
.arc-meta { font-size: .9rem; margin: 0; }
.arc-button { background: var(--arc-gold); border: 1px solid var(--arc-gold); border-radius: .5rem; color: #171200; display: inline-block; font-weight: 800; padding: .7rem 1rem; text-decoration: none; }
.arc-button:hover { background: var(--arc-amber); color: #171200; }
.arc-job { background: var(--arc-surface); border-left: 4px solid var(--arc-gold); border-radius: .25rem .75rem .75rem .25rem; padding: 1.5rem; }
.arc-job article { color: #eee6cb; }
.arc-form { display: grid; gap: 1rem; margin-top: 2rem; max-width: 46rem; }
.arc-form label { color: #eee6cb; display: grid; font-weight: 700; gap: .35rem; }
.arc-form input, .arc-form textarea { background: #11111e; border: 1px solid #57516e; border-radius: .4rem; color: var(--arc-cream); font: inherit; padding: .65rem; width: 100%; }
.arc-form textarea { min-height: 9rem; resize: vertical; }
.arc-consent { align-items: start; color: #ddd5bc; display: flex !important; font-size: .9rem; font-weight: 400 !important; gap: .6rem; }
.arc-consent input { margin-top: .3rem; width: auto; }
.arc-notice { background: #1d2a28; border-left: 4px solid var(--arc-green); border-radius: .25rem; padding: 1rem 1.25rem; }
.arc-nav { display: flex; flex-wrap: wrap; gap: 1rem; margin: 1.5rem 0 2rem; }
.arc-stat-grid { display: grid; gap: 1rem; grid-template-columns: repeat(auto-fit, minmax(12rem, 1fr)); }
.arc-stat { background: var(--arc-surface); border-radius: .75rem; padding: 1rem; }
.arc-kanban { display: grid; gap: 1rem; grid-template-columns: repeat(7, minmax(14rem, 1fr)); overflow-x: auto; padding-bottom: 1rem; }
.arc-column { background: #151525; border-top: 3px solid var(--arc-bronze); min-height: 18rem; padding: .8rem; }
.arc-column h2 { font-size: .95rem; margin-top: 0; }
.arc-candidate-card { background: var(--arc-surface); border: 1px solid #3a3652; border-radius: .5rem; margin: .65rem 0; padding: .75rem; }
.arc-stat strong { color: var(--arc-gold); display: block; font-size: 2rem; }
.arc-table { border-collapse: collapse; margin-top: 1.5rem; width: 100%; }
.arc-table td, .arc-table th { border-bottom: 1px solid #3a3652; padding: .8rem .5rem; text-align: left; vertical-align: top; }
.arc-inline-form { display: grid; gap: .5rem; margin: 0; }
.arc-inline-form select, .arc-inline-form textarea { background: #11111e; border: 1px solid #57516e; border-radius: .4rem; color: var(--arc-cream); font: inherit; padding: .45rem; }
.arc-small-button { background: transparent; border: 1px solid var(--arc-gold); border-radius: .35rem; color: var(--arc-gold); font: inherit; font-weight: 700; padding: .4rem .6rem; }
.arc-footer { border-top: 1px solid #3a3652; color: #bfb79e; font-size: .85rem; margin-top: 3rem; padding-top: 1.25rem; }
@media (max-width: 600px) { .arc-shell { padding-top: 1.25rem; } .arc-hero { padding-top: 3rem; } .arc-header { align-items: flex-start; flex-direction: column; gap: .75rem; } }
""".strip()


def stylesheet() -> str:
    return AGENT_THEME_CSS


def careers_page(jobs: list[tuple[str, str, str]], base_path: str) -> str:
    cards = "".join(job_card(slug, title, location, base_path) for slug, title, location in jobs)
    content = (
        "<section class='arc-hero'><p class='arc-kicker'>ARCenal ATS</p>"
        "<h1>Construisons la suite, ensemble.</h1>"
        "<p class='arc-lede'>Découvrez nos opportunités et présentez votre candidature."
        "</p></section><section><h2>Offres ouvertes</h2>"
        f"<ul class='arc-list'>{cards}</ul>"
        f"<a class='arc-button' href='{base_path}/recrutement/candidature-spontanee'>"
        "Candidature spontanée</a></section>"
    )
    return document("Recrutement", content, base_path)


def job_page(
    slug: str,
    title: str,
    location: str,
    description: str,
    base_path: str,
) -> str:
    content = (
        "<section class='arc-hero'><p class='arc-kicker'>Offre d'emploi</p>"
        f"<h1>{escape(title)}</h1><p class='arc-meta'>{escape(location)}</p></section>"
        f"<section class='arc-job'><article>{line_breaks(description)}</article></section>"
        f"{application_form(f'{base_path}/recrutement/offres/{quote(slug)}/candidater', base_path)}"
    )
    return document(title, content, base_path)


def spontaneous_application_page(base_path: str) -> str:
    content = (
        "<section class='arc-hero'><p class='arc-kicker'>Candidature spontanée</p>"
        "<h1>Faisons connaissance.</h1>"
        "<p class='arc-lede'>Votre profil sera transmis à notre vivier de talents.</p></section>"
        f"{application_form(f'{base_path}/recrutement/candidature-spontanee', base_path)}"
    )
    return document("Candidature spontanée", content, base_path)


def application_confirmation_page(base_path: str) -> str:
    content = (
        "<section class='arc-hero'><p class='arc-kicker'>Candidature reçue</p>"
        "<h1>Merci pour votre candidature.</h1>"
        "<div class='arc-notice'>Notre équipe recrutement l'a bien reçue. "
        "Nous reviendrons vers vous si votre profil correspond à une opportunité.</div>"
        f"<p><a class='arc-button' href='{base_path}/recrutement'>Voir les offres</a></p></section>"
    )
    return document("Candidature reçue", content, base_path)


def application_form(action: str, base_path: str) -> str:
    return (
        f"<form class='arc-form' id='candidater' action='{escape(action, quote=True)}' method='post' enctype='multipart/form-data'>"
        "<label>Prénom<input name='first_name' autocomplete='given-name' required maxlength='100'></label>"
        "<label>Nom<input name='last_name' autocomplete='family-name' required maxlength='100'></label>"
        "<label>E-mail<input name='email' type='email' autocomplete='email' required maxlength='320'></label>"
        "<label>Localisation<input name='location' autocomplete='address-level2' maxlength='200'></label>"
        "<label>CV (PDF, DOC ou DOCX)<input name='resume' type='file' accept='.pdf,.doc,.docx' required></label>"
        "<label>Lettre ou message de motivation<textarea name='cover_letter' maxlength='20000'></textarea></label>"
        "<label class='arc-consent'><input name='consent' type='checkbox' value='true' required>"
        f"J'accepte le traitement de mes données conformément à la <a href='{base_path}/recrutement/confidentialite'>politique de confidentialité</a>.</label>"
        "<button class='arc-button' type='submit'>Envoyer ma candidature</button></form>"
    )


def privacy_page(base_path: str) -> str:
    content = (
        "<section class='arc-hero'><p class='arc-kicker'>Données personnelles</p>"
        "<h1>Politique de confidentialité</h1></section><section class='arc-job'><article>"
        "Les données transmises dans une candidature sont utilisées uniquement pour le recrutement "
        "et conservées dans l'espace sécurisé d'ARCenal ATS. Vous pouvez demander l'accès, la "
        "rectification ou l'effacement de vos données auprès de l'organisation qui publie cette offre."
        "</article></section>"
    )
    return document("Politique de confidentialité", content, base_path)


def internal_dashboard_page(
    job_count: int,
    application_count: int,
    talent_count: int,
    base_path: str,
) -> str:
    content = (
        "<p class='arc-kicker'>Espace recruteur</p><h1>Pilotage du recrutement</h1>"
        "<section class='arc-stat-grid'>"
        f"{stat_card('Offres', job_count)}{stat_card('Candidatures', application_count)}"
        f"{stat_card('Vivier', talent_count)}</section>"
    )
    return internal_document("Tableau de bord", content, base_path)


def internal_jobs_page(
    jobs: list[tuple[str, str, str, str]],
    base_path: str,
) -> str:
    rows = "".join(internal_job_row(job, base_path) for job in jobs)
    content = (
        "<p class='arc-kicker'>Offres</p><h1>Offres d'emploi</h1>"
        f"<form class='arc-form' action='{base_path}/interne/offres' method='post'>"
        "<label>Identifiant URL<input name='slug' required pattern='[a-z0-9-]+'></label>"
        "<label>Intitulé<input name='title' required></label><label>Localisation<input name='location' required></label>"
        "<label>Contrat<input name='contract_type' required></label><label>Résumé<textarea name='summary' required></textarea></label>"
        "<label>Description<textarea name='description' required></textarea></label>"
        "<button class='arc-button' type='submit'>Créer le brouillon</button></form>"
        f"<table class='arc-table'><thead><tr><th>Offre</th><th>Statut</th><th>Action</th></tr></thead><tbody>{rows}</tbody></table>"
    )
    return internal_document("Offres", content, base_path)


def internal_applications_page(
    applications: list[tuple[str, str, str, str, str, str | None, str | None]],
    base_path: str,
) -> str:
    columns = "".join(pipeline_column(stage, applications, base_path) for stage in pipeline_stages())
    content = (
        "<p class='arc-kicker'>Candidatures</p><h1>Pipeline de recrutement</h1>"
        f"<section class='arc-kanban'>{columns}</section>"
    )
    return internal_document("Candidatures", content, base_path)


def internal_candidate_page(
    application: tuple[str, str, str, str, str, str | None, str | None],
    documents: list[tuple[str, str, str, int]],
    history: list[tuple[str, str, str | None, str | None, str]],
    base_path: str,
) -> str:
    identifier, name, email, job_title, stage, letter, latest_note = application
    document_rows = "".join(
        f"<li><a href='{base_path}/api/v1/internal/documents/{quote(document_id)}'>{escape(filename)}</a> "
        f"<span class='arc-meta'>{escape(media_type)} · {byte_size} octets</span></li>"
        for document_id, filename, media_type, byte_size in documents
    ) or "<li>Aucun document</li>"
    history_rows = "".join(
        f"<li>{escape(occurred_at)} · {escape(actor)} · {escape(action)}"
        f"{history_change(previous, current)}</li>"
        for action, actor, previous, current, occurred_at in history
    ) or "<li>Aucun événement</li>"
    content = (
        "<p class='arc-kicker'>Dossier candidat</p>"
        f"<h1>{escape(name)}</h1><p class='arc-meta'>{escape(email)} · {escape(job_title)}</p>"
        f"<section class='arc-job'><h2>Étape : {escape(stage_label(stage))}</h2>"
        f"<p>{escape(letter or 'Aucun message de motivation')}</p>"
        f"<p class='arc-meta'>Dernière note : {escape(latest_note or 'Aucune note')}</p></section>"
        f"<section><h2>Documents</h2><ul class='arc-list'>{document_rows}</ul></section>"
        f"<section><h2>Historique</h2><ul class='arc-list'>{history_rows}</ul></section>"
        f"<p><a class='arc-small-button' href='{base_path}/interne/candidatures'>Retour au pipeline</a></p>"
    )
    return internal_document("Dossier candidat", content, base_path)


def internal_talent_pool_page(
    candidates: list[tuple[str, str, str]],
    base_path: str,
) -> str:
    rows = "".join(
        f"<li class='arc-card'><h2>{escape(name)}</h2><p class='arc-meta'>{escape(email)} · {escape(location)}</p></li>"
        for name, email, location in candidates
    )
    content = (
        "<p class='arc-kicker'>Vivier</p><h1>Talents</h1>"
        f"<ul class='arc-list'>{rows}</ul>"
    )
    return internal_document("Vivier", content, base_path)


def stat_card(label: str, value: int) -> str:
    return f"<article class='arc-stat'><strong>{value}</strong><span>{escape(label)}</span></article>"


def internal_job_row(job: tuple[str, str, str, str], base_path: str) -> str:
    slug, title, location, status = job
    action = ""
    if status == "draft":
        action = (
            f"<form class='arc-inline-form' action='{base_path}/interne/offres/{quote(slug)}/publier' method='post'>"
            "<button class='arc-small-button' type='submit'>Publier</button></form>"
        )
    return f"<tr><td>{escape(title)}<br><span class='arc-meta'>{escape(location)}</span></td><td>{escape(status)}</td><td>{action}</td></tr>"


def internal_application_row(
    application: tuple[str, str, str, str, str, str | None, str | None],
    base_path: str,
) -> str:
    identifier, name, email, job_title, stage, cover_letter, latest_note = application
    options = pipeline_options(stage)
    letter = escape(cover_letter or "Aucun message")
    note = escape(latest_note or "Aucune note")
    return (
        f"<tr><td>{escape(name)}<br><span class='arc-meta'>{escape(email)}</span></td>"
        f"<td>{escape(job_title)}</td><td><form class='arc-inline-form' action='{base_path}/interne/candidatures/{quote(identifier)}/pipeline' method='post'>"
        f"<select name='stage'>{options}</select><textarea name='note' placeholder='Ajouter une note'></textarea>"
        f"<button class='arc-small-button' type='submit'>Enregistrer</button></form></td><td>{letter}<br><span class='arc-meta'>{note}</span></td></tr>"
    )


def pipeline_stages() -> tuple[tuple[str, str], ...]:
    return (
        ("new", "Reçue"), ("qualifying", "À qualifier"), ("interview", "Entretien"),
        ("offer", "À décider"), ("hired", "Acceptée"), ("rejected", "Refusée"),
        ("talent_pool", "Vivier"),
    )


def pipeline_column(
    stage: tuple[str, str],
    applications: list[tuple[str, str, str, str, str, str | None, str | None]],
    base_path: str,
) -> str:
    stage_value, label = stage
    cards = "".join(
        candidate_card(application, base_path)
        for application in applications
        if application[4] == stage_value
    ) or "<p class='arc-meta'>Aucune candidature</p>"
    return f"<section class='arc-column'><h2>{escape(label)}</h2>{cards}</section>"


def candidate_card(
    application: tuple[str, str, str, str, str, str | None, str | None],
    base_path: str,
) -> str:
    identifier, name, email, job_title, stage, _, latest_note = application
    options = pipeline_options(stage)
    return (
        "<article class='arc-candidate-card'>"
        f"<a href='{base_path}/interne/candidatures/{quote(identifier)}'><strong>{escape(name)}</strong></a>"
        f"<p class='arc-meta'>{escape(job_title)} · {escape(email)}</p>"
        f"<p class='arc-meta'>{escape(latest_note or 'Aucune note')}</p>"
        f"<form class='arc-inline-form' action='{base_path}/interne/candidatures/{quote(identifier)}/pipeline' method='post'>"
        f"<select name='stage'>{options}</select><textarea name='note' placeholder='Ajouter une note'></textarea>"
        "<button class='arc-small-button' type='submit'>Mettre à jour</button></form></article>"
    )


def stage_label(stage: str) -> str:
    return dict(pipeline_stages()).get(stage, stage)


def history_change(previous: str | None, current: str | None) -> str:
    if previous is None and current is None:
        return ""
    return f" : {escape(previous or '—')} → {escape(current or '—')}"


def pipeline_options(current_stage: str) -> str:
    stages = (
        ("new", "Reçue"), ("qualifying", "À qualifier"), ("interview", "Entretien"),
        ("offer", "À décider"), ("hired", "Acceptée"), ("rejected", "Refusée"),
        ("talent_pool", "Vivier"),
    )
    return "".join(
        f"<option value='{value}'{' selected' if value == current_stage else ''}>{label}</option>"
        for value, label in stages
    )


def job_card(slug: str, title: str, location: str, base_path: str) -> str:
    return (
        "<li class='arc-card'><h2>"
        f"<a href='{base_path}/recrutement/offres/{escape(slug)}'>{escape(title)}</a></h2>"
        f"<p class='arc-meta'>{escape(location)}</p></li>"
    )


def line_breaks(value: str) -> str:
    return escape(value).replace("\n", "<br>")


def document(title: str, content: str, base_path: str) -> str:
    return (
        "<!doctype html><html lang='fr'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        f"<title>{escape(title)} · ARCenal ATS</title>"
        f"<link rel='stylesheet' href='{base_path}/public/arcenal-ats.css'></head><body>"
        "<div class='arc-shell'><header class='arc-header'>"
        f"<a class='arc-brand' href='{base_path}/recrutement'>ARCenal <span>ATS</span></a>"
        "<span class='arc-kicker'>Recrutement</span></header>"
        f"<main>{content}</main><footer class='arc-footer'>ARCenal ATS · Recrutement</footer>"
        "</div></body></html>"
    )


def internal_document(title: str, content: str, base_path: str) -> str:
    navigation = (
        "<nav class='arc-nav'>"
        f"<a href='{base_path}/interne'>Tableau de bord</a>"
        f"<a href='{base_path}/interne/offres'>Offres</a>"
        f"<a href='{base_path}/interne/candidatures'>Candidatures</a>"
        f"<a href='{base_path}/interne/vivier'>Vivier</a></nav>"
    )
    return document(title, f"{navigation}{content}", base_path)
