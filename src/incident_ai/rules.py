from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Pattern

from .models import Severity


@dataclass(frozen=True, slots=True)
class Rule:
    incident_type: str
    title: str
    severity: Severity
    confidence: float
    patterns: tuple[Pattern[str], ...]
    probable_cause: str
    checks: tuple[str, ...]
    recommended_actions: tuple[str, ...]


def _rx(pattern: str) -> Pattern[str]:
    return re.compile(pattern, re.IGNORECASE | re.MULTILINE)


RULES: tuple[Rule, ...] = (
    Rule(
        incident_type="disk_full",
        title="Filesystem capacity exhausted",
        severity="critical",
        confidence=0.98,
        patterns=(_rx(r"no space left on device"), _rx(r"disk quota exceeded")),
        probable_cause="A filesystem or quota is full, preventing the application from writing data.",
        checks=(
            "Check filesystem usage with: df -h",
            "Check inode usage with: df -i",
            "Find large directories with: du -xhd1 / 2>/dev/null | sort -h",
        ),
        recommended_actions=(
            "Free or rotate non-essential data on the affected filesystem.",
            "Increase filesystem capacity or quota if growth is expected.",
            "Add disk-usage alerting before the filesystem reaches critical capacity.",
        ),
    ),
    Rule(
        incident_type="oom_kill",
        title="Process terminated by the OOM killer",
        severity="critical",
        confidence=0.98,
        patterns=(
            _rx(r"out of memory:.*killed process"),
            _rx(r"oom-kill"),
            _rx(r"killed process \d+ .* total-vm"),
        ),
        probable_cause="The host or container exhausted available memory and the kernel terminated a process.",
        checks=(
            "Inspect memory and swap with: free -h",
            "Inspect kernel OOM events with: journalctl -k | grep -i -E 'oom|killed process'",
            "Check high-memory processes with: ps aux --sort=-%mem | head",
        ),
        recommended_actions=(
            "Reduce the workload or fix excessive memory growth in the affected process.",
            "Increase the memory limit or host capacity when the workload is legitimate.",
            "Add memory saturation alerts and review container memory limits.",
        ),
    ),
    Rule(
        incident_type="nginx_upstream_refused",
        title="Reverse proxy cannot reach upstream service",
        severity="critical",
        confidence=0.97,
        patterns=(
            _rx(r"nginx.*connect\(\) failed \(111: connection refused\).*upstream"),
            _rx(r"connect\(\) failed .*connection refused.*while connecting to upstream"),
            _rx(r"upstream.*connection refused"),
        ),
        probable_cause="The reverse proxy is running, but its configured upstream service is not accepting connections.",
        checks=(
            "Verify the backend service is running: systemctl status <service>",
            "Verify the configured upstream port is listening: ss -lntp",
            "Test the backend locally: curl -v http://127.0.0.1:<port>/",
        ),
        recommended_actions=(
            "Start or restart the failed backend service after identifying why it stopped.",
            "Correct the proxy upstream host or port if configuration drift occurred.",
            "Add a service health check so backend failure is detected before proxy errors accumulate.",
        ),
    ),
    Rule(
        incident_type="connection_refused",
        title="Service connection refused",
        severity="critical",
        confidence=0.90,
        patterns=(_rx(r"connection refused"), _rx(r"connect: errno 111")),
        probable_cause="A client reached the target host but no service accepted the connection on the requested port.",
        checks=(
            "Confirm the target service is running.",
            "Check listening sockets with: ss -lntp",
            "Verify firewall, bind-address, container port, and service discovery configuration.",
        ),
        recommended_actions=(
            "Restore the unavailable service or correct the target host/port configuration.",
            "Add a readiness or dependency health check for the failing connection.",
        ),
    ),
    Rule(
        incident_type="dns_failure",
        title="DNS resolution failure",
        severity="warning",
        confidence=0.95,
        patterns=(
            _rx(r"temporary failure in name resolution"),
            _rx(r"name or service not known"),
            _rx(r"nxdomain"),
            _rx(r"could not resolve host"),
        ),
        probable_cause="The application cannot resolve a hostname through DNS.",
        checks=(
            "Resolve the hostname with: getent hosts <hostname>",
            "Inspect resolver configuration: cat /etc/resolv.conf",
            "Check configured DNS servers and network reachability.",
        ),
        recommended_actions=(
            "Correct the hostname if it is invalid or stale.",
            "Restore DNS/network connectivity if the resolver is unavailable.",
            "Review service-discovery TTLs and DNS dependencies for recurring failures.",
        ),
    ),
    Rule(
        incident_type="permission_denied",
        title="Permission denied",
        severity="warning",
        confidence=0.93,
        patterns=(_rx(r"permission denied"), _rx(r"errno 13")),
        probable_cause="The process lacks filesystem, socket, capability, or policy permissions required for the operation.",
        checks=(
            "Identify the user and group running the process.",
            "Inspect ownership and mode bits with: namei -l <path>",
            "Check SELinux/AppArmor/audit logs when mandatory access control is enabled.",
        ),
        recommended_actions=(
            "Grant only the minimum required ownership, group membership, mode, or capability.",
            "Correct service paths or policy rules rather than using broad chmod/chown changes.",
        ),
    ),
    Rule(
        incident_type="port_in_use",
        title="Network port already in use",
        severity="warning",
        confidence=0.96,
        patterns=(_rx(r"address already in use"), _rx(r"errno 98")),
        probable_cause="Another process is already bound to the requested address or port.",
        checks=(
            "Find the process using the port: ss -lntp",
            "Check for duplicate service instances or stale supervisors.",
        ),
        recommended_actions=(
            "Stop the unintended listener or configure one service to use a different port.",
            "Ensure orchestration does not start duplicate instances on the same host port.",
        ),
    ),
    Rule(
        incident_type="tls_certificate",
        title="TLS certificate validation failure",
        severity="warning",
        confidence=0.94,
        patterns=(
            _rx(r"certificate has expired"),
            _rx(r"certificate verify failed"),
            _rx(r"x509: certificate .* expired"),
        ),
        probable_cause="A TLS certificate is expired, untrusted, hostname-mismatched, or presented with an incomplete chain.",
        checks=(
            "Inspect the remote certificate with: openssl s_client -connect <host>:443 -servername <host>",
            "Verify certificate expiry, hostname, issuer, and intermediate chain.",
            "Check system time and trusted CA configuration.",
        ),
        recommended_actions=(
            "Renew or replace the invalid certificate and deploy the complete chain.",
            "Automate renewal monitoring before certificate expiry.",
        ),
    ),
    Rule(
        incident_type="timeout",
        title="Network or dependency timeout",
        severity="warning",
        confidence=0.86,
        patterns=(_rx(r"timed? out"), _rx(r"context deadline exceeded")),
        probable_cause="A network request or dependency exceeded its configured response deadline.",
        checks=(
            "Check target reachability and latency.",
            "Inspect dependency saturation, queue depth, and response times.",
            "Compare timeout settings with expected request duration.",
        ),
        recommended_actions=(
            "Restore or scale the slow dependency if it is unhealthy or saturated.",
            "Tune timeouts only after identifying the underlying latency source.",
        ),
    ),
)
