# Webhook retries

IncidentAI keeps webhook retries opt-in so existing integrations retain their one-request behavior.

## CLI

Use `--webhook-retries` to retry transient delivery failures:

```bash
incident-ai analyze app.log --redact \
  --webhook https://ops.example.test/incidents \
  --webhook-retries 2
```

The value is the maximum number of retries after the initial request. With `2`, IncidentAI can make up to three delivery attempts.

Retries use bounded exponential backoff: 0.5 seconds, then 1 second, then up to a 4-second cap for later attempts.

## Retried failures

IncidentAI retries only failures that are plausibly transient:

- HTTP `429 Too Many Requests`
- HTTP `5xx` responses
- network-level `URLError` failures
- request timeouts

Client errors such as HTTP 4xx responses other than 429 are not retried. Redirects remain rejected and SSRF destination validation is performed before any request attempt.

## Idempotency and signatures

Every retry uses the same serialized request body and therefore the same `X-IncidentAI-Event-ID`. Receivers can use that value as an idempotency key to safely suppress duplicate processing.

When HMAC signing is enabled, each attempt receives a fresh timestamp and signature over that timestamp plus the unchanged request body. This lets receivers enforce replay windows independently for each delivery attempt.

Retries are disabled by default. Negative retry counts are rejected.
