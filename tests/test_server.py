import http.client
import json
import threading
import urllib.error
import urllib.request

from incident_ai.server import IncidentAPIHandler, Metrics, ThreadingHTTPServer


def _running_server(max_body_bytes: int = 1024 * 1024, max_concurrent_requests: int = 16):
    server = ThreadingHTTPServer(("127.0.0.1", 0), IncidentAPIHandler)
    server.max_body_bytes = max_body_bytes
    server.max_concurrent_requests = max_concurrent_requests
    server.request_semaphore = threading.BoundedSemaphore(max_concurrent_requests)
    server.metrics = Metrics()
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def _request(server, method: str, path: str, body: object | None = None, content_type: str | None = None):
    url = f"http://127.0.0.1:{server.server_port}{path}"
    data = None if body is None else json.dumps(body).encode("utf-8")
    request = urllib.request.Request(url, data=data, method=method)
    if data is not None and content_type is not None:
        request.add_header("Content-Type", content_type)
    try:
        with urllib.request.urlopen(request, timeout=2) as response:
            body = response.read()
            if response.headers.get_content_type() == "application/json":
                body = json.loads(body)
            return response.status, body, response.headers
    except urllib.error.HTTPError as exc:
        body = exc.read()
        if exc.headers.get_content_type() == "application/json":
            body = json.loads(body)
        return exc.code, body, exc.headers


def test_health_endpoint():
    server, thread = _running_server()
    try:
        status, payload, headers = _request(server, "GET", "/healthz")
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert status == 200
    assert payload == {"status": "ok"}
    assert len(headers["X-IncidentAI-Request-ID"]) == 32


def test_request_ids_are_unique_per_request():
    server, thread = _running_server()
    try:
        first = _request(server, "GET", "/healthz")[2]["X-IncidentAI-Request-ID"]
        second = _request(server, "GET", "/healthz")[2]["X-IncidentAI-Request-ID"]
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert first != second


def test_error_responses_include_request_id():
    server, thread = _running_server()
    try:
        status, payload, headers = _request(server, "GET", "/missing")
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert status == 404
    assert payload == {"code": "not_found", "error": "not_found"}
    assert len(headers["X-IncidentAI-Request-ID"]) == 32


def test_version_endpoint_exposes_api_and_package_version():
    server, thread = _running_server()
    try:
        status, payload, _ = _request(server, "GET", "/version")
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert status == 200
    assert payload == {"api_version": "1", "version": "0.19.0"}


def test_capabilities_endpoint_exposes_integration_contract():
    server, thread = _running_server(max_body_bytes=2048, max_concurrent_requests=4)
    try:
        status, payload, _ = _request(server, "GET", "/capabilities")
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert status == 200
    assert payload["api_version"] == "1"
    assert payload["version"] == "0.19.0"
    assert payload["endpoints"] == ["/healthz", "/version", "/capabilities", "/openapi.json", "/metrics", "/analyze"]
    assert "multi_incident" in payload["features"]
    assert "stable_error_codes" in payload["features"]
    assert "stable_fingerprints" in payload["features"]
    assert "bounded_concurrency" in payload["features"]
    assert "content_type_validation" in payload["features"]
    assert "openapi_discovery" in payload["features"]
    assert "request_ids" in payload["features"]
    assert "prometheus_metrics" in payload["features"]
    assert payload["limits"] == {"max_body_bytes": 2048, "max_concurrent_requests": 4}


def test_openapi_endpoint_exposes_local_api_contract():
    server, thread = _running_server()
    try:
        status, payload, _ = _request(server, "GET", "/openapi.json")
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert status == 200
    assert payload["openapi"] == "3.0.3"
    assert payload["info"]["version"] == "0.19.0"
    assert set(payload["paths"]) == {"/healthz", "/version", "/capabilities", "/openapi.json", "/metrics", "/analyze"}
    assert payload["paths"]["/analyze"]["post"]["requestBody"]["content"]["application/json"]


def test_metrics_endpoint_exposes_prometheus_counters():
    server, thread = _running_server()
    try:
        _request(server, "GET", "/healthz")
        _request(server, "GET", "/missing")
        status, body, headers = _request(server, "GET", "/metrics")
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    text = body.decode("utf-8")
    assert status == 200
    assert headers.get_content_type() == "text/plain"
    assert "# TYPE incident_ai_http_requests_total counter" in text
    assert 'incident_ai_http_requests_total{method="GET",path="/healthz",status="200"} 1' in text
    assert 'incident_ai_http_requests_total{method="GET",path="/missing",status="404"} 1' in text
    assert 'incident_ai_http_requests_total{method="GET",path="/metrics",status="200"} 1' not in text
    assert len(headers["X-IncidentAI-Request-ID"]) == 32


def test_metrics_bound_unknown_path_cardinality():
    server, thread = _running_server()
    try:
        _request(server, "GET", "/unknown-path-a")
        _request(server, "GET", "/unknown-path-b")
        status, body, _ = _request(server, "GET", "/metrics")
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    text = body.decode("utf-8")
    assert status == 200
    assert 'incident_ai_http_requests_total{method="GET",path="/unknown",status="404"} 2' in text
    assert "/unknown-path-a" not in text
    assert "/unknown-path-b" not in text


def test_analyze_endpoint_rejects_when_concurrency_limit_is_reached():
    server, thread = _running_server(max_concurrent_requests=1)
    assert server.request_semaphore.acquire(blocking=False)
    try:
        status, payload, headers = _request(server, "POST", "/analyze", {"log": "Permission denied"}, "application/json")
    finally:
        server.request_semaphore.release()
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert status == 429
    assert payload == {"code": "concurrency_limit_reached", "error": "concurrency_limit_reached"}
    assert len(headers["X-IncidentAI-Request-ID"]) == 32


def test_analyze_endpoint_returns_structured_incident():
    server, thread = _running_server()
    try:
        status, payload, headers = _request(
            server,
            "POST",
            "/analyze",
            {"log": "Permission denied", "redact": True},
            "application/json",
        )
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert status == 200
    assert payload["incident_type"] == "permission_denied"
    assert payload["fingerprint"]
    assert len(headers["X-IncidentAI-Request-ID"]) == 32


def test_analyze_endpoint_supports_all():
    server, thread = _running_server()
    try:
        status, payload, _ = _request(
            server,
            "POST",
            "/analyze",
            {"log": "Permission denied\nNo space left on device", "all": True},
            "application/json",
        )
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert status == 200
    assert [item["incident_type"] for item in payload] == ["disk_full", "permission_denied"]


def test_analyze_endpoint_rejects_oversized_body():
    server, thread = _running_server(max_body_bytes=32)
    try:
        status, payload, _ = _request(server, "POST", "/analyze", {"log": "x" * 64}, "application/json")
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert status == 413
    assert payload == {"code": "request_body_too_large", "error": "request_body_too_large"}


def test_analyze_endpoint_rejects_invalid_payload():
    server, thread = _running_server()
    try:
        status, payload, _ = _request(server, "POST", "/analyze", {"log": 123}, "application/json")
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert status == 400
    assert payload == {"code": "invalid_log", "error": "'log' must be a string"}


def test_analyze_endpoint_rejects_invalid_json_with_stable_code():
    server, thread = _running_server()
    url = f"http://127.0.0.1:{server.server_port}/analyze"
    request = urllib.request.Request(url, data=b"{not-json}", method="POST")
    request.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(request, timeout=2) as response:
            status = response.status
            payload = json.loads(response.read())
            headers = response.headers
    except urllib.error.HTTPError as exc:
        status = exc.code
        payload = json.loads(exc.read())
        headers = exc.headers
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert status == 400
    assert payload["code"] == "invalid_json"
    assert payload["error"].startswith("invalid_json:")
    assert len(headers["X-IncidentAI-Request-ID"]) == 32


def test_analyze_endpoint_rejects_unsupported_media_type():
    server, thread = _running_server()
    try:
        status, payload, _ = _request(
            server,
            "POST",
            "/analyze",
            {"log": "Permission denied"},
            "text/plain; charset=utf-8",
        )
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert status == 415
    assert payload == {"code": "unsupported_media_type", "error": "unsupported_media_type"}


def test_analyze_endpoint_allows_legacy_missing_content_type():
    server, thread = _running_server()
    try:
        connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=2)
        connection.putrequest("POST", "/analyze")
        body = json.dumps({"log": "Permission denied"}).encode("utf-8")
        connection.putheader("Content-Length", str(len(body)))
        connection.endheaders(body)
        response = connection.getresponse()
        status = response.status
        payload = json.loads(response.read())
        headers = response.headers
        connection.close()
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert status == 200
    assert payload["incident_type"] == "permission_denied"
    assert len(headers["X-IncidentAI-Request-ID"]) == 32


def test_unknown_endpoint_is_not_found():
    server, thread = _running_server()
    try:
        status, payload, _ = _request(server, "GET", "/missing")
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert status == 404
    assert payload == {"code": "not_found", "error": "not_found"}
