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
       +--> signature rules
       +--> evidence extraction
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
4. **Offline by default:** logs stay on the machine unless a future enrichment provider is explicitly enabled.
5. **Provider-ready:** future LLM enrichment should consume a redacted `IncidentAnalysis` plus selected context, not raw unlimited logs by default.

## Planned enrichment boundary

Remote enrichment sits after deterministic analysis:

```text
logs -> local analysis -> structured evidence -> redaction -> explicit --enrich -> OpenAI Responses API
```

The remote provider receives a minimal structured payload instead of the complete raw log. The deterministic result remains available when enrichment is disabled. Provider or network failures return a dedicated CLI error instead of silently changing the local diagnosis.
