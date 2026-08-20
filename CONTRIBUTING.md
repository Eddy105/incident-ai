# Contributing

Contributions are welcome, especially new incident signatures backed by real-world evidence and regression tests.

## Workflow

1. Create a focused branch.
2. Add or update tests for the behavior being changed.
3. Run `make check`.
4. Keep diagnosis text actionable and vendor-neutral where possible.
5. Open a pull request explaining the incident signature and why the proposed diagnosis is safe.

For a new rule, include representative synthetic log lines. Do not commit customer logs, credentials, access tokens, private hostnames, or personal data.
