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
- Optional OpenAI enrichment behind explicit `--enrich` opt-in and local redaction
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

`--sarif` emits one SARIF result per detected incident and preserves severity, confidence, evidence, verification checks, and recommended actions as result properties. Source-grouped analyses are flattened into one SARIF run because SARIF already provides a single result stream suitable for CI ingestion.

Optional AI enrichment:

```bash
python -m pip install -e '.[openai]'
export OPENAI_API_KEY='...'
incident-ai analyze app.log --enrich
```

`--enrich` is never enabled automatically. IncidentAI first runs the local deterministic analyzer and sends only the resulting structured diagnosis plus redacted evidence, not the full raw log. Use `--model` to override the default model.

## Exit codes

| Code | Meaning |
|---:|---|
| 0 | No recognized incident / informational result |
| 1 | Recognized warning-level incident |
| 2 | Recognized critical incident |
| 3 | Input/read error |

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

The script creates `Eddy105/incident-ai` when necessary, pushes `main`, and publishes the version tag. The tag triggers the automated GitHub Release workflow.

## Architecture

See [`docs/architecture.md`](docs/architecture.md).

## Security and privacy

The default analyzer runs entirely locally and does not upload logs. Avoid placing credentials, tokens, personal data, or secrets in bug reports. See [`SECURITY.md`](SECURITY.md).

## Roadmap

- Webhook integrations
- REST API and small web dashboard
- ServerWatch integration for automatic incident context

## License

MIT
