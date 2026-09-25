from __future__ import annotations

import unittest

from arcenal_ats.domain import DEFAULT_UPLOAD_POLICY, DomainValidationError


class UploadPolicyTest(unittest.TestCase):
    def test_accepts_a_pdf_within_the_size_limit(self) -> None:
        self.assertTrue(DEFAULT_UPLOAD_POLICY.accepts("cv.pdf", "application/pdf", 1024))

    def test_rejects_an_oversized_document(self) -> None:
        with self.assertRaises(DomainValidationError):
            DEFAULT_UPLOAD_POLICY.validate("cv.pdf", "application/pdf", 11 * 1024 * 1024)

    def test_rejects_a_path_traversal_filename(self) -> None:
        with self.assertRaises(DomainValidationError):
            DEFAULT_UPLOAD_POLICY.validate("../../cv.pdf", "application/pdf", 1024)

    def test_rejects_an_unsupported_media_type(self) -> None:
        with self.assertRaises(DomainValidationError):
            DEFAULT_UPLOAD_POLICY.validate("cv.exe", "application/octet-stream", 1024)
