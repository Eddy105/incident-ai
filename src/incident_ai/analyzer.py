from __future__ import annotations

from .models import IncidentAnalysis
from .rules import RULES, Rule


def _matching_evidence(text: str, rule: Rule) -> tuple[str, ...]:
    evidence: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if any(pattern.search(stripped) for pattern in rule.patterns):
            evidence.append(stripped[:500])
        if len(evidence) == 3:
            break
    return tuple(evidence)


def analyze_text(text: str) -> IncidentAnalysis:
    """Analyze log text and return the highest-confidence matching incident."""
    if not text.strip():
        return IncidentAnalysis(
            incident_type="empty_input",
            title="No incident data supplied",
            severity="info",
            confidence=1.0,
            probable_cause="No log content was available for analysis.",
            evidence=(),
            checks=("Provide log lines from the affected service or host.",),
            recommended_actions=("Capture the error and retry the analysis.",),
        )

    matches: list[tuple[Rule, tuple[str, ...]]] = []
    for rule in RULES:
        evidence = _matching_evidence(text, rule)
        if evidence:
            matches.append((rule, evidence))

    if not matches:
        return IncidentAnalysis(
            incident_type="unknown",
            title="No known incident signature detected",
            severity="info",
            confidence=0.20,
            probable_cause="The supplied logs do not match IncidentAI's current deterministic rule set.",
            evidence=tuple(line.strip()[:500] for line in text.splitlines() if line.strip())[:3],
            checks=(
                "Inspect surrounding log lines and timestamps.",
                "Correlate application logs with system and dependency health.",
            ),
            recommended_actions=(
                "Collect a larger incident window and re-run the analysis.",
                "Add a new regression rule when the root cause is confirmed.",
            ),
        )

    rule, evidence = max(matches, key=lambda item: item[0].confidence)
    return IncidentAnalysis(
        incident_type=rule.incident_type,
        title=rule.title,
        severity=rule.severity,
        confidence=rule.confidence,
        probable_cause=rule.probable_cause,
        evidence=evidence,
        checks=rule.checks,
        recommended_actions=rule.recommended_actions,
    )
