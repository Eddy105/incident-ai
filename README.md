# IncidentAI

IncidentAI is a lightweight incident-analysis CLI for Linux, DevOps, and SRE workflows. It turns familiar log signatures into a structured diagnosis with evidence, likely cause, verification checks, and recommended actions.

The first release deliberately uses a deterministic rules engine. This keeps diagnosis transparent, testable, fast, offline, and safe to run on sensitive logs. The architecture is intended to support optional LLM enrichment later without making an external AI service a runtime requirement.

## Example

```console
$ echo 'nginx: connect() failed (111: Connection refused) while connecting to upstream' | incident-ai analyze -
INCIDENTAI
========================================================================
Incident:   Reverse proxy cannot reach upstream service
Type:       nginx_upstream_refused
Severity:   CRITICAL
Confidence: 97%

Probable cause:
  The reverse proxy is running, but its configured upstream service is not accepting connections.
```

IncidentAI also provides checks and recommended actions, for example `systemctl status`, `ss -lntp`, and a local backend health request.

## Features

- Analyze files or stdin
- Human-readable incident reports
- Machine-readable JSON output
- SARIF 2.1.0 output for CI and security tooling
- Stable exit codes for automation
- Evidence extraction from the supplied log text
- Structured JSON Lines ingestion for journald, containers, and applications
- Optional host, service, systemd unit, container, and PID context in structured-log evidence
- Deterministic, auditable diagnosis rules
- No network access required for the default analyzer
- Optional `--redact` output sanitization for common secrets and identifiers
- Secure opt-in `--webhook` export for redacted incident payloads
- Optional HMAC-SHA256 webhook signatures for authenticated delivery
- Deterministic webhook event IDs for receiver-side idempotency and duplicate detection
- Optional bounded webhook retries for transient delivery failures
- Honors numeric `Retry-After` responses for rate limiting and server backpressure
- Optional webhook dry-run validation without sending a request
- Optional OpenAI enrichment behind explicit `--enrich` opt-in and local redaction
- Dependency-free local HTTP API for monitoring integrations
- `/version` endpoint for API compatibility discovery
- Docker image support
- Automated linting, test coverage, package builds, Docker builds, and tagged GitHub releases
- Weekly Dependabot updates for Python, Docker, and GitHub Actions dependencies

## Supported signatures

The initial rule set recognizes:

- Filesystem full / quota exhausted
- Linux OOM killer events
- Nginx upstream connection failures
- Generic connection refused errors
- DNS resolution failures
- Permission failures
- Port/address already in use
- TLS certificate validation failures
- Network/dependency timeouts

Unknown incidents fail safely and return a low-confidence generic analysis instead of inventing a root cause.

## Installation

For development:

```bash
git clone https://github.com/Eddy105/incident-ai.git
cd incident-ai
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
```

Then:

```bash
incident-ai --version
```

## Usage

Analyze a file:

```bash
incident-ai analyze /var/log/nginx/error.log
```

Analyze stdin:

```bash
journalctl -u nginx --since '-10 min' | incident-ai analyze -
```

Analyze journald JSON Lines while preserving source metadata in evidence:

```bash
journalctl -o json -u nginx --since '-10 min' | incident-ai analyze - --input-format jsonl --include-context
```

With `--include-context`, recognized metadata is rendered as a compact evidence prefix such as `[host=web-01 service=nginx unit=nginx.service pid=1234]`. The flag is opt-in, so existing normalized JSON Lines output remains unchanged by default.

Analyze only records from a specific source:

```bash
journalctl -o json --since '-10 min' | incident-ai analyze - --host web-01 --service nginx
```

Analyze each source independently before correlation:

```bash
journalctl -o json --since '-10 min' | incident-ai analyze - --group-by host --all --json
```

Redact common secrets and identifiers before displaying or exporting the diagnosis:

```bash
incident-ai analyze app.log --json --redact
```

`--redact` is opt-in for backward compatibility. It sanitizes common email addresses, IP addresses, API keys, tokens, passwords, bearer credentials, and other matching identifiers in exportable analysis fields. It does not modify the source log file.

Send a redacted analysis to an internal webhook:

```bash
incident-ai analyze app.log --json --redact --webhook https://ops.example.test/incidents
```

`--webhook` sends only the structured analysis result as a JSON `POST`. It is intentionally restricted to explicit HTTP(S) URLs and requires `--redact` so credentials and common identifiers are not accidentally exported. Webhook delivery failures return exit code `4`; successful delivery does not change the normal incident exit code.

For authenticated webhook delivery, set `INCIDENT_AI_WEBHOOK_SECRET` in the process environment. IncidentAI then adds `X-IncidentAI-Timestamp` and `X-IncidentAI-Signature` headers. The signature is `sha256=HMAC_SHA256(secret, timestamp + "." + raw_request_body)`. The timestamp is included in the signed payload so receivers can reject stale or replayed requests. The secret is never sent as a header or included in the JSON payload.

Every webhook also includes `X-IncidentAI-Event-ID`, a deterministic SHA-256 identifier derived from the exact serialized request body. Receivers can use it as an idempotency key to ignore duplicate deliveries of the same payload.

```bash
export INCIDENT_AI_WEBHOOK_SECRET='replace-with-a-random-secret'
incident-ai analyze app.log --json --redact --webhook https://ops.example.test/incidents
```

For transient webhook failures, enable a bounded number of retries:

```bash
incident-ai analyze app.log --json --redact \
  --webhook https://ops.example.test/incidents \
  --webhook-retries 2
```

Retries are disabled by default. HTTP `429` and `5xx` responses use bounded exponential backoff, but a numeric `Retry-After` response header takes precedence for that attempt. Server-requested delays are capped at 60 seconds. See [`docs/webhook-retry-after.md`](docs/webhook-retry-after.md) for the exact behavior.

Validate a webhook without sending a request:

```bash
incident-ai analyze app.log --json --redact \
  --webhook https://ops.example.test/incidents \
  --webhook-dry-run
```

`--webhook-dry-run` performs the same destination and payload validation as delivery, but never creates a POST request. The validation summary is written to stderr so normal analysis output on stdout remains script-friendly. See [`docs/webhook-dry-run.md`](docs/webhook-dry-run.md).

For multiple incidents, the webhook receives a JSON array. With `--group-by`, it receives the same grouped JSON structure used by `--json`.

JSON output:

```bash
incident-ai analyze app.log --json
```

Compact JSON for scripts:

```bash
incident-ai analyze app.log --compact
```

SARIF 2.1.0 for GitHub Code Scanning, Azure DevOps, or other SARIF-aware tooling:

```bash
incident-ai analyze app.log --sarif
```

For multiple incidents:

```bash
incident-ai analyze app.log --all --sarif > results.sarif
```

`--sarif` emits one SARIF result per detected incident and preserves severity, confidence, evidence, verification checks, and recommended actions as result properties. Source-grouped analyses are flattened into one SARIF run because SARIF already provides a single result stream suitable for CI ingestion. Combine it with `--redact` when SARIF output may leave a trusted environment.

Optional AI enrichment:

```bash
python -m pip install -e '.[openai]'
export OPENAI_API_KEY='...'
incident-ai analyze app.log --enrich
```

`--enrich` is never enabled automatically. IncidentAI first runs the local deterministic analyzer and sends only the resulting structured diagnosis plus redacted evidence, not the full raw log. Use `--model` to override the default model.

## Local HTTP API

Start the dependency-free local server:

```bash
incident-ai-server
```

The default listener is `127.0.0.1:8080`. Check health and API compatibility:

```bash
curl -sS http://127.0.0.1:8080/healthz
curl -sS http://127.0.0.1:8080/version
```

`/version` returns a stable `api_version` for compatibility decisions and the installed IncidentAI `version`. See [`docs/local-api.md`](docs/local-api.md) and [`docs/api-versioning.md`](docs/api-versioning.md).

## Exit codes

| Code | Meaning |
|---:|---|
| 0 | No recognized incident / informational result |
| 1 | Recognized warning-level incident |
| 2 | Recognized critical incident |
| 3 | Input/read error |
| 4 | External enrichment or webhook delivery error |

This makes IncidentAI usable in shell scripts, CI jobs, health checks, and monitoring pipelines.

## Docker

Build:

```bash
docker build -t incident-ai .
```

Analyze stdin:

```bash
echo 'No space left on device' | docker run --rm -i incident-ai analyze -
```

Analyze a mounted log file:

```bash
docker run --rm -v "$PWD/logs:/logs:ro" incident-ai analyze /logs/app.log --json
```

## Development

```bash
make install-dev
make check
make build
```

## Automated GitHub publishing

For a fresh checkout with an authenticated GitHub CLI, the repository can be created and published automatically:

```bash
./scripts/publish-github.sh
```
