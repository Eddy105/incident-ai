from __future__ import annotations

import re

_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"), "<EMAIL>"),
    (re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"), "<IP>"),
    (
        re.compile(
            r"(?i)\b(api[_-]?key|token|password|passwd|secret|authorization)\b"
            r"\s*[:=]\s*([^\s,;]+)"
        ),
        r"\1=<REDACTED>",
    ),
    (re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b"), "<API_KEY>"),
    (re.compile(r"(?i)bearer\s+[A-Za-z0-9._~+/=-]{12,}"), "Bearer <REDACTED>"),
)


def redact_text(text: str) -> str:
    """Redact common secrets and identifiers before optional remote enrichment."""
    redacted = text
    for pattern, replacement in _PATTERNS:
        redacted = pattern.sub(replacement, redacted)
    return redacted
