#!/usr/bin/env python3
"""Shared validation logic for Git commit hooks."""

from __future__ import annotations

from dataclasses import dataclass, field
import re
import subprocess

ALLOWED_TYPES = (
    "feat",
    "fix",
    "docs",
    "style",
    "refactor",
    "test",
    "chore",
    "perf",
    "ci",
    "build",
    "revert",
)

AUTO_ALLOWED_PREFIXES = (
    "Merge ",
    "Revert ",
    "fixup! ",
    "squash! ",
)

HEADER_PATTERN = re.compile(
    r"^(?P<type>[a-z]+)"
    r"(?:\((?P<scope>[a-z0-9._/-]+)\))?"
    r"(?P<breaking>!)?"
    r": (?P<description>.+)$"
)

DEBUG_PATTERNS = (
    re.compile(r"\bprint\s*\("),
    re.compile(r"\bconsole\.log\s*\("),
    re.compile(r"\bdebugger\b"),
    re.compile(r"\bpdb\.set_trace\s*\("),
)

CONFLICT_MARKERS = ("<<<<<<<", "=======", ">>>>>>>")
MAX_SUBJECT_LENGTH = 72
MIN_DESCRIPTION_LENGTH = 10
LARGE_FILE_LIMIT_BYTES = 500 * 1024


@dataclass(slots=True)
class ValidationResult:
    is_valid: bool
    errors: list[str] = field(default_factory=list)


@dataclass(slots=True)
class PreCommitReport:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not self.errors


def validate_commit_message(message: str) -> ValidationResult:
    """Validate a commit message against project rules."""
    stripped_message = message.strip("\n")
    if not stripped_message.strip():
        return ValidationResult(False, ["Commit message cannot be empty."])

    lines = stripped_message.splitlines()
    subject = lines[0].strip()

    if subject.startswith(AUTO_ALLOWED_PREFIXES):
        return ValidationResult(True)

    match = HEADER_PATTERN.fullmatch(subject)
    errors: list[str] = []

    if not match:
        errors.append(
            "Use Conventional Commits format: <type>(<scope>): <description>."
        )
        errors.append("Example: feat(auth): add JWT login support")
        return ValidationResult(False, errors)

    commit_type = match.group("type")
    description = match.group("description")

    if commit_type not in ALLOWED_TYPES:
        errors.append(
            f"Unknown commit type '{commit_type}'. Allowed types: {', '.join(ALLOWED_TYPES)}."
        )

    if len(subject) > MAX_SUBJECT_LENGTH:
        errors.append(
            f"Subject line is too long ({len(subject)} characters). Keep it within 72 characters."
        )

    if len(description) < MIN_DESCRIPTION_LENGTH:
        errors.append(
            f"Description is too short. Use at least {MIN_DESCRIPTION_LENGTH} characters."
        )

    if not description[0].islower():
        errors.append("Description must start with a lowercase letter.")

    if description.endswith("."):
        errors.append("Description must not end with a period.")

    if len(lines) > 1 and lines[1].strip():
        errors.append("Add a blank line between the subject and the body.")

    return ValidationResult(not errors, errors)


def scan_text_content(path: str, text: str) -> PreCommitReport:
    """Scan staged text for issues that should block or warn."""
    report = PreCommitReport()

    for line_number, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()

        if line.startswith(CONFLICT_MARKERS):
            report.errors.append(
                f"{path}:{line_number} contains a merge conflict marker."
            )

        if re.search(r"[ \t]+$", line):
            report.errors.append(
                f"{path}:{line_number} contains trailing whitespace."
            )

        if any(pattern.search(line) for pattern in DEBUG_PATTERNS):
            report.warnings.append(
                f"{path}:{line_number} contains a debug statement: {stripped}"
            )

    return report


def scan_staged_content(path: str, content: bytes) -> PreCommitReport:
    """Scan staged bytes and skip text-only rules for binary files."""
    report = PreCommitReport()

    if len(content) > LARGE_FILE_LIMIT_BYTES:
        size_kb = len(content) / 1024
        report.warnings.append(
            f"{path} is large ({size_kb:.1f} KB). Consider avoiding large files in commits."
        )

    if b"\x00" in content:
        return report

    text = content.decode("utf-8", errors="replace")
    text_report = scan_text_content(path, text)
    report.errors.extend(text_report.errors)
    report.warnings.extend(text_report.warnings)
    return report


def run_git_command(args: list[str]) -> bytes:
    """Run a Git command and return stdout bytes."""
    completed = subprocess.run(
        ["git", *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return completed.stdout


def get_staged_files() -> list[str]:
    """Return staged files that were added, copied, modified, or renamed."""
    output = run_git_command(["diff", "--cached", "--name-only", "--diff-filter=ACMR"])
    return [line for line in output.decode("utf-8").splitlines() if line.strip()]


def get_staged_file_content(path: str) -> bytes:
    """Read file content from the staged snapshot, not the working tree."""
    return run_git_command(["show", f":{path}"])


def run_pre_commit_checks() -> PreCommitReport:
    """Scan all staged files and aggregate blocking errors and warnings."""
    report = PreCommitReport()

    for path in get_staged_files():
        file_report = scan_staged_content(path, get_staged_file_content(path))
        report.errors.extend(file_report.errors)
        report.warnings.extend(file_report.warnings)

    return report
