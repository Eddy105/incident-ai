# Incident fingerprints

IncidentAI assigns every `IncidentAnalysis` a stable 16-character hexadecimal fingerprint. The fingerprint is derived from the incident type, title, and probable cause and is independent of the matching evidence lines.

## Purpose

Fingerprints are intended for:

- deduplicating repeated alerts
- correlating the same incident across webhook deliveries
- grouping incidents in ServerWatch or future API integrations
- creating stable keys for downstream automation

The fingerprint is exposed in JSON, grouped JSON, SARIF result properties, and human-readable output.

## Stability

Equivalent analyses produced by the same rule receive the same fingerprint even when their evidence differs. Different incident types produce different fingerprints. The value is not a secret and should not be treated as an authentication credential.

Example JSON field:

```json
{
  "incident_type": "disk_full",
  "fingerprint": "0123456789abcdef"
}
```

The current implementation uses the first 16 hexadecimal characters of a SHA-256 digest over the incident type, title, and probable cause. This provides a compact identifier while retaining deterministic behavior across processes and machines.
