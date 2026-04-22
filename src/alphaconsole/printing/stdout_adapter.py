from __future__ import annotations

import sys

from .adapter import PrinterAdapter
from .artifact import RenderedReceipt


class StdoutPrinterAdapter(PrinterAdapter):
    def __init__(self, name: str = "stdout") -> None:
        self.name = name

    def deliver(self, receipt: RenderedReceipt) -> None:
        sys.stdout.write(receipt.text)
        if not receipt.text.endswith("\n"):
            sys.stdout.write("\n")
