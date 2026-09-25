"""Private document storage; no storage URL is exposed by public endpoints."""

from __future__ import annotations

import hashlib
from pathlib import Path
from uuid import UUID, uuid4

from arcenal_ats.domain import UploadPolicy


class PrivateDocumentStore:
    def __init__(self, directory: Path, policy: UploadPolicy) -> None:
        self._directory = directory
        self._policy = policy

    def save(self, candidate_id: UUID, filename: str, media_type: str, content: bytes) -> str:
        self._policy.validate(filename, media_type, len(content))
        self._directory.mkdir(mode=0o750, parents=True, exist_ok=True)
        storage_key = self._storage_key(candidate_id, filename, content)
        target = self._directory / storage_key
        target.parent.mkdir(mode=0o750, exist_ok=True)
        target.write_bytes(content)
        target.chmod(0o640)
        return storage_key

    def _storage_key(self, candidate_id: UUID, filename: str, content: bytes) -> str:
        digest = hashlib.sha256(content).hexdigest()[:16]
        suffix = Path(filename).suffix.lower()
        return f"{candidate_id}/{uuid4()}-{digest}{suffix}"
