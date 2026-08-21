from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from . import __version__
from .analyzer import analyze_all, analyze_text
from .ingest import InputFormatError, normalize_input
from .models import IncidentAnalysis
from .redaction import redact_analysis

DEFAULT_MAX_BODY_BYTES = 1_048_576
API_VERSION = "1"


class APIError(ValueError):
    """Raised when an API request is invalid."""

    def __init__(self, message: str, code: str = "invalid_request") -> None:
        super().__init__(message)
        self.code = code


def _analysis_payload(payload: dict[str, Any]) -> tuple[Any, int]:
    raw_log = payload.get("log")
    if not isinstance(raw_log, str):
        raise APIError("'log' must be a string", "invalid_log")

    input_format = payload.get("input_format", "auto")
    if input_format not in {"auto", "text", "jsonl"}:
        raise APIError("'input_format' must be 'auto', 'text', or 'jsonl'", "invalid_input_format")

    source_filters: dict[str, str] = {}
    for key in ("host", "service", "unit", "container"):
        value = payload.get(key)
        if value is not None:
            if not isinstance(value, str) or not value:
                raise APIError(f"'{key}' must be a non-empty string when supplied", f"invalid_{key}")
            source_filters[key] = value

    include_context = payload.get("include_context", False)
    all_incidents = payload.get("all", False)
    redact = payload.get("redact", False)
    for key, value in (("include_context", include_context), ("all", all_incidents), ("redact", redact)):
        if not isinstance(value, bool):
            raise APIError(f"'{key}' must be a boolean", f"invalid_{key}")

    try:
        normalized = normalize_input(
            raw_log,
            input_format,
            include_context=include_context,
            source_filters=source_filters,
        )
    except InputFormatError as exc:
        raise APIError(f"invalid structured input: {exc}", "invalid_structured_input") from exc

    analyses: tuple[IncidentAnalysis, ...]
    analyses = analyze_all(normalized) if all_incidents else (analyze_text(normalized),)
    if redact:
        analyses = tuple(redact_analysis(item) for item in analyses)

    if all_incidents:
        return [item.to_dict() for item in analyses], 200
    return analyses[0].to_dict(), 200


class IncidentAPIHandler(BaseHTTPRequestHandler):
    server_version = "IncidentAI"

    def _write_json(self, status: int, payload: object) -> None:
        encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(encoded)

    def _write_error(self, status: int, code: str, message: str) -> None:
        self._write_json(status, {"code": code, "error": message})

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/healthz":
            self._write_json(200, {"status": "ok"})
            return
        if self.path == "/version":
            self._write_json(200, {"api_version": API_VERSION, "version": __version__})
            return
        self._write_error(404, "not_found", "not_found")

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/analyze":
            self._write_error(404, "not_found", "not_found")
            return

        content_length = self.headers.get("Content-Length")
        try:
            length = int(content_length) if content_length is not None else -1
        except ValueError:
            length = -1
        max_body_bytes = self.server.max_body_bytes  # type: ignore[attr-defined]
        if length < 0 or length > max_body_bytes:
            self._write_error(413, "request_body_too_large", "request_body_too_large")
            return

        body = self.rfile.read(length)
        if len(body) != length:
            self._write_error(400, "incomplete_request_body", "incomplete_request_body")
            return
        try:
            payload = json.loads(body.decode("utf-8"))
            if not isinstance(payload, dict):
                raise APIError("request body must be a JSON object", "invalid_request_body")
            result, status = _analysis_payload(payload)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            self._write_error(400, "invalid_json", f"invalid_json: {exc}")
            return
        except APIError as exc:
            self._write_error(400, exc.code, str(exc))
            return
        self._write_json(status, result)

    def log_message(self, format: str, *args: object) -> None:
        return


def serve(host: str = "127.0.0.1", port: int = 8080, *, max_body_bytes: int = DEFAULT_MAX_BODY_BYTES) -> None:
    """Run the local IncidentAI HTTP API."""
    if not 1 <= port <= 65535:
        raise ValueError("port must be between 1 and 65535")
    if max_body_bytes <= 0:
        raise ValueError("max_body_bytes must be greater than zero")

    server = ThreadingHTTPServer((host, port), IncidentAPIHandler)
    server.max_body_bytes = max_body_bytes  # type: ignore[attr-defined]
    try:
        server.serve_forever()
    finally:
        server.server_close()
