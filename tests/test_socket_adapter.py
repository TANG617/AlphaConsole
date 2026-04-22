from __future__ import annotations

from datetime import datetime
import socketserver
import threading

import pytest

from alphaconsole.printing import EscPosSocketPrinterAdapter, HardwarePrintOptions
from alphaconsole.printing.test_page import build_test_receipt
from alphaconsole.rendering import RECEIPT_42


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


def test_socket_adapter_delivers_non_empty_bytes_to_tcp_server() -> None:
    with _RecordingTCPServer(("127.0.0.1", 0), _RecordingHandler) as server:
        worker = threading.Thread(target=server.handle_request, daemon=True)
        worker.start()

        adapter = EscPosSocketPrinterAdapter(
            target_id="receipt_printer",
            host="127.0.0.1",
            port=server.server_address[1],
            hardware_options=HardwarePrintOptions(cut=True),
        )
        adapter.deliver(
            build_test_receipt(
                RECEIPT_42,
                issue_id="socket-test",
                rendered_at=datetime(2026, 4, 22, 12, 0, 0),
            )
        )

        worker.join(timeout=2)

        assert server.received
        assert server.received.startswith(b"\x1b@")


def test_socket_adapter_bubbles_up_connection_failure_without_retry(monkeypatch) -> None:
    attempts = {"count": 0}

    def raising_create_connection(*args, **kwargs):
        attempts["count"] += 1
        raise TimeoutError("timed out")

    monkeypatch.setattr(
        "alphaconsole.printing.socket_adapter.socket.create_connection",
        raising_create_connection,
    )
    adapter = EscPosSocketPrinterAdapter(
        target_id="receipt_printer",
        host="127.0.0.1",
        port=19100,
    )

    with pytest.raises(TimeoutError, match="timed out"):
        adapter.deliver(build_test_receipt(RECEIPT_42))

    assert attempts["count"] == 1
