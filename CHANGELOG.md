# Changelog

All notable changes to this project will be documented here.

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
