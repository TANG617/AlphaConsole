from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
import sqlite3
from uuid import uuid4

from alphaconsole.printing import DeliveryDiagnostics

from .models import DeliveryAttemptRecord, PublicationRunRecord


class SQLiteStateStore:
    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path

    def init_schema(self) -> None:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS runtime_meta (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS daily_sequence_counters (
                    issue_date TEXT PRIMARY KEY,
                    next_value INTEGER NOT NULL
                );

                CREATE TABLE IF NOT EXISTS publication_runs (
                    issue_id TEXT PRIMARY KEY,
                    slot_id TEXT,
                    occurrence_at TEXT,
                    trigger_mode TEXT NOT NULL,
                    sequence_of_day INTEGER NOT NULL,
                    profile_name TEXT NOT NULL,
                    adapter_name TEXT NOT NULL,
                    target_id TEXT,
                    printer_profile_name TEXT,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    delivered_at TEXT,
                    UNIQUE(slot_id, occurrence_at)
                );

                CREATE TABLE IF NOT EXISTS delivery_attempts (
                    attempt_id TEXT PRIMARY KEY,
                    issue_id TEXT NOT NULL,
                    adapter_name TEXT NOT NULL,
                    attempted_at TEXT NOT NULL,
                    succeeded INTEGER NOT NULL,
                    error_text TEXT,
                    target_id TEXT,
                    printer_profile_name TEXT,
                    render_profile_name TEXT,
                    bytes_length INTEGER,
                    duration_ms INTEGER,
                    FOREIGN KEY(issue_id) REFERENCES publication_runs(issue_id)
                );
                """
            )
            _ensure_column(conn, "publication_runs", "target_id", "TEXT")
            _ensure_column(conn, "publication_runs", "printer_profile_name", "TEXT")
            _ensure_column(conn, "delivery_attempts", "target_id", "TEXT")
            _ensure_column(conn, "delivery_attempts", "printer_profile_name", "TEXT")
            _ensure_column(conn, "delivery_attempts", "render_profile_name", "TEXT")
            _ensure_column(conn, "delivery_attempts", "bytes_length", "INTEGER")
            _ensure_column(conn, "delivery_attempts", "duration_ms", "INTEGER")
            conn.commit()

    def get_last_tick_at(self) -> datetime | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT value FROM runtime_meta WHERE key = 'last_tick_at'"
            ).fetchone()
        if row is None:
            return None
        return _parse_datetime(row["value"])

    def set_last_tick_at(self, dt: datetime) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO runtime_meta(key, value)
                VALUES ('last_tick_at', ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """,
                (_serialize_datetime(dt),),
            )
            conn.commit()

    def allocate_sequence(self, issue_date: date) -> int:
        issue_date_text = issue_date.isoformat()
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT next_value
                FROM daily_sequence_counters
                WHERE issue_date = ?
                """,
                (issue_date_text,),
            ).fetchone()
            if row is None:
                conn.execute(
                    """
                    INSERT INTO daily_sequence_counters(issue_date, next_value)
                    VALUES (?, ?)
                    """,
                    (issue_date_text, 2),
                )
                conn.commit()
                return 1

            current_value = int(row["next_value"])
            conn.execute(
                """
                UPDATE daily_sequence_counters
                SET next_value = ?
                WHERE issue_date = ?
                """,
                (current_value + 1, issue_date_text),
            )
            conn.commit()
            return current_value

    def has_publication_run(self, slot_id: str, occurrence_at: datetime) -> bool:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT 1
                FROM publication_runs
                WHERE slot_id = ? AND occurrence_at = ?
                """,
                (slot_id, _serialize_datetime(occurrence_at)),
            ).fetchone()
        return row is not None

    def create_publication_run(
        self,
        *,
        issue_id: str,
        slot_id: str | None,
        occurrence_at: datetime | None,
        trigger_mode: str,
        sequence_of_day: int,
        profile_name: str,
        adapter_name: str,
        target_id: str | None = None,
        printer_profile_name: str | None = None,
        status: str,
        created_at: datetime,
        delivered_at: datetime | None = None,
    ) -> PublicationRunRecord:
        record = PublicationRunRecord(
            issue_id=issue_id,
            slot_id=slot_id,
            occurrence_at=occurrence_at,
            trigger_mode=trigger_mode,
            sequence_of_day=sequence_of_day,
            profile_name=profile_name,
            adapter_name=adapter_name,
            target_id=target_id,
            printer_profile_name=printer_profile_name,
            status=status,
            created_at=created_at,
            delivered_at=delivered_at,
        )
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO publication_runs(
                    issue_id,
                    slot_id,
                    occurrence_at,
                    trigger_mode,
                    sequence_of_day,
                    profile_name,
                    adapter_name,
                    target_id,
                    printer_profile_name,
                    status,
                    created_at,
                    delivered_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.issue_id,
                    record.slot_id,
                    _serialize_optional_datetime(record.occurrence_at),
                    record.trigger_mode,
                    record.sequence_of_day,
                    record.profile_name,
                    record.adapter_name,
                    record.target_id,
                    record.printer_profile_name,
                    record.status,
                    _serialize_datetime(record.created_at),
                    _serialize_optional_datetime(record.delivered_at),
                ),
            )
            conn.commit()
        return record

    def mark_publication_delivered(self, issue_id: str, delivered_at: datetime) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE publication_runs
                SET status = 'delivered',
                    delivered_at = ?
                WHERE issue_id = ?
                """,
                (_serialize_datetime(delivered_at), issue_id),
            )
            conn.commit()

    def mark_publication_delivery_failed(self, issue_id: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE publication_runs
                SET status = 'delivery_failed'
                WHERE issue_id = ?
                """,
                (issue_id,),
            )
            conn.commit()

    def record_delivery_attempt(
        self,
        *,
        issue_id: str,
        attempted_at: datetime,
        diagnostics: DeliveryDiagnostics,
    ) -> DeliveryAttemptRecord:
        record = DeliveryAttemptRecord(
            attempt_id=uuid4().hex,
            issue_id=issue_id,
            adapter_name=diagnostics.adapter_name,
            attempted_at=attempted_at,
            succeeded=diagnostics.succeeded,
            error_text=diagnostics.error_text,
            target_id=diagnostics.target_id,
            printer_profile_name=diagnostics.printer_profile_name,
            render_profile_name=diagnostics.render_profile_name,
            bytes_length=diagnostics.bytes_length,
            duration_ms=diagnostics.duration_ms,
        )
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO delivery_attempts(
                    attempt_id,
                    issue_id,
                    adapter_name,
                    attempted_at,
                    succeeded,
                    error_text,
                    target_id,
                    printer_profile_name,
                    render_profile_name,
                    bytes_length,
                    duration_ms
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.attempt_id,
                    record.issue_id,
                    record.adapter_name,
                    _serialize_datetime(record.attempted_at),
                    int(record.succeeded),
                    record.error_text,
                    record.target_id,
                    record.printer_profile_name,
                    record.render_profile_name,
                    record.bytes_length,
                    record.duration_ms,
                ),
            )
            conn.commit()
        return record

    def list_delivery_attempts(self, limit: int = 20) -> list[DeliveryAttemptRecord]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT
                    attempt_id,
                    issue_id,
                    adapter_name,
                    attempted_at,
                    succeeded,
                    error_text,
                    target_id,
                    printer_profile_name,
                    render_profile_name,
                    bytes_length,
                    duration_ms
                FROM delivery_attempts
                ORDER BY attempted_at DESC, attempt_id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [_delivery_attempt_record_from_row(row) for row in rows]

    def get_latest_delivery_attempt(self) -> DeliveryAttemptRecord | None:
        attempts = self.list_delivery_attempts(limit=1)
        if not attempts:
            return None
        return attempts[0]

    def list_publication_runs(self, limit: int = 50) -> list[PublicationRunRecord]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT
                    issue_id,
                    slot_id,
                    occurrence_at,
                    trigger_mode,
                    sequence_of_day,
                    profile_name,
                    adapter_name,
                    target_id,
                    printer_profile_name,
                    status,
                    created_at,
                    delivered_at
                FROM publication_runs
                ORDER BY created_at DESC, issue_id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [_publication_run_record_from_row(row) for row in rows]

    def get_latest_publication_run(self) -> PublicationRunRecord | None:
        runs = self.list_publication_runs(limit=1)
        if not runs:
            return None
        return runs[0]

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn


def _publication_run_record_from_row(row: sqlite3.Row) -> PublicationRunRecord:
    return PublicationRunRecord(
        issue_id=row["issue_id"],
        slot_id=row["slot_id"],
        occurrence_at=_parse_optional_datetime(row["occurrence_at"]),
        trigger_mode=row["trigger_mode"],
        sequence_of_day=int(row["sequence_of_day"]),
        profile_name=row["profile_name"],
        adapter_name=row["adapter_name"],
        target_id=row["target_id"],
        printer_profile_name=row["printer_profile_name"],
        status=row["status"],
        created_at=_parse_datetime(row["created_at"]),
        delivered_at=_parse_optional_datetime(row["delivered_at"]),
    )


def _delivery_attempt_record_from_row(row: sqlite3.Row) -> DeliveryAttemptRecord:
    return DeliveryAttemptRecord(
        attempt_id=row["attempt_id"],
        issue_id=row["issue_id"],
        adapter_name=row["adapter_name"],
        attempted_at=_parse_datetime(row["attempted_at"]),
        succeeded=bool(row["succeeded"]),
        error_text=row["error_text"],
        target_id=row["target_id"],
        printer_profile_name=row["printer_profile_name"],
        render_profile_name=row["render_profile_name"],
        bytes_length=row["bytes_length"],
        duration_ms=row["duration_ms"],
    )


def _ensure_column(
    conn: sqlite3.Connection,
    table_name: str,
    column_name: str,
    column_sql: str,
) -> None:
    existing_columns = {
        row["name"]
        for row in conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    }
    if column_name in existing_columns:
        return
    conn.execute(
        f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_sql}"
    )


def _serialize_datetime(value: datetime) -> str:
    return value.isoformat()


def _serialize_optional_datetime(value: datetime | None) -> str | None:
    if value is None:
        return None
    return _serialize_datetime(value)


def _parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _parse_optional_datetime(value: str | None) -> datetime | None:
    if value is None:
        return None
    return _parse_datetime(value)
