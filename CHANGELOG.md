# Changelog

All notable changes to this project will be documented here.

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

- Secure opt-in `--webhook` export for posting structured incident analysis to an explicit HTTP(S) endpoint
- Webhook delivery for single, multi-incident, and source-grouped analyses
- Mandatory `--redact` when using `--webhook` to prevent accidental secret disclosure
- HTTP status, URL-scheme, timeout, and transport error handling with stable CLI exit code 4
- Regression coverage for JSON webhook payloads and delivery failures

## [0.9.0] - 2026-08-20

### Added

- Opt-in `--redact` output sanitization for common secrets and identifiers
- Redaction of evidence, causes, checks, recommended actions, and enrichment text before display/export
- Regression coverage for direct, grouped, JSON, and SARIF redacted output

### Fixed

- Package metadata version is now synchronized with the runtime version at 0.9.0

## [0.8.0] - 2026-08-20

### Added

- SARIF 2.1.0 output with `--sarif` for CI and security tooling
- SARIF rule metadata, severity levels, confidence, evidence, verification checks, and recommended actions
- SARIF support for single, multi-incident, and source-grouped analysis results
- Regression coverage for SARIF structure and grouped-result flattening

## [0.7.0] - 2026-08-20

### Added

- Source-grouped correlation with `--group-by host|service|unit|container`
- Independent per-group incident detection and confidence scoring for structured JSON Lines input
- Group-aware JSON and human-readable output, including an explicit `<unknown>` bucket for records missing the selected source field

## [0.6.0] - 2026-08-20

### Added

- Source-scoped structured analysis with `--host`, `--service`, `--unit`, and `--container`
- Filtering across journald, container, and generic application metadata before incident analysis and confidence correlation
- Safe validation that rejects source filters for plain-text or malformed mixed input instead of silently applying them

### Fixed

- Runtime `incident-ai --version` now stays aligned with the package version

## [0.5.0] - 2026-08-20

### Added

- Correlated confidence scoring that raises confidence only after a primary incident signature matches
- Independent corroborating signals for disk exhaustion, OOM kills, Nginx upstream failures, DNS failures, and TLS certificate failures
- A 99% confidence cap so additional context strengthens a diagnosis without presenting deterministic certainty

## [0.4.0] - 2026-08-20

### Added

- Optional structured source context preservation with `--include-context`
- Host, service, systemd unit, container, and PID metadata in incident evidence for JSON Lines input
- Context extraction for common journald, container, and application-log field names while keeping default normalized output backward compatible

## [0.3.0] - 2026-08-20

### Added

- Structured JSON Lines ingestion for journald, container, and application logs
- `--input-format auto|text|jsonl` with safe auto-detection and strict validation mode
- Message extraction from common `MESSAGE`, `message`, `msg`, and `log` fields

## [0.2.0] - 2026-08-20

### Added

- Multi-incident analysis API with `analyze_all()`
- `incident-ai analyze --all` for returning every distinct recognized incident ordered by confidence
- JSON array and human-readable multi-incident output while preserving existing single-incident behavior by default

## [0.1.0] - 2026-08-20

### Added

- Deterministic incident analyzer with nine common Linux/service incident classes
- Human-readable and JSON output
- Stable automation exit codes
- File and stdin ingestion
- Evidence extraction and safe unknown-incident behavior
- Test suite and Ruff linting
- Python package metadata and `incident-ai` console command
- Docker image
- GitHub Actions CI and Docker build workflows
- Architecture, security, and contribution documentation
- Optional OpenAI Responses API enrichment with explicit opt-in and local redaction
- Automated tagged GitHub releases and weekly Dependabot dependency updates
