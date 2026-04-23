from __future__ import annotations

from dataclasses import dataclass, field
import socket
import time

from .adapter import PrinterAdapter
from .artifact import RenderedReceipt
from .diagnostics import TargetHealthResult, build_delivery_diagnostics
from .escpos import build_escpos_payload
from .profiles import PrinterProfile
from .raster import rasterize_receipt
from .targets import HardwarePrintOptions


@dataclass(slots=True)
class EscPosSocketPrinterAdapter(PrinterAdapter):
    target_id: str
    host: str
    port: int
    printer_profile: PrinterProfile
    printer_profile_name: str
    render_profile_name: str
    timeout_seconds: float = 5.0
    hardware_options: HardwarePrintOptions = field(default_factory=HardwarePrintOptions)
    name: str = field(init=False, default="escpos_socket")
    transport: str = field(init=False, default="tcp_socket")

    def __post_init__(self) -> None:
        self.name = "escpos_socket"

    def deliver(self, receipt: RenderedReceipt):
        started_at = time.perf_counter()
        rasterized = rasterize_receipt(
            receipt,
            printer_profile=self.printer_profile,
            font_path=self.hardware_options.font_path,
            font_size=self.hardware_options.font_size,
            line_spacing=self.hardware_options.line_spacing,
        )
        payload = build_escpos_payload(
            rasterized,
            cut=self.hardware_options.cut,
            feed_lines=self.hardware_options.feed_lines,
        )
        with socket.create_connection(
            (self.host, self.port),
            timeout=self.timeout_seconds,
        ) as connection:
            connection.sendall(payload.data)
        duration_ms = int((time.perf_counter() - started_at) * 1000)
        return build_delivery_diagnostics(
            adapter_name=self.name,
            target_id=self.target_id,
            printer_profile_name=self.printer_profile_name,
            render_profile_name=receipt.profile_name,
            transport=self.transport,
            bytes_length=len(payload.data),
            duration_ms=duration_ms,
            succeeded=True,
            error_text=None,
        )

    def ping(self) -> TargetHealthResult:
        started_at = time.perf_counter()
        try:
            with socket.create_connection(
                (self.host, self.port),
                timeout=self.timeout_seconds,
            ):
                latency_ms = int((time.perf_counter() - started_at) * 1000)
                return TargetHealthResult(
                    target_id=self.target_id,
                    ok=True,
                    latency_ms=latency_ms,
                    error_text=None,
                )
        except OSError as exc:
            latency_ms = int((time.perf_counter() - started_at) * 1000)
            return TargetHealthResult(
                target_id=self.target_id,
                ok=False,
                latency_ms=latency_ms,
                error_text=str(exc),
            )
