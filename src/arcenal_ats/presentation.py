# ruff: noqa: E501
"""Server-rendered pages using ARCenal Agent's dark Hermes visual language."""

from __future__ import annotations

from html import escape


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
.arc-footer { border-top: 1px solid #3a3652; color: #bfb79e; font-size: .85rem; margin-top: 3rem; padding-top: 1.25rem; }
@media (max-width: 600px) { .arc-shell { padding-top: 1.25rem; } .arc-hero { padding-top: 3rem; } .arc-header { align-items: flex-start; flex-direction: column; gap: .75rem; } }
""".strip()


def stylesheet() -> str:
    return AGENT_THEME_CSS


def careers_page(jobs: list[tuple[str, str, str]]) -> str:
    cards = "".join(job_card(slug, title, location) for slug, title, location in jobs)
    content = (
        "<section class='arc-hero'><p class='arc-kicker'>ARCenal ATS</p>"
        "<h1>Construisons la suite, ensemble.</h1>"
        "<p class='arc-lede'>Découvrez nos opportunités et présentez votre candidature."
        "</p></section><section><h2>Offres ouvertes</h2>"
        f"<ul class='arc-list'>{cards}</ul>"
        "<a class='arc-button' href='/recrutement/candidature-spontanee'>"
        "Candidature spontanée</a></section>"
    )
    return document("Recrutement", content)


def job_page(title: str, location: str, description: str) -> str:
    content = (
        "<section class='arc-hero'><p class='arc-kicker'>Offre d'emploi</p>"
        f"<h1>{escape(title)}</h1><p class='arc-meta'>{escape(location)}</p></section>"
        f"<section class='arc-job'><article>{line_breaks(description)}</article></section>"
        "<p><a class='arc-button' href='#candidater'>Candidater</a></p>"
    )
    return document(title, content)


def job_card(slug: str, title: str, location: str) -> str:
    return (
        "<li class='arc-card'><h2>"
        f"<a href='/recrutement/offres/{escape(slug)}'>{escape(title)}</a></h2>"
        f"<p class='arc-meta'>{escape(location)}</p></li>"
    )


def line_breaks(value: str) -> str:
    return escape(value).replace("\n", "<br>")


def document(title: str, content: str) -> str:
    return (
        "<!doctype html><html lang='fr'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        f"<title>{escape(title)} · ARCenal ATS</title>"
        "<link rel='stylesheet' href='/public/arcenal-ats.css'></head><body>"
        "<div class='arc-shell'><header class='arc-header'>"
        "<a class='arc-brand' href='/recrutement'>ARCenal <span>ATS</span></a>"
        "<span class='arc-kicker'>Recrutement</span></header>"
        f"<main>{content}</main><footer class='arc-footer'>ARCenal ATS · Recrutement</footer>"
        "</div></body></html>"
    )
