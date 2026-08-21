# Webhook Retry Safety Limits

IncidentAI keeps webhook retries explicitly bounded.

- `--webhook-retries` defaults to `0`.
- The maximum accepted retry count is `8`.
- A retry count above `8` is rejected before a request is sent.
- Webhook timeouts must be greater than zero.
- Retry delays remain bounded independently: `Retry-After` values are capped at 60 seconds and exponential backoff is capped at 4 seconds.
- The same deterministic `X-IncidentAI-Event-ID` is reused for all attempts of one payload.
- When HMAC signing is enabled, each attempt receives a fresh timestamp and signature.

These limits prevent a configuration mistake from turning the optional retry feature into an effectively unbounded delivery loop.
