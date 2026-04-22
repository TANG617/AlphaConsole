from __future__ import annotations

from dataclasses import dataclass, field
import socket

from .adapter import PrinterAdapter
from .artifact import RenderedReceipt
from .escpos import build_escpos_payload
from .raster import rasterize_receipt
from .targets import HardwarePrintOptions


@dataclass(slots=True)
class EscPosSocketPrinterAdapter(PrinterAdapter):
    target_id: str
    host: str
    port: int
    timeout_seconds: float = 5.0
    hardware_options: HardwarePrintOptions = field(default_factory=HardwarePrintOptions)
    name: str = field(init=False)

    def __post_init__(self) -> None:
        self.name = self.target_id

    def deliver(self, receipt: RenderedReceipt) -> None:
        rasterized = rasterize_receipt(
            receipt,
            font_path=self.hardware_options.font_path,
            font_size=self.hardware_options.font_size,
            line_spacing=self.hardware_options.line_spacing,
        )
        payload = build_escpos_payload(
            rasterized,
            cut=self.hardware_options.cut,
        )
        with socket.create_connection(
            (self.host, self.port),
            timeout=self.timeout_seconds,
        ) as connection:
            connection.sendall(payload.data)
