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


def test_send_webhook_posts_json(monkeypatch) -> None:
    captured = {}

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["body"] = request.data
        captured["content_type"] = request.get_header("Content-type")
        captured["user_agent"] = request.get_header("User-agent")
        captured["timeout"] = timeout
        return _Response()

    monkeypatch.setattr("incident_ai.webhook.urlopen", fake_urlopen)

    send_webhook({"incident_type": "disk_full"}, "https://example.test/hook", timeout=3.5)

    assert captured["url"] == "https://example.test/hook"
    assert json.loads(captured["body"]) == {"incident_type": "disk_full"}
    assert captured["content_type"] == "application/json"
    assert captured["user_agent"] == "IncidentAI/0.10"
    assert captured["timeout"] == 3.5


def test_send_webhook_rejects_non_http_url() -> None:
    with pytest.raises(WebhookError, match="http:// or https://"):
        send_webhook({}, "file:///tmp/incident.json")


def test_send_webhook_reports_http_errors(monkeypatch) -> None:
    def fake_urlopen(*_args, **_kwargs):
        raise HTTPError("https://example.test/hook", 500, "server error", {}, None)

    monkeypatch.setattr("incident_ai.webhook.urlopen", fake_urlopen)

    with pytest.raises(WebhookError, match="HTTP 500"):
        send_webhook({}, "https://example.test/hook")
