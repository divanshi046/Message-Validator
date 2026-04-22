"""Tests for the Git commit message validator."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from validator import (
    LARGE_FILE_LIMIT_BYTES,
    run_pre_commit_checks,
    scan_staged_content,
    scan_text_content,
    validate_commit_message,
)


class CommitMessageValidationTests(unittest.TestCase):
    def test_accepts_valid_conventional_commit(self) -> None:
        result = validate_commit_message("feat(auth): add jwt login support\n")
        self.assertTrue(result.is_valid)
        self.assertEqual(result.errors, [])

    def test_accepts_auto_generated_merge_message(self) -> None:
        result = validate_commit_message("Merge branch 'main' into feature/auth\n")
        self.assertTrue(result.is_valid)

    def test_rejects_empty_commit_message(self) -> None:
        result = validate_commit_message("\n\n")
        self.assertFalse(result.is_valid)
        self.assertIn("Commit message cannot be empty.", result.errors)

    def test_rejects_unknown_commit_type(self) -> None:
        result = validate_commit_message("feature(api): add user endpoint")
        self.assertFalse(result.is_valid)
        self.assertIn("Unknown commit type 'feature'.", result.errors[0])

    def test_rejects_invalid_subject_format(self) -> None:
        result = validate_commit_message("added login flow")
        self.assertFalse(result.is_valid)
        self.assertEqual(
            result.errors[0],
            "Use Conventional Commits format: <type>(<scope>): <description>.",
        )

    def test_rejects_uppercase_description_start(self) -> None:
        result = validate_commit_message("fix: Resolve token refresh bug")
        self.assertFalse(result.is_valid)
        self.assertIn("Description must start with a lowercase letter.", result.errors)

    def test_rejects_short_description(self) -> None:
        result = validate_commit_message("fix: too short")
        self.assertFalse(result.is_valid)
        self.assertIn("Description is too short. Use at least 10 characters.", result.errors)

    def test_rejects_trailing_period(self) -> None:
        result = validate_commit_message("docs: update readme files.")
        self.assertFalse(result.is_valid)
        self.assertIn("Description must not end with a period.", result.errors)

    def test_rejects_body_without_blank_line_separator(self) -> None:
        result = validate_commit_message("feat: add auth caching\nBody starts too early")
        self.assertFalse(result.is_valid)
        self.assertIn("Add a blank line between the subject and the body.", result.errors)

    def test_rejects_subject_over_seventy_two_characters(self) -> None:
        message = (
            "feat(api): add endpoint for validating commit messages across workflows "
            "in automation"
        )
        result = validate_commit_message(message)
        self.assertFalse(result.is_valid)
        self.assertTrue(any("Subject line is too long" in error for error in result.errors))


class TextScanningTests(unittest.TestCase):
    def test_reports_blocking_text_issues(self) -> None:
        report = scan_text_content(
            "app.py",
            "<<<<<<< HEAD\nvalue = 1  \n=======\n>>>>>>> branch\n",
        )
        self.assertFalse(report.is_valid)
        self.assertEqual(len(report.errors), 4)

    def test_reports_debug_statement_as_warning(self) -> None:
        report = scan_text_content("app.py", "print('debug')\n")
        self.assertTrue(report.is_valid)
        self.assertEqual(len(report.warnings), 1)
        self.assertIn("contains a debug statement", report.warnings[0])


class StagedContentScanningTests(unittest.TestCase):
    def test_warns_for_large_text_file(self) -> None:
        content = (b"a" * LARGE_FILE_LIMIT_BYTES) + b"extra"
        report = scan_staged_content("big.txt", content)
        self.assertTrue(report.is_valid)
        self.assertEqual(len(report.warnings), 1)
        self.assertIn("is large", report.warnings[0])

    def test_skips_text_checks_for_binary_files(self) -> None:
        content = b"\x00print('debug')  \n"
        report = scan_staged_content("image.bin", content)
        self.assertTrue(report.is_valid)
        self.assertEqual(report.warnings, [])

    def test_aggregates_reports_for_all_staged_files(self) -> None:
        with patch("validator.get_staged_files", return_value=["bad.py", "warn.js"]), patch(
            "validator.get_staged_file_content",
            side_effect=[b"bad = 1  \n", b"console.log('debug');\n"],
        ):
            report = run_pre_commit_checks()

        self.assertFalse(report.is_valid)
        self.assertEqual(len(report.errors), 1)
        self.assertEqual(len(report.warnings), 1)


if __name__ == "__main__":
    unittest.main()
