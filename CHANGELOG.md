# Changelog

All notable changes to this project will be documented here.

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
