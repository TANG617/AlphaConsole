from __future__ import annotations

from datetime import datetime
import socket
import threading

from alphaconsole.domain import TriggerMode
from alphaconsole.printing import EscposTcpPrinterAdapter, RenderedReceipt
from alphaconsole.printing.escpos_tcp_adapter import (
    ESC_INIT,
    FS_SELECT_CHINESE_MODE,
    GS_PARTIAL_CUT,
)


def make_receipt(text: str = "午餐\n[ ] 喝水") -> RenderedReceipt:
    return RenderedReceipt(
        issue_id="issue-1",
        publication_slot_id="noon",
        trigger_mode=TriggerMode.SCHEDULED,
        profile_name="receipt_42",
        text=text,
        rendered_at=datetime(2026, 4, 28, 12, 0, 0),
    )


def test_escpos_tcp_adapter_builds_gb18030_payload() -> None:
    adapter = EscposTcpPrinterAdapter(
        host="127.0.0.1",
        encoding="gb18030",
        feed_lines=2,
    )

    payload = adapter._build_payload(make_receipt().text)

    assert payload.startswith(ESC_INIT + FS_SELECT_CHINESE_MODE)
    assert "午餐".encode("gb18030") in payload
    assert payload.endswith(b"\n\n" + GS_PARTIAL_CUT)


def test_escpos_tcp_adapter_can_disable_cut() -> None:
    adapter = EscposTcpPrinterAdapter(
        host="127.0.0.1",
        cut=False,
        feed_lines=0,
    )

    payload = adapter._build_payload(make_receipt(text="hello").text)

    assert GS_PARTIAL_CUT not in payload
    assert payload.endswith(b"hello\n")


def test_escpos_tcp_adapter_delivers_to_tcp_socket() -> None:
    received_payloads: list[bytes] = []
    ready = threading.Event()

    def run_server(server_socket: socket.socket) -> None:
        ready.set()
        connection, _address = server_socket.accept()
        with connection:
            received_payloads.append(connection.recv(4096))

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind(("127.0.0.1", 0))
        server_socket.listen(1)
        host, port = server_socket.getsockname()
        thread = threading.Thread(
            target=run_server,
            args=(server_socket,),
            daemon=True,
        )
        thread.start()
        ready.wait(timeout=1)

        adapter = EscposTcpPrinterAdapter(
            host=host,
            port=port,
            cut=False,
            feed_lines=0,
        )
        adapter.deliver(make_receipt(text="hello"))
        thread.join(timeout=1)

    assert received_payloads == [ESC_INIT + FS_SELECT_CHINESE_MODE + b"hello\n"]
