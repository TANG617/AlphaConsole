from __future__ import annotations

from datetime import datetime
import socketserver
import threading

from alphaconsole.printing import (
    GENERIC_58MM,
    EscPosBytesFileAdapter,
    EscPosSocketPrinterAdapter,
    MemoryPrinterAdapter,
)
from alphaconsole.printing.test_page import build_test_receipt
from alphaconsole.rendering import RECEIPT_32, RECEIPT_42


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


def test_socket_adapter_returns_delivery_diagnostics() -> None:
    with _RecordingTCPServer(("127.0.0.1", 0), _RecordingHandler) as server:
        worker = threading.Thread(target=server.handle_request, daemon=True)
        worker.start()
        adapter = EscPosSocketPrinterAdapter(
            target_id="receipt_printer",
            host="127.0.0.1",
            port=server.server_address[1],
            printer_profile=GENERIC_58MM,
            printer_profile_name=GENERIC_58MM.profile_id,
            render_profile_name=RECEIPT_32.name,
        )

        diagnostics = adapter.deliver(
            build_test_receipt(
                RECEIPT_32,
                issue_id="socket-diag",
                rendered_at=datetime(2026, 4, 23, 12, 0, 0),
            )
        )
        worker.join(timeout=2)

    assert server.received.startswith(b"\x1b@")
    assert diagnostics.adapter_name == "escpos_socket"
    assert diagnostics.target_id == "receipt_printer"
    assert diagnostics.printer_profile_name == "generic_58mm"
    assert diagnostics.render_profile_name == "receipt_32"
    assert diagnostics.bytes_length is not None
    assert diagnostics.duration_ms is not None
    assert diagnostics.succeeded is True
    assert diagnostics.error_text is None


def test_bytes_file_adapter_returns_delivery_diagnostics(tmp_path) -> None:
    adapter = EscPosBytesFileAdapter(
        target_id="bytes_debug",
        output_dir=tmp_path / "escpos",
        printer_profile=GENERIC_58MM,
        printer_profile_name=GENERIC_58MM.profile_id,
        render_profile_name=RECEIPT_32.name,
    )

    diagnostics = adapter.deliver(
        build_test_receipt(
            RECEIPT_32,
            issue_id="bytes-diag",
            rendered_at=datetime(2026, 4, 23, 12, 0, 0),
        )
    )

    assert diagnostics.adapter_name == "escpos_bytes_file"
    assert diagnostics.target_id == "bytes_debug"
    assert diagnostics.printer_profile_name == "generic_58mm"
    assert diagnostics.render_profile_name == "receipt_32"
    assert diagnostics.bytes_length is not None
    assert diagnostics.bytes_length > 0
    assert diagnostics.succeeded is True
    assert (tmp_path / "escpos" / "bytes-diag__bytes_debug.bin").exists()


def test_dry_run_memory_adapter_returns_minimal_delivery_diagnostics() -> None:
    adapter = MemoryPrinterAdapter(
        target_id="memory_target",
        render_profile_name=RECEIPT_42.name,
    )

    diagnostics = adapter.deliver(build_test_receipt(RECEIPT_42))

    assert diagnostics.adapter_name == "memory"
    assert diagnostics.target_id == "memory_target"
    assert diagnostics.bytes_length is None
    assert diagnostics.duration_ms is None
    assert diagnostics.succeeded is True
