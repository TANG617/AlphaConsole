from __future__ import annotations

from pathlib import Path
import socketserver
import threading

from alphaconsole.cli import main


class _RecordingTCPServer(socketserver.TCPServer):
    allow_reuse_address = True

    def __init__(self, server_address, handler_class):
        super().__init__(server_address, handler_class)
        self.received = b""


class _RecordingHandler(socketserver.BaseRequestHandler):
    def handle(self) -> None:
        while True:
            chunk = self.request.recv(4096)
            if not chunk:
                break
            self.server.received += chunk


def test_cli_targets_inspect_outputs_target_summary(capsys) -> None:
    exit_code = main(
        [
            "targets",
            "inspect",
            "--config",
            "examples/basic.toml",
            "--target-id",
            "stdout_default",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "target_id: stdout_default" in captured.out
    assert "printer_profile: generic_58mm" in captured.out
    assert "render_profile: receipt_32" in captured.out


def test_cli_targets_ping_succeeds_for_socket_target(tmp_path: Path, capsys) -> None:
    with _RecordingTCPServer(("127.0.0.1", 0), _RecordingHandler) as server:
        config_path = _write_temp_network_config(tmp_path, server.server_address[1])

        exit_code = main(
            [
                "targets",
                "ping",
                "--config",
                str(config_path),
                "--target-id",
                "receipt_printer",
            ]
        )
        captured = capsys.readouterr()

    assert exit_code == 0
    assert "OK target=receipt_printer" in captured.out


def test_cli_targets_ping_rejects_non_socket_target(capsys) -> None:
    exit_code = main(
        [
            "targets",
            "ping",
            "--config",
            "examples/basic.toml",
            "--target-id",
            "stdout_default",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "does not support ping" in captured.err


def test_cli_print_calibration_writes_bytes_file(tmp_path: Path) -> None:
    config_path = _write_temp_bytes_debug_config(tmp_path)

    exit_code = main(
        [
            "print",
            "calibration",
            "--config",
            str(config_path),
            "--target-id",
            "bytes_debug",
        ]
    )

    assert exit_code == 0
    assert len(list((tmp_path / "escpos").glob("*.bin"))) == 1


def test_cli_deliveries_list_and_latest_show_delivery_metadata(
    tmp_path: Path,
    capsys,
) -> None:
    config_path = _write_temp_bytes_debug_config(tmp_path)
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
    assert exit_code == 0

    exit_code = main(["deliveries", "list", "--state", str(state_path), "--limit", "5"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "adapter=escpos_bytes_file" in captured.out
    assert "target=bytes_debug" in captured.out

    exit_code = main(["deliveries", "latest", "--state", str(state_path)])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "target=bytes_debug" in captured.out
    assert "bytes=" in captured.out


def test_cli_runtime_once_profile_override_records_actual_delivery_profile(
    tmp_path: Path,
    capsys,
) -> None:
    config_path = _write_temp_bytes_debug_config(tmp_path)
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
            "--profile",
            "receipt42",
            "--now",
            "2026-04-22T12:00:00",
        ]
    )
    assert exit_code == 0

    exit_code = main(["deliveries", "latest", "--state", str(state_path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "target=bytes_debug" in captured.out
    assert "render_profile=receipt_42" in captured.out
    assert "render_profile=receipt_32" not in captured.out


def _write_temp_network_config(tmp_path: Path, port: int) -> Path:
    config_text = Path("examples/printer-network.toml").read_text(encoding="utf-8")
    config_text = config_text.replace("port = 19100", f"port = {port}")
    config_text = config_text.replace(
        'output_dir = "var/escpos"',
        f'output_dir = "{(tmp_path / "escpos").as_posix()}"',
    )
    config_path = tmp_path / "printer-network.toml"
    config_path.write_text(config_text, encoding="utf-8")
    return config_path


def _write_temp_bytes_debug_config(tmp_path: Path) -> Path:
    config_text = Path("examples/printer-bytes-debug.toml").read_text(encoding="utf-8")
    config_text = config_text.replace(
        'output_dir = "var/escpos"',
        f'output_dir = "{(tmp_path / "escpos").as_posix()}"',
    )
    config_path = tmp_path / "printer-bytes-debug.toml"
    config_path.write_text(config_text, encoding="utf-8")
    return config_path
