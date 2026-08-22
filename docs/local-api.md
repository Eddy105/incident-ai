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

## Request correlation

Every local API response includes a unique `X-IncidentAI-Request-ID` header. The identifier is generated independently for each HTTP request and is useful for correlating monitoring events, client logs, reverse-proxy records, and IncidentAI responses without changing the existing JSON response bodies.

Example:

```text
X-IncidentAI-Request-ID: 9c4e1f2a8f4a4c9f8f5b4b7d9e4b2a10
```

Request IDs are present on successful responses and errors, including `404`, `413`, `415`, and `429` responses. Clients should treat the value as opaque and should not infer ordering or identity semantics from its format.

`GET /capabilities` advertises the `request_ids` feature. The feature is additive and does not change API major version `1`.

## OpenAPI discovery

Integrations can fetch the machine-readable OpenAPI contract before generating clients or validating requests:

```bash
curl -sS http://127.0.0.1:8080/openapi.json
```

The document describes the stable API endpoints, the JSON request fields accepted by `/analyze`, and the principal HTTP error responses. It is generated from the running package so its version and endpoint set stay synchronized with the implementation.

`GET /capabilities` advertises `openapi_discovery` and includes `/openapi.json` in its endpoint list. Feature names remain additive so clients can safely ignore capabilities they do not understand.

## Capability discovery

Integrations can query `/capabilities` before sending analysis requests instead of assuming which optional features are available:

```bash
curl -sS http://127.0.0.1:8080/capabilities
```

The response contains:

- `api_version` — stable API major version.
- `version` — installed IncidentAI release.
- `endpoints` — supported local API endpoints.
- `features` — supported analysis capabilities, including multi-incident analysis, JSON Lines ingestion, redaction, stable error codes, stable fingerprints, bounded concurrency, content-type validation, OpenAPI discovery, and request IDs.
- `limits.max_body_bytes` — effective request body limit for the running server instance.
- `limits.max_concurrent_requests` — maximum number of simultaneous `/analyze` requests.

Feature names are additive. Clients should ignore unknown feature names so a newer IncidentAI release can advertise capabilities without breaking older integrations.

## Analyze a log

```bash
curl -sS http://127.0.0.1:8080/analyze \
  -H 'Content-Type: application/json' \
  -d '{"log":"Permission denied"}'
```

The request object supports:

- `log` (required string)
- `all` (boolean, default `false`)
- `input_format`: `auto`, `text`, or `jsonl`
- `include_context` (boolean)
- `host`, `service`, `unit`, `container` source filters
- `redact` (boolean)

### Content type

`POST /analyze` accepts JSON requests. When a `Content-Type` header is supplied, its media type must be `application/json`; parameters such as `charset=utf-8` are accepted. An explicit non-JSON media type returns HTTP `415` with the stable `unsupported_media_type` code.

For backward compatibility, requests that omit `Content-Type` continue to be accepted and are interpreted as JSON based on the existing request contract.

## Concurrency limit

The local API uses a bounded semaphore around `/analyze` processing. The default is **16 concurrent requests**. When all slots are occupied, new analysis requests receive HTTP `429` with the stable code `concurrency_limit_reached` instead of creating additional unbounded analysis pressure.

Embedding applications can configure the limit through `serve()`:

```python
from incident_ai.server import serve

serve(max_concurrent_requests=32)
```

The configured value is advertised through `/capabilities`. Keep the limit appropriate for the available CPU and memory when running the API under sustained monitoring load.

## Stable API errors

Error responses contain both a stable machine-readable `code` and the existing human-readable `error` field:

```json
{"code":"invalid_log","error":"'log' must be a string"}
```

Clients should branch on `code`, not on the text of `error`. The `error` field remains available for logs and human diagnostics and is intentionally preserved for backward compatibility.

Current error codes include:

| HTTP | Code | Meaning |
| --- | --- | --- |
| 400 | `invalid_json` | Request body is not valid UTF-8 JSON. |
| 400 | `invalid_request_body` | Request JSON is valid but is not an object. |
| 400 | `invalid_log` | `log` is missing or is not a string. |
| 400 | `invalid_input_format` | `input_format` is unsupported. |
| 400 | `invalid_structured_input` | JSON Lines input failed validation. |
| 400 | `invalid_<field>` | A supplied boolean or source-filter field is invalid. |
| 400 | `incomplete_request_body` | The declared request body could not be read completely. |
| 404 | `not_found` | Endpoint does not exist. |
| 413 | `request_body_too_large` | Request exceeds the configured body limit. |
| 415 | `unsupported_media_type` | An explicit request media type is not `application/json`. |
| 429 | `concurrency_limit_reached` | The configured concurrent analysis budget is exhausted. |

New error codes may be added without changing the API major version. Clients should treat unknown codes as generic request failures.

## Version discovery

```bash
curl -sS http://127.0.0.1:8080/version
```

The response contains `api_version` for compatibility decisions and `version` for the installed IncidentAI release. See [`api-versioning.md`](api-versioning.md) for the compatibility policy.

`--enrich` and outbound webhooks are deliberately not part of this local API. The server is designed as a local ingestion boundary for monitoring systems such as ServerWatch; remote enrichment and external delivery remain explicit CLI operations.

## Security boundary

The default bind address is loopback-only. The request body is limited to 1 MiB by default, concurrent `/analyze` processing is limited to 16 requests by default, and explicit non-JSON content types are rejected. These bounds and protocol validation prevent accidental monitoring clients from causing unbounded memory or analysis-thread pressure and make the HTTP contract deterministic. `/capabilities` reports the effective resource limits for the running instance.

The OpenAPI document is descriptive only; it does not add authentication, TLS, rate limiting, or user management. Request IDs are correlation metadata only and do not provide authentication, authorization, or request deduplication.

If the server is intentionally exposed beyond localhost, put it behind an authenticated reverse proxy and network policy. The built-in API does not implement authentication, TLS, rate limiting, or user management. The concurrency bound is a resource-protection control, not an authentication or rate-limiting mechanism.

For programmatic use, `serve(host, port, max_body_bytes=..., max_concurrent_requests=...)` allows an embedding application to choose the listener, request-size limit, and concurrency budget.
