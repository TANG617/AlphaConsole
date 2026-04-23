from __future__ import annotations

from datetime import datetime
from pathlib import Path
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


def test_calibrated_hardware_runtime_writes_diagnostics_to_sqlite_and_dedupes(
    tmp_path: Path,
) -> None:
    with _RecordingTCPServer(("127.0.0.1", 0), _RecordingHandler) as server:
        config_path = _write_temp_network_config(tmp_path, server.server_address[1])
        bundle = build_runtime_from_config(config_path)
        service = AutomationRuntimeService(
            assembler=bundle.issue_assembler,
            print_service=bundle.print_service,
        )
        store = SQLiteStateStore(tmp_path / "state.db")
        target = bundle.target_resolver.require("receipt_printer")
        adapter = bundle.adapter_factory.create_for_target(target)

        worker = threading.Thread(target=server.handle_request, daemon=True)
        worker.start()
        first = service.run_once(
            slots=tuple(bundle.slots_by_id.values()),
            apps=tuple(bundle.apps_by_id.values()),
            adapter=adapter,
            store=store,
            now=datetime(2026, 4, 22, 12, 0, 0),
            profile=target.render_profile,
            catchup_seconds=bundle.runtime_catchup_seconds,
        )
        worker.join(timeout=2)

        latest_attempt = store.get_latest_delivery_attempt()
        latest_run = store.get_latest_publication_run()

        assert len(first.published_issue_ids) == 1
        assert server.received.startswith(b"\x1b@")
        assert latest_attempt is not None
        assert latest_attempt.target_id == "receipt_printer"
        assert latest_attempt.printer_profile_name == "generic_58mm"
        assert latest_attempt.render_profile_name == "receipt_32"
        assert latest_attempt.bytes_length is not None
        assert latest_attempt.bytes_length > 0
        assert latest_attempt.duration_ms is not None
        assert latest_run is not None
        assert latest_run.target_id == "receipt_printer"
        assert latest_run.printer_profile_name == "generic_58mm"

        store.set_last_tick_at(datetime(2026, 4, 22, 11, 59, 0))
        second = service.run_once(
            slots=tuple(bundle.slots_by_id.values()),
            apps=tuple(bundle.apps_by_id.values()),
            adapter=bundle.adapter_factory.create_for_target(
                bundle.target_resolver.require("receipt_printer")
            ),
            store=store,
            now=datetime(2026, 4, 22, 12, 0, 30),
            profile=target.render_profile,
            catchup_seconds=bundle.runtime_catchup_seconds,
        )

        assert second.published_issue_ids == ()
        assert len(second.skipped_existing_occurrences) == 1
        assert len(store.list_delivery_attempts(limit=10)) == 1


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
