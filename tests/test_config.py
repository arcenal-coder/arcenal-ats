from __future__ import annotations

import unittest
from pathlib import Path

from arcenal_ats.config import ConfigurationError, Settings


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
