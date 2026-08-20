# Security Policy

## Reporting a vulnerability

Please report security-sensitive defects privately to the repository owner rather than opening a public issue containing exploit details or sensitive logs.

## Log privacy

IncidentAI's default analyzer is offline and does not transmit input. Users remain responsible for protecting log files, which can contain credentials, tokens, private addresses, usernames, request parameters, or personal data.

Remote enrichment is an explicit opt-in. Before any selected incident context reaches an enrichment provider, IncidentAI applies its redaction pipeline to titles, probable causes, evidence, checks, and recommended actions. The local analyzer never sends raw logs to the provider.
