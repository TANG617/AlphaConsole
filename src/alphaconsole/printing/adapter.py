from __future__ import annotations

from abc import ABC, abstractmethod

from .artifact import RenderedReceipt
from .diagnostics import DeliveryDiagnostics


class PrinterAdapter(ABC):
    name: str

    @abstractmethod
    def deliver(self, receipt: RenderedReceipt) -> DeliveryDiagnostics:
        raise NotImplementedError
