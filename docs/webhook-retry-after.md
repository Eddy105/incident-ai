# Webhook `Retry-After` handling

IncidentAI honors a numeric HTTP `Retry-After` header when a retryable webhook response asks the sender to wait before trying again.

The header is used for HTTP `429 Too Many Requests` and `5xx` responses. A valid value overrides the normal exponential backoff for that attempt.

```text
HTTP/1.1 429 Too Many Requests
Retry-After: 3
```

IncidentAI waits three seconds before the next attempt. Server-provided delays are capped at 60 seconds so a remote endpoint cannot turn the bounded retry feature into an unbounded local sleep.

If the header is missing, negative, or not a numeric delay, IncidentAI falls back to its normal exponential backoff. Network errors and timeouts continue to use the local backoff because they do not provide an HTTP response header.

The existing retry limit remains unchanged: `--webhook-retries` controls the maximum number of retries after the initial request, and retries remain disabled by default.
