from __future__ import annotations

from datetime import datetime, time
from pathlib import Path
import sqlite3

import pytest

from alphaconsole.application import AutomationRuntimeService
from alphaconsole.domain import MergePolicy, PublicationSlot, SceneApp, TriggerMode
from alphaconsole.printing import MemoryPrinterAdapter, PrinterAdapter
from alphaconsole.rendering import RECEIPT_42
from alphaconsole.services import IssueAssembler
from alphaconsole.state import SQLiteStateStore


def make_slot(
    *,
    slot_id: str = "noon",
    publish_time: time = time(12, 0),
    is_enabled: bool = True,
) -> PublicationSlot:
    created_at = datetime(2026, 4, 22, 8, 0, 0)
    return PublicationSlot(
        slot_id=slot_id,
        name=slot_id.title(),
        description=None,
        publish_time=publish_time,
        recurrence_rule="daily",
        is_enabled=is_enabled,
        created_at=created_at,
        updated_at=created_at,
    )


def make_scene_app(
    *,
    app_id: str = "lunch",
    slot_id: str = "noon",
    scene_note: str | None = "Eat vegetables",
) -> SceneApp:
    created_at = datetime(2026, 4, 22, 8, 0, 0)
    return SceneApp(
        app_id=app_id,
        app_type="scene",
        name=app_id.title(),
        description=None,
        target_publication_slot_id=slot_id,
        prepare_at=None,
        default_trigger_mode=TriggerMode.SCHEDULED,
        default_merge_policy=MergePolicy.MERGEABLE,
        default_template_type="scene.default",
        expiration_policy=None,
        is_enabled=True,
        created_at=created_at,
        updated_at=created_at,
        scene_note=scene_note,
        checklist_items=(),
        scene_description=None,
        recurrence_rule=None,
    )


class RaisingPrinterAdapter(PrinterAdapter):
    name = "raising"

    def deliver(self, receipt) -> None:
        raise RuntimeError("delivery failed")


class CapturingIssueAssembler(IssueAssembler):
    def __init__(self) -> None:
        super().__init__()
        self.last_issue = None

    def assemble_scheduled_issue(self, *args, **kwargs):
        issue = super().assemble_scheduled_issue(*args, **kwargs)
        self.last_issue = issue
        return issue


def _fetch_attempt_count(db_path: Path) -> int:
    with sqlite3.connect(db_path) as conn:
        row = conn.execute("SELECT COUNT(*) FROM delivery_attempts").fetchone()
    return int(row[0])


def test_run_once_happy_path_writes_ledger_and_updates_checkpoint(
    tmp_path: Path,
) -> None:
    service = AutomationRuntimeService()
    store = SQLiteStateStore(tmp_path / "state.db")
    adapter = MemoryPrinterAdapter()
    slot = make_slot()
    app = make_scene_app()

    result = service.run_once(
        slots=[slot],
        apps=[app],
        adapter=adapter,
        store=store,
        now=datetime(2026, 4, 22, 12, 0, 0),
        profile=RECEIPT_42,
        catchup_seconds=60,
    )

    runs = store.list_publication_runs(limit=10)

    assert len(result.due_occurrences) == 1
    assert len(result.published_issue_ids) == 1
    assert len(adapter.receipts) == 1
    assert len(runs) == 1
    assert runs[0].status == "delivered"
    assert store.get_last_tick_at() == datetime(2026, 4, 22, 12, 0, 0)
    assert _fetch_attempt_count(tmp_path / "state.db") == 1


def test_run_once_skips_existing_scheduled_occurrence(tmp_path: Path) -> None:
    service = AutomationRuntimeService()
    store = SQLiteStateStore(tmp_path / "state.db")
    adapter = MemoryPrinterAdapter()
    slot = make_slot()
    app = make_scene_app()

    service.run_once(
        slots=[slot],
        apps=[app],
        adapter=adapter,
        store=store,
        now=datetime(2026, 4, 22, 12, 0, 0),
        profile=RECEIPT_42,
        catchup_seconds=60,
    )
    store.set_last_tick_at(datetime(2026, 4, 22, 11, 59, 0))

    result = service.run_once(
        slots=[slot],
        apps=[app],
        adapter=adapter,
        store=store,
        now=datetime(2026, 4, 22, 12, 0, 30),
        profile=RECEIPT_42,
        catchup_seconds=60,
    )

    assert result.published_issue_ids == ()
    assert len(result.skipped_existing_occurrences) == 1
    assert len(store.list_publication_runs(limit=10)) == 1


def test_run_once_first_tick_uses_conservative_catchup(tmp_path: Path) -> None:
    service = AutomationRuntimeService()
    store = SQLiteStateStore(tmp_path / "state.db")
    adapter = MemoryPrinterAdapter()
    due_slot = make_slot(slot_id="recent", publish_time=time(12, 0))
    old_slot = make_slot(slot_id="old", publish_time=time(11, 58))
    apps = [
        make_scene_app(app_id="recent-app", slot_id="recent"),
        make_scene_app(app_id="old-app", slot_id="old"),
    ]

    result = service.run_once(
        slots=[old_slot, due_slot],
        apps=apps,
        adapter=adapter,
        store=store,
        now=datetime(2026, 4, 22, 12, 0, 0),
        profile=RECEIPT_42,
        catchup_seconds=60,
    )

    assert [occ.slot_id for occ in result.due_occurrences] == ["recent"]
    assert len(result.published_issue_ids) == 1


def test_run_once_failure_marks_run_failed_records_attempt_and_keeps_checkpoint(
    tmp_path: Path,
) -> None:
    service = AutomationRuntimeService()
    store = SQLiteStateStore(tmp_path / "state.db")
    slot = make_slot()
    app = make_scene_app()

    with pytest.raises(RuntimeError, match="delivery failed"):
        service.run_once(
            slots=[slot],
            apps=[app],
            adapter=RaisingPrinterAdapter(),
            store=store,
            now=datetime(2026, 4, 22, 12, 0, 0),
            profile=RECEIPT_42,
            catchup_seconds=60,
        )

    runs = store.list_publication_runs(limit=10)

    assert len(runs) == 1
    assert runs[0].status == "delivery_failed"
    assert _fetch_attempt_count(tmp_path / "state.db") == 1
    assert store.get_last_tick_at() is None


def test_run_once_does_not_mutate_issue_printed_at(tmp_path: Path) -> None:
    assembler = CapturingIssueAssembler()
    service = AutomationRuntimeService(assembler=assembler)
    store = SQLiteStateStore(tmp_path / "state.db")
    adapter = MemoryPrinterAdapter()
    slot = make_slot()
    app = make_scene_app()

    service.run_once(
        slots=[slot],
        apps=[app],
        adapter=adapter,
        store=store,
        now=datetime(2026, 4, 22, 12, 0, 0),
        profile=RECEIPT_42,
        catchup_seconds=60,
    )

    assert assembler.last_issue is not None
    assert assembler.last_issue.printed_at is None


def test_run_once_first_tick_catches_cross_midnight_occurrence(tmp_path: Path) -> None:
    service = AutomationRuntimeService()
    store = SQLiteStateStore(tmp_path / "state.db")
    adapter = MemoryPrinterAdapter()
    slot = make_slot(slot_id="late-night", publish_time=time(23, 59, 45))
    app = make_scene_app(app_id="late-night-app", slot_id="late-night")

    result = service.run_once(
        slots=[slot],
        apps=[app],
        adapter=adapter,
        store=store,
        now=datetime(2026, 4, 23, 0, 0, 30),
        profile=RECEIPT_42,
        catchup_seconds=60,
    )

    runs = store.list_publication_runs(limit=10)

    assert len(result.due_occurrences) == 1
    assert result.due_occurrences[0].occurrence_at == datetime(2026, 4, 22, 23, 59, 45)
    assert len(result.published_issue_ids) == 1
    assert len(adapter.receipts) == 1
    assert len(runs) == 1
    assert runs[0].occurrence_at == datetime(2026, 4, 22, 23, 59, 45)
