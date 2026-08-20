# Source-grouped correlation

IncidentAI can partition structured JSON Lines records by operational source before incident detection and correlated confidence scoring.

Use `--group-by` with one of `host`, `service`, `unit`, or `container`:

```bash
journalctl -o json | incident-ai analyze - --group-by host --all --json
```

Each group is analyzed independently. This prevents a primary incident on one host from receiving a confidence boost from corroborating signals that only occurred on another host or service.

The JSON output has an explicit grouping envelope:

```json
{
  "group_by": "host",
  "groups": [
    {
      "value": "web-01",
      "analyses": []
    }
  ]
}
```

Records that do not contain the selected grouping field are retained under the `<unknown>` group instead of being silently discarded.

Source filters such as `--unit api.service` are applied before grouping, so filtering and grouping can be combined. `--include-context` remains optional and controls whether host, service, unit, container, and PID metadata is copied into evidence strings.

Grouping requires structured JSON Lines input. Plain text and mixed structured/plain input are rejected when `--group-by` is active, avoiding ambiguous cross-source correlation.
