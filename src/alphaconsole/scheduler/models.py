from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True, frozen=True)
class ScheduledOccurrence:
    slot_id: str
    occurrence_at: datetime
