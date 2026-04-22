from __future__ import annotations

from pathlib import Path

from alphaconsole.cli import main


def test_cli_runtime_once_stdout_runs_and_prints_summary(capsys, tmp_path: Path) -> None:
    state_path = tmp_path / "state.db"

    exit_code = main(
        [
            "runtime",
            "once",
            "--config",
            "examples/basic.toml",
            "--state",
            str(state_path),
            "--adapter",
            "stdout",
            "--now",
            "2026-04-22T12:00:00",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "[Lunch]" in captured.out
    assert "due: 1" in captured.out
    assert state_path.exists()


def test_cli_runtime_once_file_writes_output(tmp_path: Path, capsys) -> None:
    state_path = tmp_path / "state.db"
    output_dir = tmp_path / "out"

    exit_code = main(
        [
            "runtime",
            "once",
            "--config",
            "examples/basic.toml",
            "--state",
            str(state_path),
            "--adapter",
            "file",
            "--output-dir",
            str(output_dir),
            "--now",
            "2026-04-22T12:00:00",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "published: 1" in captured.out
    assert len(list(output_dir.glob("*.txt"))) == 1


def test_cli_runtime_loop_runs_with_iterations(tmp_path: Path, capsys) -> None:
    state_path = tmp_path / "state.db"
    output_dir = tmp_path / "out"

    exit_code = main(
        [
            "runtime",
            "loop",
            "--config",
            "examples/basic.toml",
            "--state",
            str(state_path),
            "--adapter",
            "file",
            "--output-dir",
            str(output_dir),
            "--now",
            "2026-04-22T12:00:00",
            "--poll-interval",
            "30",
            "--iterations",
            "2",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "runtime loop completed: 2 iterations" in captured.out
    assert len(list(output_dir.glob("*.txt"))) == 1


def test_cli_runs_list_and_limit(tmp_path: Path, capsys) -> None:
    state_path = tmp_path / "state.db"
    output_dir = tmp_path / "out"
    main(
        [
            "runtime",
            "once",
            "--config",
            "examples/basic.toml",
            "--state",
            str(state_path),
            "--adapter",
            "file",
            "--output-dir",
            str(output_dir),
            "--now",
            "2026-04-22T12:00:00",
        ]
    )

    exit_code = main(["runs", "list", "--state", str(state_path), "--limit", "1"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "slot=noon" in captured.out


def test_cli_runs_latest_handles_existing_and_empty_state(tmp_path: Path, capsys) -> None:
    empty_state = tmp_path / "empty.db"
    exit_code = main(["runs", "latest", "--state", str(empty_state)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "No publication runs found." in captured.out

    state_path = tmp_path / "state.db"
    output_dir = tmp_path / "out"
    main(
        [
            "runtime",
            "once",
            "--config",
            "examples/basic.toml",
            "--state",
            str(state_path),
            "--adapter",
            "file",
            "--output-dir",
            str(output_dir),
            "--now",
            "2026-04-22T12:00:00",
        ]
    )

    exit_code = main(["runs", "latest", "--state", str(state_path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "slot=noon" in captured.out
