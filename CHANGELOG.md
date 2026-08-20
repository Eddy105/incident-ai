# Changelog

All notable changes to this project will be documented here.

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

### Added

- Add opt-in HTTP(S) webhook export for structured incident analysis
- Require `--redact` for webhook delivery to prevent accidental secret disclosure
- Add explicit integration failure exit code `4`

## [0.9.0] - 2026-08-20

### Added

- Add opt-in redaction for exported incident analysis
- Redact common secrets and identifiers from text, JSON, grouped JSON, and SARIF output
- Add regression coverage for redaction behavior

## [0.8.0] - 2026-08-20

### Added

- Add SARIF 2.1.0 output for CI and security tooling
- Include incident fingerprints, confidence, evidence, checks, and recommended actions as SARIF properties

## [0.7.0] - 2026-08-20

### Added

- Add source-grouped cross-record correlation with `--group-by`
- Prevent cross-source confidence correlation when records belong to different hosts, services, units, or containers

## [0.6.0] - 2026-08-20

### Added

- Add source-scoping filters for host, service, systemd unit, and container
- Preserve structured source context in incident evidence

## [0.5.0] - 2026-08-20

### Added

- Add correlated confidence scoring for independent supporting incident signals

## [0.4.0] - 2026-08-20

### Added

- Preserve host, service, unit, container, and PID context from structured logs

## [0.3.0] - 2026-08-20

### Added

- Add JSON Lines ingestion for journald, container, and application logs
- Add automatic, strict, and explicit input format selection

## [0.2.0] - 2026-08-20

### Added

- Add multi-incident analysis with `analyze_all()` and `--all`

## [0.1.0] - 2026-08-20

### Added

- Initial deterministic Linux and service incident analysis
- CLI, JSON output, Docker image, CI, tests, and automatic releases
