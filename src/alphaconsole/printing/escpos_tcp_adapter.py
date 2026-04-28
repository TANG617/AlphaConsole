from __future__ import annotations

from dataclasses import dataclass
import socket

from .adapter import PrinterAdapter
from .artifact import RenderedReceipt


ESC_INIT = b"\x1b@"
FS_SELECT_CHINESE_MODE = b"\x1c&"
GS_PARTIAL_CUT = b"\x1dVB\x00"
_SUPPORTED_ENCODINGS = {"gb18030", "gb-18030"}


@dataclass(slots=True)
class EscposTcpPrinterAdapter(PrinterAdapter):
    host: str
    port: int = 9100
    timeout_seconds: float = 5.0
    encoding: str = "gb18030"
    cut: bool = True
    feed_lines: int = 3
    name: str = "escpos_tcp"

    def __post_init__(self) -> None:
        if not self.host.strip():
            raise ValueError("ESC/POS TCP adapter requires a printer host.")
        if self.port <= 0 or self.port > 65535:
            raise ValueError("ESC/POS TCP adapter port must be between 1 and 65535.")
        if self.timeout_seconds <= 0:
            raise ValueError("ESC/POS TCP adapter timeout must be positive.")
        if self.feed_lines < 0:
            raise ValueError("ESC/POS TCP adapter feed_lines must be non-negative.")
        self.encoding = _normalize_escpos_tcp_encoding(self.encoding)

    def deliver(self, receipt: RenderedReceipt) -> None:
        payload = self._build_payload(receipt.text)
        with socket.create_connection(
            (self.host, self.port),
            timeout=self.timeout_seconds,
        ) as printer_socket:
            printer_socket.sendall(payload)

    def _build_payload(self, text: str) -> bytes:
        normalized_text = text.replace("\r\n", "\n").replace("\r", "\n")
        if not normalized_text.endswith("\n"):
            normalized_text += "\n"

        text_bytes = normalized_text.encode(self.encoding, errors="replace")
        feed_bytes = b"\n" * self.feed_lines
        cut_bytes = GS_PARTIAL_CUT if self.cut else b""

        return ESC_INIT + FS_SELECT_CHINESE_MODE + text_bytes + feed_bytes + cut_bytes


def _normalize_escpos_tcp_encoding(value: str) -> str:
    normalized = value.strip().lower()
    if normalized not in _SUPPORTED_ENCODINGS:
        raise ValueError(
            "EscposTcpPrinterAdapter only supports gb18030 because it uses the "
            "Chinese/Kanji mode ESC/POS path."
        )
    return "gb18030"
