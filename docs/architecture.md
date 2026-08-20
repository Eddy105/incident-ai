# Architecture

IncidentAI is structured around a small, testable analysis pipeline:

```text
log file / stdin
       |
       v
   CLI input
       |
       v
 deterministic analyzer
       |
       +--> primary signature rules
       +--> evidence extraction
       +--> corroborating signal scoring
       |
       v
 IncidentAnalysis model
       |
       +--> human-readable formatter
       +--> JSON formatter
       |
       v
 terminal / automation
```

## Design goals

1. **Deterministic first:** known signatures produce reproducible output.
2. **Safe failure:** unknown incidents are explicitly marked unknown instead of receiving fabricated diagnoses.
3. **Automation friendly:** JSON and stable exit codes are first-class outputs.
4. **Offline by default:** logs stay on the machine unless an enrichment provider is explicitly enabled.
5. **Provider-ready:** LLM enrichment consumes a redacted `IncidentAnalysis` plus selected context, not raw unlimited logs by default.

## Correlated confidence scoring

Primary rules remain the only mechanism that can create an incident diagnosis. After a primary rule matches, IncidentAI checks a small set of incident-specific corroborating signatures across the same input window. Each distinct supporting signal adds one percentage point to the rule's base confidence, capped at 99%.

This separation is intentional: supporting context can strengthen an existing deterministic diagnosis but cannot create a diagnosis by itself. Existing single-signal behavior therefore remains backward compatible while richer incident windows can produce better-ranked results.

## Enrichment boundary

Remote enrichment sits after deterministic analysis:

```text
logs -> local analysis -> correlated confidence -> structured evidence -> redaction -> explicit --enrich -> OpenAI Responses API
```

The remote provider receives a minimal structured payload instead of the complete raw log. The deterministic result remains available when enrichment is disabled. Provider or network failures return a dedicated CLI error instead of silently changing the local diagnosis.
