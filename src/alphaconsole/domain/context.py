from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from .enums import TriggerMode


@dataclass(slots=True)
class IssueBuildContext:
    issue_id: str
    issue_date: date
    issued_at: datetime
    publication_slot_id: str | None
    trigger_mode: TriggerMode
    sequence_of_day: int
