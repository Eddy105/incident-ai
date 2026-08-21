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
- `POST /analyze` — accepts a JSON request and returns one analysis or a list of analyses.

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

New error codes may be added without changing the API major version. Clients should treat unknown codes as generic request failures.

## Version discovery

```bash
curl -sS http://127.0.0.1:8080/version
```

The response contains `api_version` for compatibility decisions and `version` for the installed IncidentAI release. See [`api-versioning.md`](api-versioning.md) for the compatibility policy.

`--enrich` and outbound webhooks are deliberately not part of this local API. The server is designed as a local ingestion boundary for monitoring systems such as ServerWatch; remote enrichment and external delivery remain explicit CLI operations.

## Security boundary

The default bind address is loopback-only. The request body is limited to 1 MiB by default to prevent an accidental unbounded memory allocation from a monitoring client.

If the server is intentionally exposed beyond localhost, put it behind an authenticated reverse proxy and network policy. The built-in API does not implement authentication, TLS, rate limiting, or user management.

For programmatic use, `serve(host, port, max_body_bytes=...)` allows an embedding application to choose the listener and request-size limit.
