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
