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


def test_version_endpoint_exposes_api_and_package_version() -> None:
    server, thread = _running_server()
    try:
        status, payload = _request(server, "GET", "/version")
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert status == 200
    assert payload == {"api_version": "1", "version": "0.14.0"}


def test_capabilities_endpoint_exposes_integration_contract() -> None:
    server, thread = _running_server(max_body_bytes=2048)
    try:
        status, payload = _request(server, "GET", "/capabilities")
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert status == 200
    assert payload["api_version"] == "1"
    assert payload["version"] == "0.14.0"
    assert payload["endpoints"] == ["/healthz", "/version", "/capabilities", "/analyze"]
    assert "multi_incident" in payload["features"]
    assert "stable_error_codes" in payload["features"]
    assert "stable_fingerprints" in payload["features"]
    assert payload["limits"] == {"max_body_bytes": 2048}


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
        status, payload = _request(server, "POST", "/analyze", {"log": "x" * 64})
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert status == 413
    assert payload == {"code": "request_body_too_large", "error": "request_body_too_large"}


def test_analyze_endpoint_rejects_invalid_payload() -> None:
    server, thread = _running_server()
    try:
        status, payload = _request(server, "POST", "/analyze", {"log": 123})
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert status == 400
    assert payload == {"code": "invalid_log", "error": "'log' must be a string"}


def test_analyze_endpoint_rejects_invalid_json_with_stable_code() -> None:
    server, thread = _running_server()
    url = f"http://127.0.0.1:{server.server_port}/analyze"
    request = urllib.request.Request(url, data=b"{not-json}", method="POST")
    request.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(request, timeout=2) as response:
            status = response.status
            payload = json.loads(response.read())
    except urllib.error.HTTPError as exc:
        status = exc.code
        payload = json.loads(exc.read())
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert status == 400
    assert payload["code"] == "invalid_json"
    assert payload["error"].startswith("invalid_json:")


def test_unknown_endpoint_is_not_found() -> None:
    server, thread = _running_server()
    try:
        status, payload = _request(server, "GET", "/missing")
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert status == 404
    assert payload == {"code": "not_found", "error": "not_found"}
