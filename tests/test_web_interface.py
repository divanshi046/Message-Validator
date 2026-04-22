"""Tests for the local web interface helpers."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from web_interface import (
    build_content_payload,
    build_message_payload,
    build_staged_payload,
)


class MessagePayloadTests(unittest.TestCase):
    def test_build_message_payload_for_valid_message(self) -> None:
        payload = build_message_payload("feat(auth): add jwt login support")
        self.assertTrue(payload["is_valid"])
        self.assertEqual(payload["parsed"]["type"], "feat")
        self.assertEqual(payload["parsed"]["scope"], "auth")
        self.assertFalse(payload["parsed"]["breaking"])

    def test_build_message_payload_for_invalid_message(self) -> None:
        payload = build_message_payload("updated code")
        self.assertFalse(payload["is_valid"])
        self.assertGreater(len(payload["errors"]), 0)


class ContentPayloadTests(unittest.TestCase):
    def test_build_content_payload_reports_warnings(self) -> None:
        payload = build_content_payload("demo.py", "print('debug')\n")
        self.assertTrue(payload["is_valid"])
        self.assertEqual(payload["path"], "demo.py")
        self.assertEqual(len(payload["warnings"]), 1)

    def test_build_content_payload_reports_errors(self) -> None:
        payload = build_content_payload("demo.py", "<<<<<<< HEAD\nvalue = 1  \n")
        self.assertFalse(payload["is_valid"])
        self.assertGreaterEqual(len(payload["errors"]), 2)


class StagedPayloadTests(unittest.TestCase):
    def test_build_staged_payload_returns_files_and_results(self) -> None:
        with patch("web_interface.get_staged_files", return_value=["demo.txt"]), patch(
            "web_interface.run_pre_commit_checks"
        ) as mock_report:
            mock_report.return_value.errors = []
            mock_report.return_value.warnings = ["demo.txt:1 contains a debug statement"]
            mock_report.return_value.is_valid = True

            payload = build_staged_payload()

        self.assertTrue(payload["is_valid"])
        self.assertEqual(payload["files"], ["demo.txt"])
        self.assertEqual(len(payload["warnings"]), 1)


if __name__ == "__main__":
    unittest.main()
