from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class PublicationRunRecord:
    issue_id: str
    slot_id: str | None
    occurrence_at: datetime | None
    trigger_mode: str
    sequence_of_day: int
    profile_name: str
    adapter_name: str
    status: str
    created_at: datetime
    delivered_at: datetime | None


@dataclass(slots=True)
class DeliveryAttemptRecord:
    attempt_id: str
    issue_id: str
    adapter_name: str
    attempted_at: datetime
    succeeded: bool
    error_text: str | None


@dataclass(slots=True)
class RuntimeCheckpoint:
    last_tick_at: datetime | None
