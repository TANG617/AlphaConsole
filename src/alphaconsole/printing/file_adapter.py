from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .adapter import PrinterAdapter
from .artifact import RenderedReceipt


@dataclass(slots=True)
class FilePrinterAdapter(PrinterAdapter):
    output_dir: Path
    name: str = "file"

    def deliver(self, receipt: RenderedReceipt) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        output_path = self.output_dir / f"{receipt.issue_id}__{receipt.profile_name}.txt"
        output_path.write_text(receipt.text, encoding="utf-8")
