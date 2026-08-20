from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal

Severity = Literal["info", "warning", "critical"]


@dataclass(frozen=True, slots=True)
class IncidentAnalysis:
    incident_type: str
    title: str
    severity: Severity
    confidence: float
    probable_cause: str
    evidence: tuple[str, ...]
    checks: tuple[str, ...]
    recommended_actions: tuple[str, ...]
    enrichment: str | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)
