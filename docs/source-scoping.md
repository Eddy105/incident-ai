# Source-scoped structured analysis

IncidentAI can limit structured JSON Lines input to a single operational source before incident detection and correlated confidence scoring.

Supported filters:

- `--host` matches journald `_HOSTNAME` and generic `hostname`/`host` fields.
- `--service` matches `SYSLOG_IDENTIFIER` and generic `service`/`app`/`application` fields.
- `--unit` matches journald `_SYSTEMD_UNIT` and generic `unit` fields.
- `--container` matches `CONTAINER_NAME`, `container_name`, and `container` fields.

Filters use exact string matching and combine with AND semantics. This makes it possible to isolate one service instance from a multi-host or cluster-wide log stream before analysis.

```bash
journalctl -o json | incident-ai analyze - --host web-02 --unit api.service --all --json
```

Source filters require structured JSON Lines input. Plain text, malformed JSON, or mixed structured/plain input is rejected when a source filter is active so IncidentAI never silently analyzes an unintended source set.

Use `--include-context` together with source filters when the resulting evidence should retain host, service, unit, container, and PID metadata.
