# Webhook dry-run

`--webhook-dry-run` validates an outbound webhook configuration and the exact payload metadata without sending an HTTP request.

Use it with the same safety requirements as a real webhook:

```bash
incident-ai analyze app.log --json --redact \
  --webhook https://ops.example.test/incidents \
  --webhook-dry-run
```

The command keeps the normal incident output on stdout. The validation result is written to stderr and includes:

- webhook URL
- deterministic event ID for the serialized payload
- whether HMAC signing is configured
- configured retry count
- configured timeout
- `sent: false`

The dry-run performs the same webhook destination validation as a real delivery, including DNS resolution and rejection of non-public destinations, embedded credentials, and non-HTTP(S) schemes. It never creates a POST request and never invokes the network transport.

The event ID is derived from the exact serialized JSON payload, so a dry-run can be used in CI to verify that the receiver-side idempotency key will be stable before enabling delivery.
