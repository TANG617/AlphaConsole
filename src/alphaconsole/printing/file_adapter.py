from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .adapter import PrinterAdapter
from .artifact import RenderedReceipt
from .diagnostics import build_delivery_diagnostics


@dataclass(slots=True)
class FilePrinterAdapter(PrinterAdapter):
    output_dir: Path
    target_id: str | None = None
    printer_profile_name: str | None = None
    render_profile_name: str | None = None
    name: str = "file"
    transport: str = "file"

    def deliver(self, receipt: RenderedReceipt):
        self.output_dir.mkdir(parents=True, exist_ok=True)
        output_path = self.output_dir / f"{receipt.issue_id}__{receipt.profile_name}.txt"
        output_path.write_text(receipt.text, encoding="utf-8")
        return build_delivery_diagnostics(
            adapter_name=self.name,
            target_id=self.target_id,
            printer_profile_name=self.printer_profile_name,
            render_profile_name=self.render_profile_name or receipt.profile_name,
            transport=self.transport,
            bytes_length=None,
            duration_ms=None,
            succeeded=True,
            error_text=None,
        )
