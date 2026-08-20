from __future__ import annotations

import json
from typing import Literal

InputFormat = Literal["auto", "text", "jsonl"]
_MESSAGE_KEYS = ("MESSAGE", "message", "msg", "log")
_CONTEXT_FIELDS = (
    ("host", ("_HOSTNAME", "hostname", "host")),
    ("service", ("SYSLOG_IDENTIFIER", "service", "app", "application")),
    ("unit", ("_SYSTEMD_UNIT", "unit")),
    ("container", ("CONTAINER_NAME", "container_name", "container")),
    ("pid", ("_PID", "pid")),
)
_CONTEXT_KEYS = {label: keys for label, keys in _CONTEXT_FIELDS}


class InputFormatError(ValueError):
    """Raised when explicitly requested structured input is malformed."""


def _context_value(record: dict[str, object], label: str) -> str | None:
    for key in _CONTEXT_KEYS[label]:
        value = record.get(key)
        if value is None:
            continue
        rendered = str(value).strip()
        if rendered:
            return rendered
    return None


def _context_from_record(record: dict[str, object]) -> str:
    context: list[str] = []
    for label, _keys in _CONTEXT_FIELDS:
        value = _context_value(record, label)
        if value is not None:
            context.append(f"{label}={value.replace(']', '\\]')[:120]}")
    return " ".join(context)


def _record_matches_filters(record: dict[str, object], filters: dict[str, str]) -> bool:
    return all(_context_value(record, label) == expected for label, expected in filters.items())


def _message_from_record(record: dict[str, object], *, include_context: bool = False) -> str:
    message = ""
    for key in _MESSAGE_KEYS:
        value = record.get(key)
        if value is not None:
            message = str(value)
            break
    if not message:
        message = json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    if include_context:
        context = _context_from_record(record)
        if context:
            return f"[{context}] {message}"
    return message


def normalize_input(
    text: str,
    input_format: InputFormat = "auto",
    *,
    include_context: bool = False,
    source_filters: dict[str, str] | None = None,
) -> str:
    """Normalize raw text or JSON Lines records into analyzer-friendly text."""
    filters = {key: value for key, value in (source_filters or {}).items() if value}
    if input_format == "text" or not text.strip():
        if filters:
            raise InputFormatError("source filters require JSON Lines input")
        return text

    records: list[dict[str, object]] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            if input_format == "auto" and not filters:
                return text
            raise InputFormatError(f"invalid JSON on line {line_number}: {exc.msg}") from exc

        if not isinstance(value, dict):
            if input_format == "auto" and not filters:
                return text
            raise InputFormatError(f"JSON line {line_number} must contain an object")
        records.append(value)

    if filters:
        records = [record for record in records if _record_matches_filters(record, filters)]

    return "\n".join(_message_from_record(record, include_context=include_context) for record in records)
