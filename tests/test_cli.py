import json
from pathlib import Path

import pytest

from incident_ai.cli import main


def test_cli_json_output(tmp_path: Path, capsys) -> None:
    log = tmp_path / "app.log"
    log.write_text("Permission denied", encoding="utf-8")

    code = main(["analyze", str(log), "--json"])
    captured = capsys.readouterr()

    assert code == 1
    assert '"incident_type": "permission_denied"' in captured.out


def test_cli_all_json_output(tmp_path: Path, capsys) -> None:
    log = tmp_path / "app.log"
    log.write_text(
        "No space left on device\nCould not resolve host: api.internal",
        encoding="utf-8",
    )

    code = main(["analyze", str(log), "--all", "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert code == 2
    assert [item["incident_type"] for item in payload] == ["disk_full", "dns_failure"]


def test_cli_all_preserves_single_incident_shape_as_list(tmp_path: Path, capsys) -> None:
    log = tmp_path / "app.log"
    log.write_text("Permission denied", encoding="utf-8")

    code = main(["analyze", str(log), "--all", "--compact"])
    payload = json.loads(capsys.readouterr().out)

    assert code == 1
    assert len(payload) == 1
    assert payload[0]["incident_type"] == "permission_denied"


def test_cli_sarif_output(tmp_path: Path, capsys) -> None:
    log = tmp_path / "app.log"
    log.write_text("No space left on device", encoding="utf-8")

    code = main(["analyze", str(log), "--sarif"])
    payload = json.loads(capsys.readouterr().out)

    assert code == 2
    assert payload["version"] == "2.1.0"
    assert payload["runs"][0]["tool"]["driver"]["name"] == "IncidentAI"
    assert payload["runs"][0]["results"][0]["ruleId"] == "disk_full"
    assert payload["runs"][0]["results"][0]["level"] == "error"
    assert payload["runs"][0]["results"][0]["properties"]["confidence"] == 0.98


def test_cli_sarif_flattens_grouped_results(tmp_path: Path, capsys) -> None:
    log = tmp_path / "cluster.jsonl"
    log.write_text(
        '{"MESSAGE":"No space left on device","_HOSTNAME":"web-01"}\n'
        '{"MESSAGE":"Permission denied","_HOSTNAME":"web-02"}',
        encoding="utf-8",
    )

    code = main(["analyze", str(log), "--group-by", "host", "--sarif"])
    payload = json.loads(capsys.readouterr().out)

    assert code == 2
    results = payload["runs"][0]["results"]
    assert [result["ruleId"] for result in results] == ["disk_full", "permission_denied"]


def test_cli_sarif_rejects_compact(tmp_path: Path) -> None:
    log = tmp_path / "app.log"
    log.write_text("Permission denied", encoding="utf-8")

    with pytest.raises(SystemExit) as exc_info:
        main(["analyze", str(log), "--sarif", "--compact"])

    assert exc_info.value.code == 2


def test_cli_auto_detects_journald_json_lines(tmp_path: Path, capsys) -> None:
    log = tmp_path / "journal.jsonl"
    log.write_text(
        '{"MESSAGE":"No space left on device","_SYSTEMD_UNIT":"worker.service"}\n'
        '{"MESSAGE":"Could not resolve host: api.internal","_SYSTEMD_UNIT":"worker.service"}',
        encoding="utf-8",
    )

    code = main(["analyze", str(log), "--all", "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert code == 2
    assert [item["incident_type"] for item in payload] == ["disk_full", "dns_failure"]


def test_cli_include_context_keeps_journald_metadata_in_evidence(tmp_path: Path, capsys) -> None:
    log = tmp_path / "journal.jsonl"
    log.write_text(
        '{"MESSAGE":"No space left on device","_HOSTNAME":"web-01","_SYSTEMD_UNIT":"worker.service","_PID":"42"}',
        encoding="utf-8",
    )

    code = main(["analyze", str(log), "--json", "--include-context"])
    payload = json.loads(capsys.readouterr().out)

    assert code == 2
    assert payload["incident_type"] == "disk_full"
    assert payload["evidence"] == ["[host=web-01 unit=worker.service pid=42] No space left on device"]


def test_cli_filters_structured_logs_by_source(tmp_path: Path, capsys) -> None:
    log = tmp_path / "cluster.jsonl"
    log.write_text(
        '{"MESSAGE":"No space left on device","_HOSTNAME":"web-01","_SYSTEMD_UNIT":"api.service"}\n'
        '{"MESSAGE":"Permission denied","_HOSTNAME":"web-02","_SYSTEMD_UNIT":"api.service"}',
        encoding="utf-8",
    )

    code = main(["analyze", str(log), "--host", "web-02", "--unit", "api.service", "--json", "--include-context"])
    payload = json.loads(capsys.readouterr().out)

    assert code == 1
    assert payload["incident_type"] == "permission_denied"
    assert payload["evidence"] == ["[host=web-02 unit=api.service] Permission denied"]


def test_cli_source_filter_without_match_returns_empty_input(tmp_path: Path, capsys) -> None:
    log = tmp_path / "cluster.jsonl"
    log.write_text('{"MESSAGE":"Permission denied","_HOSTNAME":"web-01"}', encoding="utf-8")

    code = main(["analyze", str(log), "--host", "web-99", "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert code == 0
    assert payload["incident_type"] == "empty_input"


def test_cli_groups_structured_logs_before_correlation(tmp_path: Path, capsys) -> None:
    log = tmp_path / "cluster.jsonl"
    log.write_text(
        '{"MESSAGE":"No space left on device","_HOSTNAME":"web-01"}\n'
        '{"MESSAGE":"filesystem /var 100%","_HOSTNAME":"web-02"}\n'
        '{"MESSAGE":"Permission denied","_HOSTNAME":"web-02"}',
        encoding="utf-8",
    )

    code = main(["analyze", str(log), "--group-by", "host", "--all", "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert code == 2
    assert payload["group_by"] == "host"
    assert [group["value"] for group in payload["groups"]] == ["web-01", "web-02"]
    web_01 = payload["groups"][0]["analyses"]
    web_02 = payload["groups"][1]["analyses"]
    assert web_01[0]["incident_type"] == "disk_full"
    assert web_01[0]["confidence"] == 0.98
    assert web_02[0]["incident_type"] == "permission_denied"


def test_cli_group_by_rejects_plain_text(tmp_path: Path) -> None:
    log = tmp_path / "app.log"
    log.write_text("Permission denied", encoding="utf-8")

    with pytest.raises(SystemExit) as exc_info:
        main(["analyze", str(log), "--group-by", "host", "--input-format", "text"])

    assert exc_info.value.code == 3


def test_cli_jsonl_reports_malformed_input(tmp_path: Path) -> None:
    log = tmp_path / "broken.jsonl"
    log.write_text('{"message":"Permission denied"}\nnot-json', encoding="utf-8")

    with pytest.raises(SystemExit) as exc_info:
        main(["analyze", str(log), "--input-format", "jsonl"])

    assert exc_info.value.code == 3


def test_cli_critical_exit_code(tmp_path: Path) -> None:
    log = tmp_path / "app.log"
    log.write_text("No space left on device", encoding="utf-8")
    assert main(["analyze", str(log)]) == 2


def test_cli_unknown_exit_code_is_zero(tmp_path: Path) -> None:
    log = tmp_path / "app.log"
    log.write_text("unclassified signal", encoding="utf-8")
    assert main(["analyze", str(log)]) == 0


def test_cli_redacts_output_without_changing_exit_code(tmp_path: Path, capsys) -> None:
    log = tmp_path / "app.log"
    log.write_text("Permission denied from 10.0.0.5 token=super-secret-value", encoding="utf-8")

    code = main(["analyze", str(log), "--json", "--redact"])
    payload = json.loads(capsys.readouterr().out)

    assert code == 1
    assert "10.0.0.5" not in json.dumps(payload)
    assert "super-secret-value" not in json.dumps(payload)
    assert "<IP>" in payload["evidence"][0]
    assert "<REDACTED>" in payload["evidence"][0]


def test_cli_redacts_grouped_sarif_output(tmp_path: Path, capsys) -> None:
    log = tmp_path / "cluster.jsonl"
    log.write_text(
        '{"MESSAGE":"Permission denied from 10.0.0.5 token=super-secret-value","_HOSTNAME":"web-01"}',
        encoding="utf-8",
    )

    code = main(["analyze", str(log), "--group-by", "host", "--sarif", "--redact"])
    payload = json.loads(capsys.readouterr().out)

    assert code == 1
    serialized = json.dumps(payload)
    assert "10.0.0.5" not in serialized
    assert "super-secret-value" not in serialized


def test_cli_webhook_requires_redaction(tmp_path: Path) -> None:
    log = tmp_path / "app.log"
    log.write_text("Permission denied", encoding="utf-8")

    with pytest.raises(SystemExit) as exc_info:
        main(["analyze", str(log), "--webhook", "https://example.test/incidents"])

    assert exc_info.value.code == 2


def test_cli_webhook_sends_redacted_structured_analysis(tmp_path: Path, monkeypatch) -> None:
    log = tmp_path / "app.log"
    log.write_text("Permission denied from 10.0.0.5 token=super-secret-value", encoding="utf-8")
    captured = {}

    def fake_send(payload, url):
        captured["payload"] = payload
        captured["url"] = url

    monkeypatch.setattr("incident_ai.cli.send_webhook", fake_send)

    code = main(["analyze", str(log), "--redact", "--webhook", "https://example.test/incidents"])

    assert code == 1
    assert captured["url"] == "https://example.test/incidents"
    serialized = json.dumps(captured["payload"])
    assert "10.0.0.5" not in serialized
    assert "super-secret-value" not in serialized
    assert captured["payload"]["incident_type"] == "permission_denied"
