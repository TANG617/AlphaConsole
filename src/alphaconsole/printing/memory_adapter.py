from __future__ import annotations

from dataclasses import dataclass, field

from .adapter import PrinterAdapter
from .artifact import RenderedReceipt
from .diagnostics import build_delivery_diagnostics


@dataclass(slots=True)
class MemoryPrinterAdapter(PrinterAdapter):
    receipts: list[RenderedReceipt] = field(default_factory=list)
    target_id: str | None = None
    printer_profile_name: str | None = None
    render_profile_name: str | None = None
    name: str = "memory"
    transport: str = "memory"

    def deliver(self, receipt: RenderedReceipt):
        self.receipts.append(receipt)
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
