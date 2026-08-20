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
