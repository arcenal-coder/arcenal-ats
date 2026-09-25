"""Runtime configuration loaded from the environment."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


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
    settings = Settings(
        database_url="postgresql+psycopg://arcenal_ats@localhost/arcenal_ats",
        document_directory=Path("/var/lib/arcenal-ats/documents"),
        public_base_url="https://localhost",
        allowed_widget_origins=(),
    )
    settings.validate()
    return settings
