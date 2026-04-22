from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timedelta

from alphaconsole.domain import PublicationSlot

from .models import ScheduledOccurrence


def compute_due_occurrences(
    slots: Sequence[PublicationSlot],
    window_start: datetime,
    window_end: datetime,
) -> list[ScheduledOccurrence]:
    due_occurrences: list[ScheduledOccurrence] = []
    current_date = window_start.date()
    end_date = window_end.date()

    while current_date <= end_date:
        for slot in slots:
            if not slot.is_enabled:
                continue

            occurrence_at = datetime.combine(current_date, slot.publish_time)
            if window_start < occurrence_at <= window_end:
                due_occurrences.append(
                    ScheduledOccurrence(
                        slot_id=slot.slot_id,
                        occurrence_at=occurrence_at,
                    )
                )
        current_date += timedelta(days=1)

    due_occurrences.sort(key=lambda item: (item.occurrence_at, item.slot_id))
    return due_occurrences
