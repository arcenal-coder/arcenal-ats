from __future__ import annotations

import unittest

from arcenal_ats.presentation import (
    careers_page,
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
            [("python-developer", "Python Developer", "Paris", "draft")],
            "/ats",
        )

        self.assertIn("/ats/interne/offres", page)
        self.assertIn("/ats/interne/offres/python-developer/publier", page)

    def test_renders_the_full_v1_pipeline_in_the_recruiter_view(self) -> None:
        page = internal_applications_page(
            [("abc", "Ada Lovelace", "ada@example.test", "Python", "new", None)],
            "/ats",
        )

        self.assertIn("À qualifier", page)
        self.assertIn("À décider", page)
        self.assertIn("Vivier", page)

    def test_renders_a_careers_link_to_a_job(self) -> None:
        page = careers_page([("python-developer", "Python Developer", "Paris")], "/ats")
        self.assertIn("/ats/recrutement/offres/python-developer", page)
        self.assertIn("/ats/public/arcenal-ats.css", page)
