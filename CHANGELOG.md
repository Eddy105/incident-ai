# Changelog

All notable changes to this project will be documented here.

## [0.13.0] - 2026-08-21

### Added

- Add stable machine-readable error codes to the local HTTP API
- Preserve the existing `error` messages for backward-compatible diagnostics
- Add regression coverage for validation, invalid JSON, size-limit, and not-found error codes

## [0.12.2] - 2026-08-21

### Added

- Add `GET /version` to the local HTTP API
- Expose a stable API major version alongside the running package version for integration compatibility checks
- Add regression coverage for API and package version metadata

## [0.12.1] - 2026-08-21

### Added

- Add a dependency-free local HTTP API for monitoring and automation integrations
- Add `incident-ai-server` with loopback-only `127.0.0.1:8080` defaults
- Add `GET /healthz` and bounded `POST /analyze` endpoints
- Support structured input options, source filters, multi-incident analysis, and opt-in redaction through the API
- Limit request bodies to 1 MiB by default and document the security boundary for non-local deployments
- Add regression coverage for health checks, analysis, validation errors, and request-size limits

## [0.12.0] - 2026-08-21

### Added

- Add `--webhook-dry-run` to validate webhook destination and payload metadata without sending a request
- Keep dry-run diagnostics on stderr so normal incident output remains script-friendly on stdout
- Add `inspect_webhook()` for programmatic configuration validation
- Preserve the deterministic webhook event ID and HMAC configuration status in dry-run metadata
- Add regression coverage for dry-run validation and private-destination rejection

## [0.11.6] - 2026-08-21

### Security

- Bound `--webhook-retries` to a maximum of 8 retries so the retry feature cannot create unbounded delivery loops
- Reject non-positive webhook timeouts before any network request is attempted
- Validate the retry count type at the webhook API boundary as well as through the CLI
- Add regression coverage for retry and timeout limits

## [0.11.5] - 2026-08-21

### Added

- Support both numeric `Retry-After` delays and HTTP-date values for retryable webhook responses
- Fall back to bounded exponential backoff when an HTTP-date is invalid or already in the past
- Add regression coverage for HTTP-date parsing, expiry, and webhook delivery

## [0.11.4] - 2026-08-21

### Added

- Honor numeric `Retry-After` headers for retryable HTTP 429 and 5xx webhook responses
- Cap server-requested retry delays at 60 seconds so webhook delivery remains bounded
- Add regression coverage for server-requested and capped retry delays

## [0.11.3] - 2026-08-20

### Added

- Add opt-in bounded retries for transient webhook delivery failures
- Retry HTTP 429 and 5xx responses, network errors, and timeouts with exponential backoff
- Keep retries disabled by default for backward-compatible delivery behavior
- Expose retries through `--webhook-retries`
- Preserve the deterministic event ID across retry attempts
- Add regression coverage for transient HTTP and network retries

## [0.11.2] - 2026-08-20

### Added

- Add deterministic `X-IncidentAI-Event-ID` headers to webhook requests
- Derive event IDs from the exact serialized request body for receiver-side idempotency and duplicate detection
- Add regression coverage for stable and changing event IDs

## [0.11.1] - 2026-08-20

### Security

- Fully redact titles, probable causes, checks, and recommended actions before optional remote OpenAI enrichment
- Add regression coverage proving credentials and identifiers cannot cross the enrichment boundary
