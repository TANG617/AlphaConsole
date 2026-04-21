from __future__ import annotations

from pathlib import Path

from alphaconsole.cli import main


def test_cli_list_outputs_slots_and_apps(capsys) -> None:
    exit_code = main(["list", "--config", "examples/basic.toml"])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "slots:" in captured.out
    assert "noon" in captured.out
    assert "apps:" in captured.out
    assert "lunch" in captured.out


def test_cli_preview_scheduled_outputs_issue_text_without_writing_file(
    tmp_path: Path,
    capsys,
) -> None:
    config_path = tmp_path / "runtime.toml"
    config_path.write_text(Path("examples/basic.toml").read_text(encoding="utf-8"))

    exit_code = main(
        [
            "preview",
            "scheduled",
            "--config",
            str(config_path),
            "--slot-id",
            "noon",
            "--now",
            "2026-04-21T12:00:00",
            "--sequence-of-day",
            "2",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "DATE: 2026-04-21" in captured.out
    assert "[Lunch]" in captured.out
    assert "[Afternoon Reset]" in captured.out
    assert list(tmp_path.iterdir()) == [config_path]


def test_cli_publish_scheduled_stdout_outputs_receipt(capsys) -> None:
    exit_code = main(
        [
            "publish",
            "scheduled",
            "--config",
            "examples/basic.toml",
            "--slot-id",
            "noon",
            "--adapter",
            "stdout",
            "--now",
            "2026-04-21T12:00:00",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "DATE: 2026-04-21" in captured.out
    assert "[Lunch]" in captured.out


def test_cli_publish_scheduled_file_writes_output_file(tmp_path: Path) -> None:
    exit_code = main(
        [
            "publish",
            "scheduled",
            "--config",
            "examples/basic.toml",
            "--slot-id",
            "noon",
            "--adapter",
            "file",
            "--output-dir",
            str(tmp_path),
            "--now",
            "2026-04-21T12:00:00",
        ]
    )

    written_files = list(tmp_path.glob("*.txt"))

    assert exit_code == 0
    assert len(written_files) == 1
    assert written_files[0].read_text(encoding="utf-8")


def test_cli_publish_immediate_outputs_receipt(capsys) -> None:
    exit_code = main(
        [
            "publish",
            "immediate",
            "--config",
            "examples/basic.toml",
            "--app-id",
            "lunch",
            "--adapter",
            "stdout",
            "--now",
            "2026-04-21T12:05:00",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "TRIGGER: immediate" in captured.out
    assert "[Lunch]" in captured.out
