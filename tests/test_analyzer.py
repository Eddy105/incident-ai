from incident_ai import analyze_all, analyze_text


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


def test_analyze_all_returns_distinct_incidents_by_confidence() -> None:
    analyses = analyze_all(
        "write failed: No space left on device\n"
        "curl: (6) Could not resolve host: api.internal\n"
        "another write failed: No space left on device"
    )

    assert [item.incident_type for item in analyses] == ["disk_full", "dns_failure"]
    assert analyses[0].confidence >= analyses[1].confidence
    assert len(analyses[0].evidence) == 2


def test_corroborating_oom_signal_raises_confidence() -> None:
    baseline = analyze_text("Killed process 123 (worker) total-vm:123456kB")
    corroborated = analyze_text(
        "worker invoked oom-killer\n"
        "Killed process 123 (worker) total-vm:123456kB"
    )

    assert baseline.incident_type == "oom_kill"
    assert baseline.confidence == 0.98
    assert corroborated.incident_type == "oom_kill"
    assert corroborated.confidence == 0.99


def test_corroborating_signals_do_not_create_an_incident_without_primary_match() -> None:
    analysis = analyze_text("worker invoked oom-killer")

    assert analysis.incident_type == "unknown"
    assert analysis.confidence == 0.20


def test_corroborating_confidence_is_capped() -> None:
    analysis = analyze_text(
        "worker invoked oom-killer\n"
        "memory cgroup out of memory\n"
        "oom_reaper: reaped process 123\n"
        "Killed process 123 (worker) total-vm:123456kB"
    )

    assert analysis.incident_type == "oom_kill"
    assert analysis.confidence == 0.99


def test_unknown_input_is_safe() -> None:
    analysis = analyze_text("some completely novel operational failure")
    assert analysis.incident_type == "unknown"
    assert analysis.severity == "info"


def test_empty_input_is_safe() -> None:
    analysis = analyze_text("   \n")
    assert analysis.incident_type == "empty_input"
