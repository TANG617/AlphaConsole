from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import time

from .adapter import PrinterAdapter
from .artifact import RenderedReceipt
from .diagnostics import build_delivery_diagnostics
from .escpos import build_escpos_payload
from .profiles import PrinterProfile
from .raster import rasterize_receipt
from .targets import HardwarePrintOptions


@dataclass(slots=True)
class EscPosBytesFileAdapter(PrinterAdapter):
    target_id: str
    output_dir: Path
    printer_profile: PrinterProfile
    printer_profile_name: str
    render_profile_name: str
    hardware_options: HardwarePrintOptions = field(default_factory=HardwarePrintOptions)
    name: str = field(init=False, default="escpos_bytes_file")
    transport: str = field(init=False, default="bytes_file")

    def __post_init__(self) -> None:
        self.name = "escpos_bytes_file"

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
        self.output_dir.mkdir(parents=True, exist_ok=True)
        output_path = self.output_dir / f"{receipt.issue_id}__{self.target_id}.bin"
        output_path.write_bytes(payload.data)
        duration_ms = int((time.perf_counter() - started_at) * 1000)
        return build_delivery_diagnostics(
            adapter_name=self.name,
            target_id=self.target_id,
            printer_profile_name=self.printer_profile_name,
            render_profile_name=self.render_profile_name or receipt.profile_name,
            transport=self.transport,
            bytes_length=len(payload.data),
            duration_ms=duration_ms,
            succeeded=True,
            error_text=None,
        )
