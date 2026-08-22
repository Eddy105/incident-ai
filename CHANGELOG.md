# Changelog

All notable changes to this project will be documented here.

## [0.17.0] - 2026-08-22

### Added

- Add `GET /openapi.json` with a dependency-free OpenAPI 3.0.3 description of the local API
- Advertise OpenAPI discovery through `GET /capabilities` and the `openapi_discovery` feature identifier
- Include request and response integration metadata for health, version, capabilities, and analysis endpoints
- Add regression coverage for the OpenAPI endpoint and API endpoint discovery

## [0.16.0] - 2026-08-22

### Added

- Validate explicit `Content-Type` headers on local `POST /analyze` requests
- Return stable `unsupported_media_type` errors with HTTP 415 for non-JSON media types
- Advertise content-type validation through local API capability discovery
- Preserve backward compatibility for clients that omit `Content-Type`
- Add regression coverage for rejected media types and legacy header omission

## [0.15.0] - 2026-08-22

### Security

- Bound concurrent local API analysis requests to 16 by default to prevent unbounded request-thread and analysis pressure
- Return stable `concurrency_limit_reached` errors with HTTP 429 when the configured concurrency budget is exhausted
- Advertise the effective concurrency limit through `GET /capabilities`
- Allow embedding applications to configure `max_concurrent_requests` explicitly
- Add regression coverage for the concurrency boundary and capability reporting

## [0.14.0] - 2026-08-21

### Added

- Add `GET /capabilities` to the local HTTP API for integration feature discovery
- Report supported endpoints, stable feature identifiers, API/package versions, and the effective request-size limit
- Keep capability feature identifiers additive so older clients can safely ignore newly advertised features
- Add regression coverage for capability discovery and configured request-size limits

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
