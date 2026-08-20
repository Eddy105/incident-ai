from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class WebhookError(RuntimeError):
    """Raised when an incident webhook cannot be delivered."""


def send_webhook(payload: object, url: str, *, timeout: float = 10.0) -> None:
    """POST a JSON incident payload to an explicit HTTP(S) webhook URL."""
    if not url.startswith(("https://", "http://")):
        raise WebhookError("webhook URL must use http:// or https://")

    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    request = Request(
        url,
        data=body,
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "IncidentAI/0.10",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=timeout) as response:
            if response.status >= 400:
                raise WebhookError(f"webhook returned HTTP {response.status}")
    except HTTPError as exc:
        raise WebhookError(f"webhook returned HTTP {exc.code}") from exc
    except URLError as exc:
        raise WebhookError(f"webhook delivery failed: {exc.reason}") from exc
    except TimeoutError as exc:
        raise WebhookError("webhook delivery timed out") from exc
