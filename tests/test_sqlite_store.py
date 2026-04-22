from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
import sqlite3

import pytest

from alphaconsole.state import SQLiteStateStore


def test_sqlite_store_initializes_schema(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    store = SQLiteStateStore(db_path)

    store.init_schema()

    with sqlite3.connect(db_path) as conn:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }

    assert "runtime_meta" in tables
    assert "daily_sequence_counters" in tables
    assert "publication_runs" in tables
    assert "delivery_attempts" in tables


def test_sqlite_store_reads_and_writes_last_tick_at(tmp_path: Path) -> None:
    store = SQLiteStateStore(tmp_path / "state.db")
    store.init_schema()
    ticked_at = datetime(2026, 4, 22, 12, 0, 0)

    assert store.get_last_tick_at() is None

    store.set_last_tick_at(ticked_at)

    assert store.get_last_tick_at() == ticked_at


def test_sqlite_store_allocates_daily_sequence_per_day(tmp_path: Path) -> None:
    store = SQLiteStateStore(tmp_path / "state.db")
    store.init_schema()

    assert store.allocate_sequence(date(2026, 4, 22)) == 1
    assert store.allocate_sequence(date(2026, 4, 22)) == 2
    assert store.allocate_sequence(date(2026, 4, 23)) == 1


def test_sqlite_store_creates_publication_run_and_enforces_unique_occurrence(
    tmp_path: Path,
) -> None:
    store = SQLiteStateStore(tmp_path / "state.db")
    store.init_schema()
    occurrence_at = datetime(2026, 4, 22, 12, 0, 0)

    record = store.create_publication_run(
        issue_id="issue-1",
        slot_id="noon",
        occurrence_at=occurrence_at,
        trigger_mode="scheduled",
        sequence_of_day=1,
        profile_name="receipt_42",
        adapter_name="stdout",
        status="assembled",
        created_at=occurrence_at,
    )

    assert record.issue_id == "issue-1"
    assert store.has_publication_run("noon", occurrence_at) is True

    with pytest.raises(sqlite3.IntegrityError):
        store.create_publication_run(
            issue_id="issue-2",
            slot_id="noon",
            occurrence_at=occurrence_at,
            trigger_mode="scheduled",
            sequence_of_day=2,
            profile_name="receipt_42",
            adapter_name="stdout",
            status="assembled",
            created_at=occurrence_at,
        )


def test_sqlite_store_records_delivery_attempt(tmp_path: Path) -> None:
    store = SQLiteStateStore(tmp_path / "state.db")
    store.init_schema()
    created_at = datetime(2026, 4, 22, 12, 0, 0)
    store.create_publication_run(
        issue_id="issue-1",
        slot_id="noon",
        occurrence_at=created_at,
        trigger_mode="scheduled",
        sequence_of_day=1,
        profile_name="receipt_42",
        adapter_name="stdout",
        status="assembled",
        created_at=created_at,
    )

    attempt = store.record_delivery_attempt(
        issue_id="issue-1",
        adapter_name="stdout",
        attempted_at=created_at,
        succeeded=True,
        error_text=None,
    )

    with sqlite3.connect(tmp_path / "state.db") as conn:
        row = conn.execute(
            """
            SELECT issue_id, adapter_name, succeeded
            FROM delivery_attempts
            WHERE attempt_id = ?
            """,
            (attempt.attempt_id,),
        ).fetchone()

    assert row == ("issue-1", "stdout", 1)


def test_sqlite_store_lists_runs_and_returns_latest(tmp_path: Path) -> None:
    store = SQLiteStateStore(tmp_path / "state.db")
    store.init_schema()
    first = datetime(2026, 4, 22, 12, 0, 0)
    second = datetime(2026, 4, 22, 12, 5, 0)

    store.create_publication_run(
        issue_id="issue-1",
        slot_id="noon",
        occurrence_at=first,
        trigger_mode="scheduled",
        sequence_of_day=1,
        profile_name="receipt_42",
        adapter_name="stdout",
        status="assembled",
        created_at=first,
    )
    store.create_publication_run(
        issue_id="issue-2",
        slot_id="noon",
        occurrence_at=second,
        trigger_mode="scheduled",
        sequence_of_day=2,
        profile_name="receipt_42",
        adapter_name="stdout",
        status="delivered",
        created_at=second,
        delivered_at=second,
    )

    runs = store.list_publication_runs(limit=10)
    latest = store.get_latest_publication_run()

    assert [run.issue_id for run in runs] == ["issue-2", "issue-1"]
    assert latest is not None
    assert latest.issue_id == "issue-2"
