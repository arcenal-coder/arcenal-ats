from __future__ import annotations

import unittest

from arcenal_ats.presentation import (
    careers_page,
    internal_candidate_page,
    internal_talent_pool_page,
    internal_applications_page,
    internal_jobs_page,
    job_page,
    spontaneous_application_page,
    stylesheet,
)


class PresentationTest(unittest.TestCase):
    def test_exposes_the_arcenal_agent_dark_theme_tokens(self) -> None:
        css = stylesheet()
        self.assertIn("#101014", css)
        self.assertIn("#ffd700", css)
        self.assertIn("#1a1a2e", css)

    def test_escapes_job_data_in_the_public_page(self) -> None:
        page = job_page("python", "<script>", "Paris", "<b>description</b>", "/ats")
        self.assertNotIn("<script>", page)
        self.assertIn("&lt;b&gt;description&lt;/b&gt;", page)

    def test_renders_a_postable_application_form_under_the_installation_path(self) -> None:
        page = job_page("python-developer", "Python Developer", "Paris", "Description", "/ats")

        self.assertIn("method='post'", page)
        self.assertIn("enctype='multipart/form-data'", page)
        self.assertIn("/ats/recrutement/offres/python-developer/candidater", page)
        self.assertIn("name='resume'", page)

    def test_renders_a_spontaneous_application_form(self) -> None:
        page = spontaneous_application_page("/ats")

        self.assertIn("/ats/recrutement/candidature-spontanee", page)
        self.assertIn("politique de confidentialité", page)

    def test_renders_recruiter_actions_under_the_internal_path(self) -> None:
        page = internal_jobs_page(
            [
                (
                    "python-developer",
                    "Python Developer",
                    "Paris",
                    "CDI",
                    "Résumé",
                    "Description",
                    "draft",
                )
            ],
            "/ats",
        )

        self.assertIn("/ats/interne/offres", page)
        self.assertIn("/ats/interne/offres/python-developer/publier", page)
        self.assertIn("/ats/interne/offres/python-developer/modifier", page)
        self.assertIn("/ats/interne/offres/python-developer/archiver", page)

    def test_renders_the_full_v1_pipeline_in_the_recruiter_view(self) -> None:
        page = internal_applications_page(
            [
                (
                    "abc",
                    "Ada Lovelace",
                    "ada@example.test",
                    "Python",
                    "new",
                    None,
                    "Note de suivi",
                )
            ],
            "/ats",
        )

        self.assertIn("À qualifier", page)
        self.assertIn("À décider", page)
        self.assertIn("Vivier", page)
        self.assertIn("Note de suivi", page)
        self.assertIn("arc-kanban", page)
        self.assertIn("/ats/interne/candidatures/abc", page)

    def test_renders_a_candidate_document_and_history_through_internal_paths(self) -> None:
        page = internal_candidate_page(
            ("abc", "Ada Lovelace", "ada@example.test", "Python", "new", None, None),
            [("doc", "cv.pdf", "application/pdf", 42)],
            [("application.stage_changed", "recruiter", "new", "qualifying", "2026-09-28")],
            "/ats",
        )

        self.assertIn("/ats/api/v1/internal/documents/doc", page)
        self.assertIn("new → qualifying", page)
        self.assertIn("Retour au pipeline", page)

    def test_renders_a_searchable_talent_pool_under_the_installation_path(self) -> None:
        page = internal_talent_pool_page(
            [("candidate", "Ada Lovelace", "ada@example.test", "Paris")],
            [("python", "Python")],
            "/ats",
        )

        self.assertIn("/ats/interne/vivier", page)
        self.assertIn("name='query'", page)
        self.assertIn("Ada Lovelace", page)
        self.assertIn("/ats/interne/vivier/candidate/reactiver", page)

    def test_renders_a_careers_link_to_a_job(self) -> None:
        page = careers_page([("python-developer", "Python Developer", "Paris")], "/ats")
        self.assertIn("/ats/recrutement/offres/python-developer", page)
        self.assertIn("/ats/public/arcenal-ats.css", page)
