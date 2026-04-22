from __future__ import annotations

from pathlib import Path

from alphaconsole.cli import main


def test_cli_targets_list_outputs_targets_and_default(capsys) -> None:
    exit_code = main(["targets", "list", "--config", "examples/basic.toml"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "stdout_default" in captured.out
    assert "(default)" in captured.out


def test_cli_print_test_page_bytes_debug_creates_bin_file(tmp_path: Path) -> None:
    config_path = _write_temp_basic_config(tmp_path)

    exit_code = main(
        [
            "print",
            "test-page",
            "--config",
            str(config_path),
            "--target-id",
            "bytes_debug",
        ]
    )

    assert exit_code == 0
    assert len(list((tmp_path / "escpos").glob("*.bin"))) == 1


def test_cli_publish_scheduled_with_target_id_writes_bytes_file(tmp_path: Path) -> None:
    config_path = _write_temp_basic_config(tmp_path)

    exit_code = main(
        [
            "publish",
            "scheduled",
            "--config",
            str(config_path),
            "--slot-id",
            "noon",
            "--target-id",
            "bytes_debug",
            "--now",
            "2026-04-22T12:00:00",
        ]
    )

    assert exit_code == 0
    assert len(list((tmp_path / "escpos").glob("*.bin"))) == 1


def test_cli_runtime_once_with_target_id_writes_bytes_file(
    tmp_path: Path,
    capsys,
) -> None:
    config_path = _write_temp_basic_config(tmp_path)
    state_path = tmp_path / "state.db"

    exit_code = main(
        [
            "runtime",
            "once",
            "--config",
            str(config_path),
            "--state",
            str(state_path),
            "--target-id",
            "bytes_debug",
            "--now",
            "2026-04-22T12:00:00",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "published: 1" in captured.out
    assert len(list((tmp_path / "escpos").glob("*.bin"))) == 1


def _write_temp_basic_config(tmp_path: Path) -> Path:
    config_text = Path("examples/basic.toml").read_text(encoding="utf-8")
    config_text = config_text.replace(
        'output_dir = "var/escpos"',
        f'output_dir = "{(tmp_path / "escpos").as_posix()}"',
    )
    config_path = tmp_path / "basic.toml"
    config_path.write_text(config_text, encoding="utf-8")
    return config_path
