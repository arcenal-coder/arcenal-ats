from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from uuid import uuid4

from arcenal_ats.domain import DEFAULT_UPLOAD_POLICY
from arcenal_ats.storage import PrivateDocumentStore


class PrivateDocumentStoreTest(unittest.TestCase):
    def test_saves_a_document_under_a_candidate_private_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            key = PrivateDocumentStore(root, DEFAULT_UPLOAD_POLICY).save(
                uuid4(), "cv.pdf", "application/pdf", b"pdf"
            )
            self.assertTrue((root / key).is_file())

    def test_does_not_keep_the_original_filename_as_the_storage_key(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            key = PrivateDocumentStore(Path(temporary_directory), DEFAULT_UPLOAD_POLICY).save(
                uuid4(), "cv.pdf", "application/pdf", b"pdf"
            )
            self.assertNotEqual(key, "cv.pdf")
