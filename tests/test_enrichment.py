import json

from incident_ai.enrichment import build_enrichment_input
from incident_ai.models import IncidentAnalysis


def test_build_enrichment_input_redacts_all_exported_fields() -> None:
    analysis = IncidentAnalysis(
        incident_type="permission_denied",
        title="Access denied for admin@example.com from 10.20.30.40",
        severity="warning",
        confidence=0.93,
        probable_cause="password=supersecret token=abc123 and API key sk-abcdefghijklmnopqrstuvwxyz",
        evidence=("Authorization: Bearer verylongcredentialvalue",),
        checks=("Contact admin@example.com at 10.20.30.40",),
        recommended_actions=("Rotate secret=topsecret before retrying",),
    )

    payload = json.loads(build_enrichment_input(analysis))
    serialized = json.dumps(payload, ensure_ascii=False)

    assert "admin@example.com" not in serialized
    assert "10.20.30.40" not in serialized
    assert "supersecret" not in serialized
    assert "abc123" not in serialized
    assert "abcdefghijklmnopqrstuvwxyz" not in serialized
    assert "verylongcredentialvalue" not in serialized
    assert "topsecret" not in serialized
    assert "<EMAIL>" in serialized
    assert "<IP>" in serialized
    assert "<REDACTED>" in serialized
