from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Iterable

from .models import ChecklistItem, EntryKind, EntryRecord, EntryStatus

_SCHEMA = """
CREATE TABLE IF NOT EXISTS entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kind TEXT NOT NULL,
    title TEXT NOT NULL,
    notes TEXT NOT NULL DEFAULT '',
    due_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    printed_at TEXT,
    printer_host TEXT NOT NULL,
    preview_path TEXT,
    error_message TEXT
);

CREATE TABLE IF NOT EXISTS checklist_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_id INTEGER NOT NULL,
    item_order INTEGER NOT NULL,
    label TEXT NOT NULL,
    is_required INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (entry_id) REFERENCES entries(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS print_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_id INTEGER NOT NULL,
    requested_at TEXT NOT NULL,
    completed_at TEXT,
    status TEXT NOT NULL,
    preview_path TEXT,
    error_message TEXT,
    FOREIGN KEY (entry_id) REFERENCES entries(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_entries_due_pending
ON entries(status, due_at);

CREATE INDEX IF NOT EXISTS idx_checklist_items_entry_id
ON checklist_items(entry_id, item_order);
"""


class Repository:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")

    def initialize(self) -> None:
        self.conn.executescript(_SCHEMA)
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    def create_event(
        self,
        title: str,
        due_at: datetime,
        notes: str,
        printer_host: str,
    ) -> EntryRecord:
        return self._create_entry(
            kind=EntryKind.EVENT,
            title=title,
            due_at=due_at,
            notes=notes,
            items=[],
            printer_host=printer_host,
        )

    def create_checklist(
        self,
        title: str,
        due_at: datetime,
        notes: str,
        items: Iterable[str],
        printer_host: str,
    ) -> EntryRecord:
        normalized = [item.strip() for item in items if item.strip()]
        if not normalized:
            raise ValueError("Checklist requires at least one item.")
        return self._create_entry(
            kind=EntryKind.CHECKLIST,
            title=title,
            due_at=due_at,
            notes=notes,
            items=normalized,
            printer_host=printer_host,
        )

    def _create_entry(
        self,
        kind: EntryKind,
        title: str,
        due_at: datetime,
        notes: str,
        items: list[str],
        printer_host: str,
    ) -> EntryRecord:
        timestamp = datetime.now(tz=due_at.tzinfo).isoformat()
        with self.conn:
            cursor = self.conn.execute(
                """
                INSERT INTO entries (
                    kind, title, notes, due_at, status, created_at, updated_at, printer_host
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    kind.value,
                    title.strip(),
                    notes.strip(),
                    due_at.isoformat(),
                    EntryStatus.PENDING.value,
                    timestamp,
                    timestamp,
                    printer_host,
                ),
            )
            entry_id = int(cursor.lastrowid)
            for index, label in enumerate(items, start=1):
                self.conn.execute(
                    """
                    INSERT INTO checklist_items (entry_id, item_order, label, is_required)
                    VALUES (?, ?, ?, 1)
                    """,
                    (entry_id, index, label),
                )
        return self.get_entry(entry_id)

    def list_entries(self, limit: int = 100) -> list[EntryRecord]:
        rows = self.conn.execute(
            """
            SELECT * FROM entries
            ORDER BY due_at ASC, id ASC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [self._hydrate_entry(row) for row in rows]

    def get_entry(self, entry_id: int) -> EntryRecord:
        row = self.conn.execute(
            "SELECT * FROM entries WHERE id = ?",
            (entry_id,),
        ).fetchone()
        if row is None:
            raise KeyError(f"Entry {entry_id} not found.")
        return self._hydrate_entry(row)

    def claim_due_entries(
        self,
        due_before: datetime,
        limit: int = 20,
    ) -> list[EntryRecord]:
        rows = self.conn.execute(
            """
            SELECT id FROM entries
            WHERE status = ? AND due_at <= ?
            ORDER BY due_at ASC, id ASC
            LIMIT ?
            """,
            (EntryStatus.PENDING.value, due_before.isoformat(), limit),
        ).fetchall()
        if not rows:
            return []
        ids = [int(row["id"]) for row in rows]
        updated_at = due_before.isoformat()
        with self.conn:
            self.conn.executemany(
                "UPDATE entries SET status = ?, updated_at = ? WHERE id = ?",
                [
                    (EntryStatus.PROCESSING.value, updated_at, entry_id)
                    for entry_id in ids
                ],
            )
        return [self.get_entry(entry_id) for entry_id in ids]

    def mark_done(self, entry_id: int, preview_path: str) -> None:
        timestamp = datetime.now().astimezone().isoformat()
        with self.conn:
            self.conn.execute(
                """
                UPDATE entries
                SET status = ?, updated_at = ?, printed_at = ?, preview_path = ?, error_message = NULL
                WHERE id = ?
                """,
                (
                    EntryStatus.DONE.value,
                    timestamp,
                    timestamp,
                    preview_path,
                    entry_id,
                ),
            )
            self.conn.execute(
                """
                INSERT INTO print_jobs (entry_id, requested_at, completed_at, status, preview_path, error_message)
                VALUES (?, ?, ?, ?, ?, NULL)
                """,
                (
                    entry_id,
                    timestamp,
                    timestamp,
                    EntryStatus.DONE.value,
                    preview_path,
                ),
            )

    def mark_failed(
        self,
        entry_id: int,
        error_message: str,
        preview_path: str | None,
    ) -> None:
        timestamp = datetime.now().astimezone().isoformat()
        with self.conn:
            self.conn.execute(
                """
                UPDATE entries
                SET status = ?, updated_at = ?, preview_path = ?, error_message = ?
                WHERE id = ?
                """,
                (
                    EntryStatus.FAILED.value,
                    timestamp,
                    preview_path,
                    error_message,
                    entry_id,
                ),
            )
            self.conn.execute(
                """
                INSERT INTO print_jobs (entry_id, requested_at, completed_at, status, preview_path, error_message)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    entry_id,
                    timestamp,
                    timestamp,
                    EntryStatus.FAILED.value,
                    preview_path,
                    error_message,
                ),
            )

    def record_reprint(self, entry_id: int, preview_path: str) -> None:
        timestamp = datetime.now().astimezone().isoformat()
        with self.conn:
            self.conn.execute(
                """
                INSERT INTO print_jobs (entry_id, requested_at, completed_at, status, preview_path, error_message)
                VALUES (?, ?, ?, ?, ?, NULL)
                """,
                (
                    entry_id,
                    timestamp,
                    timestamp,
                    EntryStatus.DONE.value,
                    preview_path,
                ),
            )

    def _hydrate_entry(self, row: sqlite3.Row) -> EntryRecord:
        items = self.conn.execute(
            """
            SELECT label, is_required
            FROM checklist_items
            WHERE entry_id = ?
            ORDER BY item_order ASC
            """,
            (int(row["id"]),),
        ).fetchall()
        return EntryRecord(
            id=int(row["id"]),
            kind=EntryKind(row["kind"]),
            title=str(row["title"]),
            notes=str(row["notes"]),
            due_at=datetime.fromisoformat(str(row["due_at"])),
            status=EntryStatus(row["status"]),
            created_at=datetime.fromisoformat(str(row["created_at"])),
            updated_at=datetime.fromisoformat(str(row["updated_at"])),
            printed_at=(
                datetime.fromisoformat(str(row["printed_at"]))
                if row["printed_at"]
                else None
            ),
            printer_host=str(row["printer_host"]),
            preview_path=str(row["preview_path"]) if row["preview_path"] else None,
            error_message=str(row["error_message"]) if row["error_message"] else None,
            items=[
                ChecklistItem(
                    label=str(item["label"]),
                    is_required=bool(item["is_required"]),
                )
                for item in items
            ],
        )
