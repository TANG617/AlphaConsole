from __future__ import annotations

from dataclasses import dataclass, field

from .adapter import PrinterAdapter
from .artifact import RenderedReceipt


@dataclass(slots=True)
class MemoryPrinterAdapter(PrinterAdapter):
    receipts: list[RenderedReceipt] = field(default_factory=list)
    name: str = "memory"

    def deliver(self, receipt: RenderedReceipt) -> None:
        self.receipts.append(receipt)
