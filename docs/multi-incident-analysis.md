# Multi-incident analysis

IncidentAI normally returns the highest-confidence recognized incident to preserve the original CLI and API contract.

Use `--all` when a log window may contain more than one independent failure:

```bash
incident-ai analyze app.log --all
```

For machine-readable output, combine it with `--json` or `--compact`:

```bash
incident-ai analyze app.log --all --json
```

The JSON result is an array ordered by descending confidence. Each incident type appears at most once, while its evidence can contain up to three matching log lines.

The process exit code reflects the most severe returned incident: `2` when any critical incident is present, `1` for recognized warning-level incidents, and `0` when nothing is recognized.

Python callers can use the public API directly:

```python
from incident_ai import analyze_all

analyses = analyze_all(log_text)
for analysis in analyses:
    print(analysis.incident_type, analysis.confidence)
```

`analyze_text()` remains unchanged and still returns only the highest-confidence result.
