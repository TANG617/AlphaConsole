from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from .block import Block
from .enums import TriggerMode
from .issue_header import IssueHeader


@dataclass(slots=True)
class Issue:
    issue_id: str
    issue_date: date
    publication_slot_id: str | None
    trigger_mode: TriggerMode
    sequence_of_day: int
    header: IssueHeader
    blocks: tuple[Block, ...]
    created_at: datetime
    printed_at: datetime | None = None
