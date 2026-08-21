from email.utils import formatdate
from urllib.error import HTTPError

from incident_ai.webhook import _retry_after_delay, send_webhook


class _Response:
    status = 202

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


class _Opener:
    def __init__(self, response=None, error=None) -> None:
        self.response = response
        self.error = error

    def open(self, request, timeout):
        if self.error:
            raise self.error
        return self.response


def _public_dns(monkeypatch) -> None:
    monkeypatch.setattr(
        "incident_ai.webhook.socket.getaddrinfo",
        lambda *_args, **_kwargs: [(2, 1, 6, "", ("93.184.216.34", 443))],
    )


def test_retry_after_http_date_is_converted_to_delay(monkeypatch) -> None:
    monkeypatch.setattr("incident_ai.webhook.time.time", lambda: 1_700_000_000)
    value = formatdate(1_700_000_005, usegmt=True)

    assert _retry_after_delay(value) == 5.0


def test_retry_after_past_http_date_falls_back_to_backoff(monkeypatch) -> None:
    monkeypatch.setattr("incident_ai.webhook.time.time", lambda: 1_700_000_010)
    value = formatdate(1_700_000_005, usegmt=True)

    assert _retry_after_delay(value) is None


def test_send_webhook_honors_http_date_retry_after(monkeypatch) -> None:
    _public_dns(monkeypatch)
    monkeypatch.setattr("incident_ai.webhook.time.time", lambda: 1_700_000_000)
    headers = {"Retry-After": formatdate(1_700_000_007, usegmt=True)}
    first = _Opener(error=HTTPError("https://example.test/hook", 429, "rate limited", headers, None))
    second = _Opener(_Response())
    openers = iter((first, second))
    monkeypatch.setattr("incident_ai.webhook.build_opener", lambda *_handlers: next(openers))
    sleeps = []
    monkeypatch.setattr("incident_ai.webhook.time.sleep", sleeps.append)

    send_webhook({"incident_type": "rate_limited"}, "https://example.test/hook", max_retries=1)

    assert sleeps == [7.0]
