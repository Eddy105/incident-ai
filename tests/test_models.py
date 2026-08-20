from incident_ai import analyze_text


def test_fingerprint_is_stable_for_equivalent_incidents() -> None:
    first = analyze_text("write failed: No space left on device")
    second = analyze_text("another write failed: No space left on device")

    assert first.fingerprint == second.fingerprint
    assert len(first.fingerprint) == 16
    assert first.fingerprint in first.to_dict().values()


def test_fingerprint_changes_for_different_incident_types() -> None:
    disk = analyze_text("write failed: No space left on device")
    dns = analyze_text("curl: (6) Could not resolve host: api.internal")

    assert disk.fingerprint != dns.fingerprint
