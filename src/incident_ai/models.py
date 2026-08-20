from __future__ import annotations

import hashlib
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

    @property
    def fingerprint(self) -> str:
        """Return a stable identifier for deduplication of equivalent incidents."""
        material = "\x00".join((self.incident_type, self.title, self.probable_cause))
        return hashlib.sha256(material.encode("utf-8")).hexdigest()[:16]

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["fingerprint"] = self.fingerprint
        return payload
