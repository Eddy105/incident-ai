import hashlib
import hmac
import json
from urllib.error import HTTPError

import pytest

from incident_ai.webhook import WebhookError, send_webhook


class _Response:
    def __init__(self, status: int = 202) -> None:
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


class _Opener:
    def __init__(self, response=None, error=None) -> None:
        self.response = response
        self.error = error
        self.request = None
        self.timeout = None

    def open(self, request, timeout):
        self.request = request
        self.timeout = timeout
        if self.error:
            raise self.error
        return self.response


def _public_dns(monkeypatch) -> None:
    monkeypatch.setattr(
        "incident_ai.webhook.socket.getaddrinfo",
        lambda *_args, **_kwargs: [(2, 1, 6, "", ("93.184.216.34", 443))],
    )


def test_send_webhook_posts_json(monkeypatch) -> None:
    _public_dns(monkeypatch)
    captured = {}
    opener = _Opener(_Response())

    def fake_build_opener(*_handlers):
        return opener

    monkeypatch.setattr("incident_ai.webhook.build_opener", fake_build_opener)

    send_webhook({"incident_type": "disk_full"}, "https://example.test/hook", timeout=3.5)

    captured["url"] = opener.request.full_url
    captured["body"] = opener.request.data
    captured["content_type"] = opener.request.get_header("Content-type")
    captured["user_agent"] = opener.request.get_header("User-agent")
    captured["event_id"] = opener.request.get_header("X-incidentai-event-id")
    captured["timeout"] = opener.timeout

    assert captured["url"] == "https://example.test/hook"
    assert json.loads(captured["body"]) == {"incident_type": "disk_full"}
    assert captured["content_type"] == "application/json"
    assert captured["user_agent"] == "IncidentAI/0.11"
    assert captured["event_id"] == hashlib.sha256(captured["body"]).hexdigest()
    assert captured["timeout"] == 3.5


def test_send_webhook_event_id_is_stable_for_same_payload(monkeypatch) -> None:
    _public_dns(monkeypatch)
    openers = [_Opener(_Response()), _Opener(_Response())]
    monkeypatch.setattr("incident_ai.webhook.build_opener", lambda *_handlers: openers.pop(0))

    first = _Opener(_Response())
    second = _Opener(_Response())
    openers.extend([first, second])

    send_webhook({"incident_type": "oom", "fingerprint": "abc123"}, "https://example.test/hook")
    first_id = openers[0].request.get_header("X-incidentai-event-id") if openers[0].request else None

    send_webhook({"incident_type": "oom", "fingerprint": "abc123"}, "https://example.test/hook")
    second_id = openers[1].request.get_header("X-incidentai-event-id") if openers[1].request else None

    assert first_id is not None
    assert first_id == second_id


def test_send_webhook_event_id_changes_with_payload(monkeypatch) -> None:
    _public_dns(monkeypatch)
    openers = [_Opener(_Response()), _Opener(_Response())]
    monkeypatch.setattr("incident_ai.webhook.build_opener", lambda *_handlers: openers.pop(0))

    first = openers[0]
    openers.append(first)
    send_webhook({"incident_type": "oom"}, "https://example.test/hook")
    first_id = first.request.get_header("X-incidentai-event-id")

    second = openers[0]
    send_webhook({"incident_type": "disk_full"}, "https://example.test/hook")
    second_id = second.request.get_header("X-incidentai-event-id")

    assert first_id != second_id


def test_send_webhook_signs_payload(monkeypatch) -> None:
    _public_dns(monkeypatch)
    monkeypatch.setattr("incident_ai.webhook.time.time", lambda: 1_700_000_000)
    opener = _Opener(_Response())
    monkeypatch.setattr("incident_ai.webhook.build_opener", lambda *_handlers: opener)

    send_webhook({"incident_type": "disk_full"}, "https://example.test/hook", secret="top-secret")

    body = opener.request.data
    signed = "1700000000.".encode("ascii") + body
    expected = hmac.new(b"top-secret", signed, hashlib.sha256).hexdigest()

    assert opener.request.get_header("X-incidentai-timestamp") == "1700000000"
    assert opener.request.get_header("X-incidentai-signature") == f"sha256={expected}"
    assert opener.request.get_header("X-incidentai-event-id") == hashlib.sha256(body).hexdigest()


def test_send_webhook_uses_environment_secret(monkeypatch) -> None:
    _public_dns(monkeypatch)
    monkeypatch.setenv("INCIDENT_AI_WEBHOOK_SECRET", "env-secret")
    monkeypatch.setattr("incident_ai.webhook.time.time", lambda: 1_700_000_001)
    opener = _Opener(_Response())
    monkeypatch.setattr("incident_ai.webhook.build_opener", lambda *_handlers: opener)

    send_webhook({"incident_type": "oom"}, "https://example.test/hook")

    body = opener.request.data
    signed = "1700000001.".encode("ascii") + body
    expected = hmac.new(b"env-secret", signed, hashlib.sha256).hexdigest()

    assert opener.request.get_header("X-incidentai-signature") == f"sha256={expected}"


def test_send_webhook_has_no_signature_without_secret(monkeypatch) -> None:
    _public_dns(monkeypatch)
    monkeypatch.delenv("INCIDENT_AI_WEBHOOK_SECRET", raising=False)
    opener = _Opener(_Response())
    monkeypatch.setattr("incident_ai.webhook.build_opener", lambda *_handlers: opener)

    send_webhook({"incident_type": "oom"}, "https://example.test/hook")

    assert opener.request.get_header("X-incidentai-signature") is None
    assert opener.request.get_header("X-incidentai-timestamp") is None


def test_send_webhook_rejects_non_http_url() -> None:
    with pytest.raises(WebhookError, match="http:// or https://"):
        send_webhook({}, "file:///tmp/incident.json")


def test_send_webhook_rejects_private_destination(monkeypatch) -> None:
    monkeypatch.setattr(
        "incident_ai.webhook.socket.getaddrinfo",
        lambda *_args, **_kwargs: [(2, 1, 6, "", ("127.0.0.1", 80))],
    )

    with pytest.raises(WebhookError, match="public IP"):
        send_webhook({}, "http://localhost/hook")


def test_send_webhook_rejects_embedded_credentials(monkeypatch) -> None:
    _public_dns(monkeypatch)

    with pytest.raises(WebhookError, match="embedded credentials"):
        send_webhook({}, "https://user:secret@example.test/hook")


def test_send_webhook_rejects_redirects(monkeypatch) -> None:
    _public_dns(monkeypatch)
    opener = _Opener(error=HTTPError("https://example.test/hook", 302, "redirect", {}, None))
    monkeypatch.setattr("incident_ai.webhook.build_opener", lambda *_handlers: opener)

    with pytest.raises(WebhookError, match="redirects are not allowed"):
        send_webhook({}, "https://example.test/hook")


def test_send_webhook_reports_http_errors(monkeypatch) -> None:
    _public_dns(monkeypatch)
    opener = _Opener(error=HTTPError("https://example.test/hook", 500, "server error", {}, None))
    monkeypatch.setattr("incident_ai.webhook.build_opener", lambda *_handlers: opener)

    with pytest.raises(WebhookError, match="HTTP 500"):
        send_webhook({}, "https://example.test/hook")
