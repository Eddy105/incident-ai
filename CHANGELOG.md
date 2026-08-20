# Changelog

All notable changes to this project will be documented here.

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
