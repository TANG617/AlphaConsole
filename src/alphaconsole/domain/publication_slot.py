from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time


@dataclass(slots=True)
class PublicationSlot:
    slot_id: str
    name: str
    description: str | None
    publish_time: time
    recurrence_rule: str | None
    is_enabled: bool
    created_at: datetime
    updated_at: datetime
