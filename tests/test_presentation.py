from __future__ import annotations

import unittest

from arcenal_ats.presentation import careers_page, job_page, stylesheet


class PresentationTest(unittest.TestCase):
    def test_exposes_the_arcenal_agent_dark_theme_tokens(self) -> None:
        css = stylesheet()
        self.assertIn("#101014", css)
        self.assertIn("#ffd700", css)
        self.assertIn("#1a1a2e", css)

    def test_escapes_job_data_in_the_public_page(self) -> None:
        page = job_page("<script>", "Paris", "<b>description</b>")
        self.assertNotIn("<script>", page)
        self.assertIn("&lt;b&gt;description&lt;/b&gt;", page)

    def test_renders_a_careers_link_to_a_job(self) -> None:
        page = careers_page([("python-developer", "Python Developer", "Paris")])
        self.assertIn("/recrutement/offres/python-developer", page)
