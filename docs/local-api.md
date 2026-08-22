# Local HTTP API

IncidentAI provides a small standard-library HTTP server for local automation and monitoring integrations. It is intentionally dependency-free and binds to `127.0.0.1` by default.

## Start the server

```bash
incident-ai-server
```

The default listener is `127.0.0.1:8080`. The console entry point can also be invoked through Python:

```bash
python -c 'from incident_ai.server import serve; serve("127.0.0.1", 8080)'
```

The server exposes:

- `GET /healthz` — returns `{"status":"ok"}`.
- `GET /version` — returns the stable API major version and installed package version.
- `GET /capabilities` — returns the supported endpoints, features, and effective request-size and concurrency limits.
- `GET /openapi.json` — returns a dependency-free OpenAPI 3.0.3 document for local API integration.
- `POST /analyze` — accepts a JSON request and returns one analysis or a list of analyses.

## OpenAPI discovery

Integrations can fetch the machine-readable OpenAPI contract before generating clients or validating requests:

```bash
curl -sS http://127.0.0.1:8080/openapi.json
```

The document describes the stable API endpoints, the JSON request fields accepted by `/analyze`, and the principal HTTP error responses. It is generated from the running package so its version and endpoint set stay synchronized with the implementation.

`GET /capabilities` advertises `openapi_discovery` and includes `/openapi.json` in its endpoint list. Feature discovery remains additive so clients can safely ignore capabilities they do not understand.

## Capability discovery

Integrations can query `/capabilities` before sending analysis requests instead of assuming which optional features are available:

```bash
curl -sS http://127.0.0.1:8080/capabilities
```

The response contains:

- `api_version` — stable API major version.
- `version` — installed IncidentAI release.
- `endpoints` — supported local API endpoints.
- `features` — supported analysis capabilities, including multi-incident analysis, JSON Lines ingestion, redaction, stable error codes, stable fingerprints, bounded concurrency, content-type validation, and OpenAPI discovery.
- `limits.max_body_bytes` — effective request body limit for the running server instance.
- `limits.max_concurrent_requests` — maximum number of simultaneous `/analyze` requests.

## Analyze a log

```bash
curl -sS http://127.0.0.1:8080/analyze \
  -H 'Content-Type: application/json' \
  -d '{"log":"Permission denied"}'
```

The request object supports `log`, `all`, `input_format`, `include_context`, `host`, `service`, `unit`, `container`, and `redact` as documented by `/openapi.json`.

### Content type

`POST /analyze` accepts JSON requests. When a `Content-Type` header is supplied, its media type must be `application/json`; parameters such as `charset=utf-8` are accepted. An explicit non-JSON media type returns HTTP `415` with the stable `unsupported_media_type` code.

For backward compatibility, requests that omit `Content-Type` continue to be accepted.

## Concurrency limit

The local API uses a bounded semaphore around `/analyze` processing. The default is **16 concurrent requests**. When all slots are occupied, new analysis requests receive HTTP `429` with the stable code `concurrency_limit_reached`.

Embedding applications can configure the limit through `serve(max_concurrent_requests=...)`. The configured value is advertised through `/capabilities`.

## Stable API errors

Error responses contain both a stable machine-readable `code` and the existing human-readable `error` field. Clients should branch on `code`, not on the text of `error`.

Current error classes include invalid JSON/request data, not-found endpoints, oversized bodies, unsupported media types, and exhausted concurrency. New error codes may be added without changing the API major version.

## Version discovery

```bash
curl -sS http://127.0.0.1:8080/version
```

The response contains `api_version` for compatibility decisions and `version` for the installed IncidentAI release.

`--enrich` and outbound webhooks are deliberately not part of this local API. Remote enrichment and external delivery remain explicit CLI operations.

## Security boundary

The default bind address is loopback-only. The request body is limited to 1 MiB by default, concurrent `/analyze` processing is limited to 16 requests by default, and explicit non-JSON content types are rejected. The OpenAPI document is descriptive only and does not add authentication, TLS, rate limiting, or user management.

If the server is intentionally exposed beyond localhost, put it behind an authenticated reverse proxy and network policy. The built-in concurrency bound is a resource-protection control, not an authentication or rate-limiting mechanism.
