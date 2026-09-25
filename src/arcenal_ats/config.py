"""Runtime configuration loaded from the environment."""

from __future__ import annotations

from dataclasses import dataclass
from os import environ
from pathlib import Path
from typing import Mapping


class ConfigurationError(ValueError):
    """Raised when a required deployment setting is missing or unsafe."""


@dataclass(frozen=True)
class Settings:
    database_url: str
    document_directory: Path
    public_base_url: str
    allowed_widget_origins: tuple[str, ...]

    def validate(self) -> None:
        if not self.database_url.startswith("postgresql+"):
            raise ConfigurationError("ARCenal ATS requires a PostgreSQL SQLAlchemy URL.")
        if self.document_directory.is_absolute() is False:
            raise ConfigurationError("Document storage must use an absolute non-public path.")
        if not self.public_base_url.startswith("https://"):
            raise ConfigurationError("The public base URL must use HTTPS.")


def default_settings() -> Settings:
    return settings_from_environment(environ)


def settings_from_environment(environment: Mapping[str, str]) -> Settings:
    settings = Settings(
        database_url=environment.get(
            "ARCENAL_ATS_DATABASE_URL",
            "postgresql+psycopg://arcenal_ats@localhost/arcenal_ats",
        ),
        document_directory=Path(
            environment.get("ARCENAL_ATS_DOCUMENT_DIRECTORY", "/var/lib/arcenal-ats/documents")
        ),
        public_base_url=environment.get("ARCENAL_ATS_PUBLIC_BASE_URL", "https://localhost"),
        allowed_widget_origins=allowed_origins(environment.get("ARCENAL_ATS_ALLOWED_WIDGET_ORIGINS", "")),
    )
    settings.validate()
    return settings


def allowed_origins(value: str) -> tuple[str, ...]:
    return tuple(origin.strip() for origin in value.split(",") if origin.strip())
