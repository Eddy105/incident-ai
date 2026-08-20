from __future__ import annotations

import json
from dataclasses import replace

from .models import IncidentAnalysis
from .redaction import redact_text


class EnrichmentError(RuntimeError):
    pass


def build_enrichment_input(analysis: IncidentAnalysis) -> str:
    """Build a minimal redacted payload; raw logs are never sent by this function."""
    payload = {
        "incident_type": analysis.incident_type,
        "title": analysis.title,
        "severity": analysis.severity,
        "confidence": analysis.confidence,
        "probable_cause": analysis.probable_cause,
        "evidence": [redact_text(item) for item in analysis.evidence],
        "checks": list(analysis.checks),
        "recommended_actions": list(analysis.recommended_actions),
    }
    return json.dumps(payload, ensure_ascii=False)


def enrich_with_openai(
    analysis: IncidentAnalysis,
    *,
    model: str = "gpt-5.6",
) -> IncidentAnalysis:
    """Optionally enrich an already-computed local analysis through OpenAI Responses API."""
    try:
        from openai import OpenAI
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise EnrichmentError(
            "OpenAI enrichment requires the optional dependency: pip install 'incident-ai[openai]'"
        ) from exc

    prompt = (
        "You are an SRE incident-analysis assistant. Review the structured local diagnosis below. "
        "Do not claim certainty beyond the evidence. Return a concise second opinion with: "
        "(1) likely root cause, (2) what to verify next, (3) safest remediation order, and "
        "(4) any important alternative hypothesis. Never instruct destructive actions without "
        "a verification or backup step first.\n\nLocal diagnosis:\n"
        + build_enrichment_input(analysis)
    )

    try:
        client = OpenAI()
        response = client.responses.create(model=model, input=prompt)
    except Exception as exc:  # pragma: no cover - network/provider dependent
        raise EnrichmentError(f"OpenAI enrichment failed: {exc}") from exc

    text = getattr(response, "output_text", "").strip()
    if not text:
        raise EnrichmentError("OpenAI enrichment returned no text.")
    return replace(analysis, enrichment=text)
