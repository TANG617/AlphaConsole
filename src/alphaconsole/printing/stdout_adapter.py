from __future__ import annotations

import sys

from .adapter import PrinterAdapter
from .artifact import RenderedReceipt
from .diagnostics import build_delivery_diagnostics


class StdoutPrinterAdapter(PrinterAdapter):
    transport = "stdout"

    def __init__(
        self,
        *,
        target_id: str | None = None,
        printer_profile_name: str | None = None,
        render_profile_name: str | None = None,
        name: str = "stdout",
    ) -> None:
        self.name = name
        self.target_id = target_id
        self.printer_profile_name = printer_profile_name
        self.render_profile_name = render_profile_name

    def deliver(self, receipt: RenderedReceipt):
        sys.stdout.write(receipt.text)
        if not receipt.text.endswith("\n"):
            sys.stdout.write("\n")
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
