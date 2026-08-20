from __future__ import annotations

import json
from typing import Literal

InputFormat = Literal["auto", "text", "jsonl"]
_MESSAGE_KEYS = ("MESSAGE", "message", "msg", "log")


class InputFormatError(ValueError):
    """Raised when explicitly requested structured input is malformed."""


def _message_from_record(record: dict[str, object]) -> str:
    for key in _MESSAGE_KEYS:
        value = record.get(key)
        if value is not None:
            return str(value)
    return json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def normalize_input(text: str, input_format: InputFormat = "auto") -> str:
    """Normalize raw text or JSON Lines records into analyzer-friendly text."""
    if input_format == "text" or not text.strip():
        return text

    records: list[dict[str, object]] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            if input_format == "auto":
                return text
            raise InputFormatError(f"invalid JSON on line {line_number}: {exc.msg}") from exc

        if not isinstance(value, dict):
            if input_format == "auto":
                return text
            raise InputFormatError(f"JSON line {line_number} must contain an object")
        records.append(value)

    return "\n".join(_message_from_record(record) for record in records)
