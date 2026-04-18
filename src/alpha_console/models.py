from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class EntryKind(StrEnum):
    EVENT = "event"
    CHECKLIST = "checklist"


class EntryStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"


@dataclass(slots=True)
class ChecklistItem:
    label: str
    is_required: bool = True


@dataclass(slots=True)
class EntryRecord:
    id: int
    kind: EntryKind
    title: str
    notes: str
    due_at: datetime
    status: EntryStatus
    created_at: datetime
    updated_at: datetime
    printed_at: datetime | None
    printer_host: str
    preview_path: str | None
    error_message: str | None
    items: list[ChecklistItem]


@dataclass(slots=True)
class SlipDocument:
    title: str
    subtitle: str
    emblem: list[str]
    metadata: list[tuple[str, str]]
    section_title: str
    lines: list[str]
    footer: list[str]
