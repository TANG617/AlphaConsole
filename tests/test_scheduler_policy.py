from __future__ import annotations

from datetime import datetime, time

from alphaconsole.domain import PublicationSlot
from alphaconsole.scheduler import compute_due_occurrences


def make_slot(
    *,
    slot_id: str,
    publish_time: time,
    is_enabled: bool = True,
) -> PublicationSlot:
    now = datetime(2026, 4, 22, 8, 0, 0)
    return PublicationSlot(
        slot_id=slot_id,
        name=slot_id.title(),
        description=None,
        publish_time=publish_time,
        recurrence_rule="daily",
        is_enabled=is_enabled,
        created_at=now,
        updated_at=now,
    )


def test_compute_due_occurrences_includes_enabled_slot_inside_window() -> None:
    due = compute_due_occurrences(
        slots=[make_slot(slot_id="noon", publish_time=time(12, 0))],
        window_start=datetime(2026, 4, 22, 11, 59, 30),
        window_end=datetime(2026, 4, 22, 12, 0, 0),
    )

    assert [(occ.slot_id, occ.occurrence_at.isoformat()) for occ in due] == [
        ("noon", "2026-04-22T12:00:00")
    ]


def test_compute_due_occurrences_excludes_disabled_slot() -> None:
    due = compute_due_occurrences(
        slots=[make_slot(slot_id="noon", publish_time=time(12, 0), is_enabled=False)],
        window_start=datetime(2026, 4, 22, 11, 59, 30),
        window_end=datetime(2026, 4, 22, 12, 0, 0),
    )

    assert due == []


def test_compute_due_occurrences_uses_open_closed_window() -> None:
    due = compute_due_occurrences(
        slots=[
            make_slot(slot_id="start", publish_time=time(11, 59, 30)),
            make_slot(slot_id="end", publish_time=time(12, 0, 0)),
        ],
        window_start=datetime(2026, 4, 22, 11, 59, 30),
        window_end=datetime(2026, 4, 22, 12, 0, 0),
    )

    assert [occ.slot_id for occ in due] == ["end"]


def test_compute_due_occurrences_sorts_by_occurrence_at_then_slot_id() -> None:
    due = compute_due_occurrences(
        slots=[
            make_slot(slot_id="b-slot", publish_time=time(12, 0)),
            make_slot(slot_id="a-slot", publish_time=time(12, 0)),
            make_slot(slot_id="earlier", publish_time=time(11, 59, 45)),
        ],
        window_start=datetime(2026, 4, 22, 11, 59, 0),
        window_end=datetime(2026, 4, 22, 12, 0, 0),
    )

    assert [occ.slot_id for occ in due] == ["earlier", "a-slot", "b-slot"]


def test_compute_due_occurrences_includes_cross_midnight_previous_day_occurrence() -> None:
    due = compute_due_occurrences(
        slots=[make_slot(slot_id="late-night", publish_time=time(23, 59, 45))],
        window_start=datetime(2026, 4, 22, 23, 59, 30),
        window_end=datetime(2026, 4, 23, 0, 0, 30),
    )

    assert [(occ.slot_id, occ.occurrence_at.isoformat()) for occ in due] == [
        ("late-night", "2026-04-22T23:59:45")
    ]


def test_compute_due_occurrences_does_not_create_cross_midnight_false_positive() -> None:
    due = compute_due_occurrences(
        slots=[make_slot(slot_id="after-midnight", publish_time=time(0, 1, 0))],
        window_start=datetime(2026, 4, 22, 23, 59, 30),
        window_end=datetime(2026, 4, 23, 0, 0, 30),
    )

    assert due == []
