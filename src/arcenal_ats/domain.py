"""Pure business rules shared by HTTP and persistence adapters."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class JobStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    CLOSED = "closed"
    ARCHIVED = "archived"


class PipelineStage(str, Enum):
    NEW = "new"
    QUALIFYING = "qualifying"
    INTERVIEW = "interview"
    OFFER = "offer"
    HIRED = "hired"
    REJECTED = "rejected"


class DomainValidationError(ValueError):
    """Raised when a request violates an ATS business invariant."""


@dataclass(frozen=True)
class UploadPolicy:
    allowed_media_types: frozenset[str]
    maximum_size_bytes: int

    def accepts(self, filename: str, media_type: str, size_bytes: int) -> bool:
        return (
            self._has_safe_name(filename)
            and self._has_safe_type(media_type)
            and self._has_safe_size(size_bytes)
        )

    def validate(self, filename: str, media_type: str, size_bytes: int) -> None:
        if self.accepts(filename, media_type, size_bytes):
            return
        raise DomainValidationError("The uploaded document does not meet the security policy.")

    def _has_safe_name(self, filename: str) -> bool:
        return bool(filename) and Path(filename).name == filename and "\x00" not in filename

    def _has_safe_type(self, media_type: str) -> bool:
        return media_type.lower() in self.allowed_media_types

    def _has_safe_size(self, size_bytes: int) -> bool:
        return 0 < size_bytes <= self.maximum_size_bytes


DEFAULT_UPLOAD_POLICY = UploadPolicy(
    allowed_media_types=frozenset(
        {
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        }
    ),
    maximum_size_bytes=10 * 1024 * 1024,
)
