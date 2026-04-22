#!/usr/bin/env python3
"""Implementation for the pre-commit hook."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from validator import run_pre_commit_checks


def main() -> int:
    try:
        report = run_pre_commit_checks()
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.decode("utf-8", errors="replace").strip()
        print(stderr or "Git pre-commit checks failed to run.", file=sys.stderr)
        return 1

    if report.errors:
        print("Commit rejected: staged files have blocking issues.", file=sys.stderr)
        for error in report.errors:
            print(f"  - {error}", file=sys.stderr)

    if report.warnings:
        output = sys.stderr if report.errors else sys.stdout
        print("Warnings from staged file scan:", file=output)
        for warning in report.warnings:
            print(f"  - {warning}", file=output)

    return 0 if report.is_valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
