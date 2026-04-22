from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sqlite3
import socketserver
import threading

from alphaconsole.application import AutomationRuntimeService
from alphaconsole.runtime import build_runtime_from_config
from alphaconsole.state import SQLiteStateStore


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


def test_end_to_end_hardware_runtime_delivers_to_fake_socket_and_dedupes(
    tmp_path: Path,
) -> None:
    with _RecordingTCPServer(("127.0.0.1", 0), _RecordingHandler) as server:
        config_path = _write_temp_network_config(tmp_path, server.server_address[1])
        bundle = build_runtime_from_config(config_path)
        service = AutomationRuntimeService(
            assembler=bundle.issue_assembler,
            print_service=bundle.print_service,
        )
        state_path = tmp_path / "state.db"
        store = SQLiteStateStore(state_path)
        target = bundle.printer_targets_by_id[bundle.default_printer_target_id]
        adapter = bundle.adapter_factory.create_for_target(target)

        worker = threading.Thread(target=server.handle_request, daemon=True)
        worker.start()
        first_result = service.run_once(
            slots=tuple(bundle.slots_by_id.values()),
            apps=tuple(bundle.apps_by_id.values()),
            adapter=adapter,
            store=store,
            now=datetime(2026, 4, 22, 12, 0, 0),
            profile=bundle.default_profile,
            catchup_seconds=bundle.runtime_catchup_seconds,
        )
        worker.join(timeout=2)

        assert len(first_result.published_issue_ids) == 1
        assert server.received.startswith(b"\x1b@")

        restarted_bundle = build_runtime_from_config(config_path)
        restarted_service = AutomationRuntimeService(
            assembler=restarted_bundle.issue_assembler,
            print_service=restarted_bundle.print_service,
        )
        restarted_store = SQLiteStateStore(state_path)
        restarted_store.set_last_tick_at(datetime(2026, 4, 22, 11, 59, 0))
        second_result = restarted_service.run_once(
            slots=tuple(restarted_bundle.slots_by_id.values()),
            apps=tuple(restarted_bundle.apps_by_id.values()),
            adapter=restarted_bundle.adapter_factory.create_for_target(
                restarted_bundle.printer_targets_by_id[
                    restarted_bundle.default_printer_target_id
                ]
            ),
            store=restarted_store,
            now=datetime(2026, 4, 22, 12, 0, 30),
            profile=restarted_bundle.default_profile,
            catchup_seconds=restarted_bundle.runtime_catchup_seconds,
        )

        runs = restarted_store.list_publication_runs(limit=5)
        with sqlite3.connect(state_path) as conn:
            attempt_count = conn.execute(
                "SELECT COUNT(*) FROM delivery_attempts"
            ).fetchone()[0]

        assert second_result.published_issue_ids == ()
        assert len(second_result.skipped_existing_occurrences) == 1
        assert runs[0].status == "delivered"
        assert attempt_count == 1


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
