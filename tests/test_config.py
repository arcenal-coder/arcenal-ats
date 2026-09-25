from __future__ import annotations

import unittest
from pathlib import Path

from arcenal_ats.config import ConfigurationError, Settings, settings_from_environment


class SettingsTest(unittest.TestCase):
    def test_accepts_a_secure_postgresql_configuration(self) -> None:
        settings = Settings(
            "postgresql+psycopg://ats@localhost/ats",
            Path("/var/lib/ats"),
            "https://ats.example.test",
            (),
        )
        settings.validate()

    def test_rejects_non_postgresql_database(self) -> None:
        settings = Settings(
            "sqlite:///ats.db", Path("/var/lib/ats"), "https://ats.example.test", ()
        )
        with self.assertRaises(ConfigurationError):
            settings.validate()

    def test_rejects_relative_document_directory(self) -> None:
        settings = Settings(
            "postgresql+psycopg://ats@localhost/ats",
            Path("documents"),
            "https://ats.example.test",
            (),
        )
        with self.assertRaises(ConfigurationError):
            settings.validate()

    def test_loads_the_widget_allow_list_from_the_environment(self) -> None:
        settings = settings_from_environment(
            {
                "ARCENAL_ATS_DATABASE_URL": "postgresql+psycopg:///arcenal_ats",
                "ARCENAL_ATS_DOCUMENT_DIRECTORY": "/var/lib/arcenal_ats/documents",
                "ARCENAL_ATS_PUBLIC_BASE_URL": "https://ats.example.test",
                "ARCENAL_ATS_ALLOWED_WIDGET_ORIGINS": "https://site.example, https://jobs.example",
            }
        )
        self.assertEqual(
            settings.allowed_widget_origins,
            ("https://site.example", "https://jobs.example"),
        )
