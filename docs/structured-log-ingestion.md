# Structured log ingestion

IncidentAI can analyze newline-delimited JSON logs without requiring a preprocessing pipeline. This is useful for `journalctl -o json`, container logs, and services that emit structured JSON records.

By default, `incident-ai analyze` uses `--input-format auto`. When every non-empty input line is a JSON object, IncidentAI extracts the first available message field from `MESSAGE`, `message`, `msg`, or `log` before running the deterministic analyzer. Mixed or ordinary text remains unchanged.

```bash
journalctl -u nginx -o json --since '-10 min' | incident-ai analyze - --all
```

Force JSON Lines validation when a pipeline is expected to be structured:

```bash
incident-ai analyze app.jsonl --input-format jsonl --json
```

Malformed JSON or non-object JSON records then produce exit code `3`, the same input-error class used for unreadable files.

Force legacy plain-text behavior when JSON-looking lines must not be normalized:

```bash
incident-ai analyze app.log --input-format text
```

Records without a recognized message field are serialized deterministically so rules can still match useful values such as an `error` field.
