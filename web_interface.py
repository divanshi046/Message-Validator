#!/usr/bin/env python3
"""Local web interface for the commit message validator project."""

from __future__ import annotations

from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import argparse
import json
import mimetypes
import subprocess

from validator import (
    ALLOWED_TYPES,
    AUTO_ALLOWED_PREFIXES,
    HEADER_PATTERN,
    MAX_SUBJECT_LENGTH,
    MIN_DESCRIPTION_LENGTH,
    get_staged_files,
    run_pre_commit_checks,
    scan_staged_content,
    validate_commit_message,
)

BASE_DIR = Path(__file__).resolve().parent
WEB_DIR = BASE_DIR / "web"


def build_message_payload(message: str) -> dict[str, object]:
    """Return structured data for the commit message validator UI."""
    result = validate_commit_message(message)
    stripped_message = message.strip("\n")
    lines = stripped_message.splitlines() if stripped_message else []
    subject = lines[0].strip() if lines else ""
    auto_allowed = subject.startswith(AUTO_ALLOWED_PREFIXES)
    match = HEADER_PATTERN.fullmatch(subject)

    commit_type = match.group("type") if match else None
    scope = match.group("scope") if match else None
    description = match.group("description") if match else ""
    breaking = bool(match and match.group("breaking"))

    checks = [
        {
            "label": "Matches Conventional Commits header format",
            "passed": auto_allowed or bool(match),
        },
        {
            "label": "Uses an allowed commit type",
            "passed": auto_allowed or (commit_type in ALLOWED_TYPES if commit_type else False),
        },
        {
            "label": f"Subject stays within {MAX_SUBJECT_LENGTH} characters",
            "passed": len(subject) <= MAX_SUBJECT_LENGTH,
        },
        {
            "label": f"Description is at least {MIN_DESCRIPTION_LENGTH} characters",
            "passed": auto_allowed or len(description) >= MIN_DESCRIPTION_LENGTH,
        },
        {
            "label": "Description starts with lowercase",
            "passed": auto_allowed or (bool(description) and description[0].islower()),
        },
        {
            "label": "Description does not end with a period",
            "passed": auto_allowed or (bool(description) and not description.endswith(".")),
        },
        {
            "label": "Body is separated from the subject by a blank line",
            "passed": len(lines) <= 1 or not lines[1].strip(),
        },
    ]

    return {
        "is_valid": result.is_valid,
        "errors": result.errors,
        "subject": subject,
        "subject_length": len(subject),
        "line_count": len(lines),
        "auto_allowed": auto_allowed,
        "allowed_types": list(ALLOWED_TYPES),
        "parsed": {
            "type": commit_type,
            "scope": scope,
            "description": description or None,
            "breaking": breaking,
        },
        "checks": checks,
    }


def build_content_payload(path: str, content: str) -> dict[str, object]:
    """Return structured data for the file scan UI."""
    normalized_path = path.strip() or "demo.txt"
    content_bytes = content.encode("utf-8")
    report = scan_staged_content(normalized_path, content_bytes)

    return {
        "is_valid": report.is_valid,
        "errors": report.errors,
        "warnings": report.warnings,
        "path": normalized_path,
        "line_count": len(content.splitlines()),
        "size_bytes": len(content_bytes),
        "size_kb": round(len(content_bytes) / 1024, 2),
    }


def build_staged_payload() -> dict[str, object]:
    """Return a snapshot of current staged-file checks."""
    try:
        files = get_staged_files()
        report = run_pre_commit_checks()
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.decode("utf-8", errors="replace").strip()
        return {
            "is_valid": False,
            "files": [],
            "errors": [stderr or "Unable to inspect staged files."],
            "warnings": [],
        }

    return {
        "is_valid": report.is_valid,
        "files": files,
        "errors": report.errors,
        "warnings": report.warnings,
    }


class ValidatorRequestHandler(BaseHTTPRequestHandler):
    """Serve the local web UI and its JSON endpoints."""

    def do_GET(self) -> None:
        if self.path in {"/", "/index.html"}:
            self._serve_static_file("index.html")
            return

        if self.path == "/api/staged-report":
            self._send_json(HTTPStatus.OK, build_staged_payload())
            return

        relative_path = self.path.removeprefix("/static/").lstrip("/")
        if relative_path:
            self._serve_static_file(relative_path)
            return

        self.send_error(HTTPStatus.NOT_FOUND, "Not found")

    def do_POST(self) -> None:
        if self.path == "/api/validate-message":
            payload = self._read_json_body()
            if payload is None:
                return
            message = str(payload.get("message", ""))
            self._send_json(HTTPStatus.OK, build_message_payload(message))
            return

        if self.path == "/api/scan-content":
            payload = self._read_json_body()
            if payload is None:
                return
            path = str(payload.get("path", "demo.txt"))
            content = str(payload.get("content", ""))
            self._send_json(HTTPStatus.OK, build_content_payload(path, content))
            return

        self.send_error(HTTPStatus.NOT_FOUND, "Not found")

    def log_message(self, format: str, *args: object) -> None:
        """Keep the local demo server output clean."""
        return

    def _read_json_body(self) -> dict[str, object] | None:
        content_length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(content_length)

        try:
            payload = json.loads(raw_body.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            self._send_json(
                HTTPStatus.BAD_REQUEST,
                {"error": "Request body must be valid JSON."},
            )
            return None

        if not isinstance(payload, dict):
            self._send_json(
                HTTPStatus.BAD_REQUEST,
                {"error": "JSON body must be an object."},
            )
            return None

        return payload

    def _serve_static_file(self, relative_path: str) -> None:
        target = (WEB_DIR / relative_path).resolve()

        if not str(target).startswith(str(WEB_DIR.resolve())) or not target.is_file():
            self.send_error(HTTPStatus.NOT_FOUND, "File not found")
            return

        content_type, _ = mimetypes.guess_type(target.name)
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type or "application/octet-stream")
        self.end_headers()
        self.wfile.write(target.read_bytes())

    def _send_json(self, status: HTTPStatus, payload: dict[str, object]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the commit validator web interface.")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to.")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    server = ThreadingHTTPServer((args.host, args.port), ValidatorRequestHandler)
    print(f"Commit Validator UI running at http://{args.host}:{args.port}")
    print("Press Ctrl+C to stop the server.")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
    finally:
        server.server_close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
