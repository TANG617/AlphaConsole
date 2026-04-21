from __future__ import annotations

from dataclasses import dataclass

from alphaconsole.domain import Issue
from alphaconsole.printing import RenderedReceipt


@dataclass(slots=True)
class PublicationResult:
    issue: Issue
    receipt: RenderedReceipt
    adapter_name: str
