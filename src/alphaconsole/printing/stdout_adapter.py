from __future__ import annotations

import sys

from .adapter import PrinterAdapter
from .artifact import RenderedReceipt


class StdoutPrinterAdapter(PrinterAdapter):
    name = "stdout"

    def deliver(self, receipt: RenderedReceipt) -> None:
        sys.stdout.write(receipt.text)
        if not receipt.text.endswith("\n"):
            sys.stdout.write("\n")
