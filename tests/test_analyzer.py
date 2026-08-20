from incident_ai import analyze_text


def test_nginx_upstream_refused_is_detected() -> None:
    analysis = analyze_text(
        'nginx: connect() failed (111: Connection refused) while connecting to upstream'
    )
    assert analysis.incident_type == "nginx_upstream_refused"
    assert analysis.severity == "critical"
    assert analysis.confidence >= 0.95


def test_disk_full_is_detected() -> None:
    analysis = analyze_text("write failed: No space left on device")
    assert analysis.incident_type == "disk_full"
    assert analysis.severity == "critical"


def test_dns_failure_is_detected() -> None:
    analysis = analyze_text("curl: (6) Could not resolve host: api.internal")
    assert analysis.incident_type == "dns_failure"
    assert analysis.severity == "warning"


def test_unknown_input_is_safe() -> None:
    analysis = analyze_text("some completely novel operational failure")
    assert analysis.incident_type == "unknown"
    assert analysis.severity == "info"


def test_empty_input_is_safe() -> None:
    analysis = analyze_text("   \n")
    assert analysis.incident_type == "empty_input"
