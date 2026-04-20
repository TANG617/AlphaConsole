from __future__ import annotations

from abc import ABC, abstractmethod

from .artifact import RenderedReceipt


class PrinterAdapter(ABC):
    name: str

    @abstractmethod
    def deliver(self, receipt: RenderedReceipt) -> None:
        raise NotImplementedError
