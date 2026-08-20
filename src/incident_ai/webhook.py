from __future__ import annotations

import hashlib
import hmac
import ipaddress
import json
import os
import socket
import time
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


def _signature_headers(body: bytes, secret: str | None, timestamp: int) -> dict[str, str]:
    if not secret:
        return {}
    signed_payload = f"{timestamp}.".encode("ascii") + body
    signature = hmac.new(secret.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()
    return {
        "X-IncidentAI-Timestamp": str(timestamp),
        "X-IncidentAI-Signature": f"sha256={signature}",
    }


def _retry_delay(attempt: int) -> float:
    return min(0.5 * (2**attempt), 4.0)


def _should_retry_http(status: int) -> bool:
    return status == 429 or 500 <= status < 600


def send_webhook(
    payload: object,
    url: str,
    *,
    timeout: float = 10.0,
    secret: str | None = None,
    max_retries: int = 0,
) -> None:
    """POST JSON to a public webhook with optional bounded retries."""
    if max_retries < 0:
        raise WebhookError("webhook max_retries must be zero or greater")
    _validate_destination(url)

    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    event_id = hashlib.sha256(body).hexdigest()
    signing_secret = secret if secret is not None else os.environ.get("INCIDENT_AI_WEBHOOK_SECRET")
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "IncidentAI/0.11",
        "X-IncidentAI-Event-ID": event_id,
    }

    for attempt in range(max_retries + 1):
        timestamp = int(time.time())
        request_headers = {**headers, **_signature_headers(body, signing_secret, timestamp)}
        request = Request(url, data=body, headers=request_headers, method="POST")
        try:
            opener = build_opener(_NoRedirectHandler())
            with opener.open(request, timeout=timeout) as response:
                if response.status >= 400:
                    if _should_retry_http(response.status) and attempt < max_retries:
                        time.sleep(_retry_delay(attempt))
                        continue
                    raise WebhookError(f"webhook returned HTTP {response.status}")
                return
        except HTTPError as exc:
            if 300 <= exc.code < 400:
                raise WebhookError("webhook redirects are not allowed") from exc
            if _should_retry_http(exc.code) and attempt < max_retries:
                time.sleep(_retry_delay(attempt))
                continue
            raise WebhookError(f"webhook returned HTTP {exc.code}") from exc
        except URLError as exc:
            if attempt < max_retries:
                time.sleep(_retry_delay(attempt))
                continue
            raise WebhookError(f"webhook delivery failed: {exc.reason}") from exc
        except TimeoutError as exc:
            if attempt < max_retries:
                time.sleep(_retry_delay(attempt))
                continue
            raise WebhookError("webhook delivery timed out") from exc

    raise WebhookError("webhook delivery failed after retries")
