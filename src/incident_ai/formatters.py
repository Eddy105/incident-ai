from __future__ import annotations

import json

from .models import IncidentAnalysis


def format_json(analysis: IncidentAnalysis, *, pretty: bool = True) -> str:
    if pretty:
        return json.dumps(analysis.to_dict(), indent=2, ensure_ascii=False)
    return json.dumps(analysis.to_dict(), separators=(",", ":"), ensure_ascii=False)


def format_json_many(analyses: tuple[IncidentAnalysis, ...], *, pretty: bool = True) -> str:
    payload = [analysis.to_dict() for analysis in analyses]
    if pretty:
        return json.dumps(payload, indent=2, ensure_ascii=False)
    return json.dumps(payload, separators=(",", ":"), ensure_ascii=False)


def format_json_grouped(
    groups: tuple[tuple[str, tuple[IncidentAnalysis, ...]], ...],
    *,
    group_by: str,
    pretty: bool = True,
) -> str:
    payload = {
        "group_by": group_by,
        "groups": [
            {
                "value": value,
                "analyses": [analysis.to_dict() for analysis in analyses],
            }
            for value, analyses in groups
        ],
    }
    if pretty:
        return json.dumps(payload, indent=2, ensure_ascii=False)
    return json.dumps(payload, separators=(",", ":"), ensure_ascii=False)


def _sarif_level(severity: str) -> str:
    return {"critical": "error", "warning": "warning", "info": "note"}[severity]


def _sarif_result(analysis: IncidentAnalysis) -> dict[str, object]:
    return {
        "ruleId": analysis.incident_type,
        "level": _sarif_level(analysis.severity),
        "message": {"text": analysis.probable_cause},
        "properties": {
            "title": analysis.title,
            "fingerprint": analysis.fingerprint,
            "severity": analysis.severity,
            "confidence": analysis.confidence,
            "evidence": list(analysis.evidence),
            "checks": list(analysis.checks),
            "recommendedActions": list(analysis.recommended_actions),
        },
    }


def format_sarif(analyses: tuple[IncidentAnalysis, ...], *, tool_name: str = "IncidentAI") -> str:
    rules: dict[str, dict[str, object]] = {}
    for analysis in analyses:
        rules.setdefault(
            analysis.incident_type,
            {
                "id": analysis.incident_type,
                "name": analysis.title,
                "shortDescription": {"text": analysis.title},
                "help": {"text": analysis.probable_cause},
            },
        )

    payload = {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {"driver": {"name": tool_name, "rules": list(rules.values())}},
                "results": [_sarif_result(analysis) for analysis in analyses],
            }
        ],
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


def format_text(analysis: IncidentAnalysis) -> str:
    lines = [
        "INCIDENTAI",
        "=" * 72,
        f"Incident:   {analysis.title}",
        f"Type:       {analysis.incident_type}",
        f"Fingerprint: {analysis.fingerprint}",
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


def format_text_many(analyses: tuple[IncidentAnalysis, ...]) -> str:
    return "\n\n".join(format_text(analysis) for analysis in analyses)


def format_text_grouped(
    groups: tuple[tuple[str, tuple[IncidentAnalysis, ...]], ...],
    *,
    group_by: str,
) -> str:
    sections: list[str] = []
    for value, analyses in groups:
        header = f"SOURCE GROUP {group_by}={value}\n" + "-" * 72
        sections.append(f"{header}\n{format_text_many(analyses)}")
    return "\n\n".join(sections)
