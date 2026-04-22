from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from alphaconsole.scheduler import ScheduledOccurrence


@dataclass(slots=True)
class RuntimeTickResult:
    ticked_at: datetime
    window_start: datetime
    window_end: datetime
    due_occurrences: tuple[ScheduledOccurrence, ...]
    published_issue_ids: tuple[str, ...]
    skipped_existing_occurrences: tuple[ScheduledOccurrence, ...]
