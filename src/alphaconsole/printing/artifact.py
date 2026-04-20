from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from alphaconsole.domain import TriggerMode


@dataclass(slots=True, frozen=True)
class RenderedReceipt:
    issue_id: str
    publication_slot_id: str | None
    trigger_mode: TriggerMode
    profile_name: str
    text: str
    rendered_at: datetime
