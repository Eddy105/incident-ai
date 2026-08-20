from __future__ import annotations

import ipaddress
import json
import socket
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


class WebhookError(RuntimeError):
    """Raised when an incident webhook cannot be delivered."""


class _NoRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, *_args, **_kwargs):
        return None


def _validate_destination(url: str) -> None:
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"}:
        raise WebhookError("webhook URL must use http:// or https://")
    if parsed.username or parsed.password:
        raise WebhookError("webhook URL must not contain embedded credentials")
    if not parsed.hostname:
        raise WebhookError("webhook URL must contain a hostname")

    try:
        addresses = socket.getaddrinfo(parsed.hostname, parsed.port, type=socket.SOCK_STREAM)
    except OSError as exc:
        raise WebhookError(f"webhook hostname could not be resolved: {exc}") from exc

    for address in {item[4][0] for item in addresses}:
        try:
            ip = ipaddress.ip_address(address)
        except ValueError as exc:
            raise WebhookError("webhook hostname resolved to an invalid IP address") from exc
        if not ip.is_global:
            raise WebhookError("webhook destination must resolve only to public IP addresses")


def send_webhook(payload: object, url: str, *, timeout: float = 10.0) -> None:
    """POST a JSON incident payload to a public HTTP(S) webhook URL."""
    _validate_destination(url)

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
        opener = build_opener(_NoRedirectHandler())
        with opener.open(request, timeout=timeout) as response:
            if response.status >= 400:
                raise WebhookError(f"webhook returned HTTP {response.status}")
    except HTTPError as exc:
        if 300 <= exc.code < 400:
            raise WebhookError("webhook redirects are not allowed") from exc
        raise WebhookError(f"webhook returned HTTP {exc.code}") from exc
    except URLError as exc:
        raise WebhookError(f"webhook delivery failed: {exc.reason}") from exc
    except TimeoutError as exc:
        raise WebhookError("webhook delivery timed out") from exc
