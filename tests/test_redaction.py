from incident_ai import analyze_text
from incident_ai.enrichment import build_enrichment_input
from incident_ai.redaction import redact_text


def test_redacts_common_secrets_and_identifiers() -> None:
    text = "user=a@example.com ip=10.0.0.5 token=super-secret-value password=hunter2"
    redacted = redact_text(text)
    assert "a@example.com" not in redacted
    assert "10.0.0.5" not in redacted
    assert "super-secret-value" not in redacted
    assert "hunter2" not in redacted


def test_enrichment_payload_uses_only_structured_analysis() -> None:
    analysis = analyze_text(
        "client 10.0.0.5 failed: Permission denied token=super-secret-value"
    )
    payload = build_enrichment_input(analysis)
    assert "10.0.0.5" not in payload
    assert "super-secret-value" not in payload
    assert "permission_denied" in payload
