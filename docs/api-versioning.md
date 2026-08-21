# Local API versioning

The local HTTP API exposes `GET /version` so monitoring integrations can verify compatibility without parsing package metadata.

```console
$ curl -sS http://127.0.0.1:8080/version
{"api_version":"1","version":"0.12.2"}
```

- `api_version` is the API major version. It changes only for intentional HTTP API compatibility breaks.
- `version` is the installed IncidentAI package version.

Consumers should use `api_version` for compatibility decisions and treat the package `version` as diagnostic release metadata. The endpoint does not require authentication and should therefore only be exposed on trusted networks or through an authenticated reverse proxy.
