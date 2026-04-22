#!/usr/bin/env python3
"""Implementation for the commit-msg hook."""

from __future__ import annotations

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from validator import validate_commit_message


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("Usage: commit-msg <commit-message-file>", file=sys.stderr)
        return 1

    message_path = Path(argv[1])
    message = message_path.read_text(encoding="utf-8", errors="replace")
    result = validate_commit_message(message)

    if result.is_valid:
        return 0

    print("Commit rejected: message does not follow Conventional Commits.", file=sys.stderr)
    for error in result.errors:
        print(f"  - {error}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
