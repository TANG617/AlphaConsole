from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from .enums import TriggerMode


@dataclass(slots=True)
class IssueHeader:
    issue_date: date
    printed_at: datetime
    sequence_of_day: int
    trigger_mode: TriggerMode
