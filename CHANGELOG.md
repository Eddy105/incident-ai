# Changelog

All notable changes to this project will be documented here.

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

### Added
