import json
import threading
import urllib.error
import urllib.request

from incident_ai.server import IncidentAPIHandler, ThreadingHTTPServer


def _running_server(max_body_bytes: int = 1024 * 1024):
    server = ThreadingHTTPServer(("127.0.0.1", 0), IncidentAPIHandler)
    server.max_body_bytes = max_body_bytes
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def _request(server, method: str, path: str, body: object | None = None):
    url = f"http://127.0.0.1:{server.server_port}{path}"
    data = None if body is None else json.dumps(body).encode("utf-8")
    request = urllib.request.Request(url, data=data, method=method)
    if data is not None:
        request.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(request, timeout=2) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read())


def test_health_endpoint() -> None:
    server, thread = _running_server()
    try:
        status, payload = _request(server, "GET", "/healthz")
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert status == 200
    assert payload == {"status": "ok"}


def test_analyze_endpoint_returns_structured_incident() -> None:
    server, thread = _running_server()
    try:
        status, payload = _request(
            server,
            "POST",
            "/analyze",
            {"log": "Permission denied", "redact": True},
        )
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert status == 200
    assert payload["incident_type"] == "permission_denied"
    assert payload["fingerprint"]


def test_analyze_endpoint_supports_all() -> None:
    server, thread = _running_server()
    try:
        status, payload = _request(
            server,
            "POST",
            "/analyze",
            {"log": "Permission denied\nNo space left on device", "all": True},
        )
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert status == 200
    assert [item["incident_type"] for item in payload] == ["disk_full", "permission_denied"]


def test_analyze_endpoint_rejects_oversized_body() -> None:
    server, thread = _running_server(max_body_bytes=32)
    try:
        status, payload = _request(server, "POST", "/analyze", {"log": "Permission denied"})
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert status == 413
    assert payload["error"] == "request_body_too_large"


def test_analyze_endpoint_rejects_invalid_payload() -> None:
    server, thread = _running_server()
    try:
        status, payload = _request(server, "POST", "/analyze", {"log": 123})
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert status == 400
    assert payload["error"] == "'log' must be a string"


def test_unknown_endpoint_is_not_found() -> None:
    server, thread = _running_server()
    try:
        status, payload = _request(server, "GET", "/missing")
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert status == 404
    assert payload == {"error": "not_found"}
