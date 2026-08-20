from __future__ import annotations

import json

from .models import IncidentAnalysis


def format_json(analysis: IncidentAnalysis, *, pretty: bool = True) -> str:
    if pretty:
        return json.dumps(analysis.to_dict(), indent=2, ensure_ascii=False)
    return json.dumps(analysis.to_dict(), separators=(",", ":"), ensure_ascii=False)


def format_text(analysis: IncidentAnalysis) -> str:
    lines = [
        "INCIDENTAI",
        "=" * 72,
        f"Incident:   {analysis.title}",
        f"Type:       {analysis.incident_type}",
        f"Severity:   {analysis.severity.upper()}",
        f"Confidence: {analysis.confidence:.0%}",
        "",
        "Probable cause:",
        f"  {analysis.probable_cause}",
    ]

    if analysis.evidence:
        lines.extend(["", "Evidence:"])
        lines.extend(f"  - {item}" for item in analysis.evidence)

    lines.extend(["", "Checks:"])
    lines.extend(f"  - {item}" for item in analysis.checks)
    lines.extend(["", "Recommended actions:"])
    lines.extend(f"  - {item}" for item in analysis.recommended_actions)
    if analysis.enrichment:
        lines.extend(["", "AI enrichment:", analysis.enrichment])
    return "\n".join(lines)
