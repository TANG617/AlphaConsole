from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

from alphaconsole.domain import PublicationSlot

from .models import ScheduledOccurrence


def compute_due_occurrences(
    slots: Sequence[PublicationSlot],
    window_start: datetime,
    window_end: datetime,
) -> list[ScheduledOccurrence]:
    due_occurrences: list[ScheduledOccurrence] = []

    for slot in slots:
        if not slot.is_enabled:
            continue

        occurrence_at = datetime.combine(window_end.date(), slot.publish_time)
        if window_start < occurrence_at <= window_end:
            due_occurrences.append(
                ScheduledOccurrence(
                    slot_id=slot.slot_id,
                    occurrence_at=occurrence_at,
                )
            )

    due_occurrences.sort(key=lambda item: (item.occurrence_at, item.slot_id))
    return due_occurrences
