import pytest

from incident_ai.webhook import MAX_WEBHOOK_RETRIES, WebhookError, send_webhook


def test_send_webhook_rejects_retry_count_above_bound(monkeypatch) -> None:
    with pytest.raises(WebhookError, match=f"between 0 and {MAX_WEBHOOK_RETRIES}"):
        send_webhook({}, "https://example.test/hook", max_retries=MAX_WEBHOOK_RETRIES + 1)


def test_send_webhook_accepts_retry_count_at_bound(monkeypatch) -> None:
    monkeypatch.setattr("incident_ai.webhook._validate_destination", lambda _url: None)
    monkeypatch.setattr("incident_ai.webhook.build_opener", lambda *_handlers: (_ for _ in ()).throw(AssertionError))

    with pytest.raises(AssertionError):
        send_webhook({}, "https://example.test/hook", max_retries=MAX_WEBHOOK_RETRIES)


def test_send_webhook_rejects_boolean_retry_count() -> None:
    with pytest.raises(WebhookError, match="must be an integer"):
        send_webhook({}, "https://example.test/hook", max_retries=True)


def test_send_webhook_rejects_non_positive_timeout() -> None:
    with pytest.raises(WebhookError, match="greater than zero"):
        send_webhook({}, "https://example.test/hook", timeout=0)

    with pytest.raises(WebhookError, match="greater than zero"):
        send_webhook({}, "https://example.test/hook", timeout=-1)
