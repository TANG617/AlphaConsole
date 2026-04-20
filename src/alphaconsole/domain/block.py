from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from datetime import datetime

from .enums import MergePolicy, TriggerMode


@dataclass(slots=True)
class Block(ABC):
    block_id: str
    block_type: str
    title: str
    body: str
    source_app_id: str
    source_app_type: str
    publication_slot_id: str | None
    trigger_mode: TriggerMode
    merge_policy: MergePolicy
    expires_at: datetime | None
    template_type: str
    created_at: datetime

    def is_expired(self, issued_at: datetime) -> bool:
        return self.expires_at is not None and issued_at > self.expires_at
