from pathlib import Path

from incident_ai.cli import main


def test_cli_json_output(tmp_path: Path, capsys) -> None:
    log = tmp_path / "app.log"
    log.write_text("Permission denied", encoding="utf-8")

    code = main(["analyze", str(log), "--json"])
    captured = capsys.readouterr()

    assert code == 1
    assert '"incident_type": "permission_denied"' in captured.out


def test_cli_critical_exit_code(tmp_path: Path) -> None:
    log = tmp_path / "app.log"
    log.write_text("No space left on device", encoding="utf-8")
    assert main(["analyze", str(log)]) == 2


def test_cli_unknown_exit_code_is_zero(tmp_path: Path) -> None:
    log = tmp_path / "app.log"
    log.write_text("unclassified signal", encoding="utf-8")
    assert main(["analyze", str(log)]) == 0
