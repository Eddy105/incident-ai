# Changelog

All notable changes to this project will be documented here.

## [0.11.2] - 2026-08-20

### Added

- Add deterministic `X-IncidentAI-Event-ID` headers to webhook requests
- Derive event IDs from the exact serialized request body for receiver-side idempotency and duplicate detection
- Add regression coverage for stable and changing event IDs

## [0.11.1] - 2026-08-20

### Security

- Fully redact titles, probable causes, checks, and recommended actions before optional remote OpenAI enrichment
- Add regression coverage proving credentials and identifiers cannot cross the enrichment boundary

## [0.11.0] - 2026-08-20

### Added

- Add stable 16-character SHA-256 incident fingerprints for deduplication and correlation
- Include fingerprints in JSON, grouped JSON, and SARIF output
- Display fingerprints in human-readable incident output
- Add regression coverage for fingerprint stability and separation

## [0.10.2] - 2026-08-20

### Security

- Add optional HMAC-SHA256 authentication for webhook requests via `INCIDENT_AI_WEBHOOK_SECRET`
- Sign the timestamp and exact request body to support receiver-side replay protection
- Keep the secret out of headers and JSON payloads
- Add regression coverage for explicit secrets, environment secrets, and unsigned backward-compatible delivery

## [0.10.1] - 2026-08-20

### Security

- Reject webhook destinations that resolve to non-public IP addresses to reduce SSRF risk
- Reject webhook URLs containing embedded credentials
- Disable automatic HTTP(S) redirects for webhook delivery
- Add regression coverage for private destinations, credentials, and redirects

## [0.10.0] - 2026-08-20
