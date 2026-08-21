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

`--enrich` and outbound webhooks are deliberately not part of this local API. The server is designed as a local ingestion boundary for monitoring systems such as ServerWatch; remote enrichment and external delivery remain explicit CLI operations.

## Security boundary

The default bind address is loopback-only. The request body is limited to 1 MiB by default to prevent an accidental unbounded memory allocation from a monitoring client.

If the server is intentionally exposed beyond localhost, put it behind an authenticated reverse proxy and network policy. The built-in API does not implement authentication, TLS, rate limiting, or user management.

For programmatic use, `serve(host, port, max_body_bytes=...)` allows an embedding application to choose the listener and request-size limit.
