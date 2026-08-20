from __future__ import annotations

import re


def _rx(pattern: str) -> re.Pattern[str]:
    return re.compile(pattern, re.IGNORECASE | re.MULTILINE)


# Supplemental signatures raise confidence only after a primary incident rule matches.
# They are intentionally distinct from the primary patterns so supporting context cannot
# create an incident by itself.
CORROBORATING_SIGNALS: dict[str, tuple[re.Pattern[str], ...]] = {
    "disk_full": (
        _rx(r"filesystem .*\b100%\b"),
        _rx(r"inode(?:s)? .*\b100%\b"),
    ),
    "oom_kill": (
        _rx(r"memory cgroup out of memory"),
        _rx(r"oom_reaper"),
        _rx(r"memory pressure .*critical"),
    ),
    "nginx_upstream_refused": (
        _rx(r"upstream server temporarily disabled"),
        _rx(r"no live upstreams"),
    ),
    "dns_failure": (
        _rx(r"dns server .* (?:unreachable|unavailable)"),
        _rx(r"resolver .* (?:timeout|timed out)"),
    ),
    "tls_certificate": (
        _rx(r"unable to get local issuer certificate"),
        _rx(r"self[- ]signed certificate"),
    ),
}


def correlated_confidence(incident_type: str, base_confidence: float, text: str) -> float:
    """Raise confidence when independent supporting signals corroborate a matched rule."""
    patterns = CORROBORATING_SIGNALS.get(incident_type, ())
    matched_signals = sum(1 for pattern in patterns if pattern.search(text))
    return min(0.99, base_confidence + (0.01 * matched_signals))
