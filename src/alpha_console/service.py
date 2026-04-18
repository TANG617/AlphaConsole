from __future__ import annotations

from dataclasses import dataclass

from .config import Settings
from .db import Repository
from .layout import ReceiptScene
from .models import EntryRecord
from .printer import PrinterService
from .timeutil import now_local


@dataclass(slots=True)
class ProcessedEntry:
    entry_id: int
    title: str
    status: str
    detail: str


@dataclass(slots=True)
class PreviewArtifact:
    scene: ReceiptScene
    ascii_preview: str
    preview_path: str


class ConsoleService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.settings.ensure_dirs()
        self.repo = Repository(settings.db_path)
        self.repo.initialize()
        self.printer = PrinterService(settings)

    def close(self) -> None:
        self.repo.close()

    def create_event(self, title: str, due_at, notes: str = "") -> EntryRecord:
        return self.repo.create_event(
            title=title,
            due_at=due_at,
            notes=notes,
            printer_host=self.settings.printer_host,
        )

    def create_checklist(
        self,
        title: str,
        due_at,
        items: list[str],
        notes: str = "",
    ) -> EntryRecord:
        return self.repo.create_checklist(
            title=title,
            due_at=due_at,
            notes=notes,
            items=items,
            printer_host=self.settings.printer_host,
        )

    def list_entries(self, limit: int = 100) -> list[EntryRecord]:
        return self.repo.list_entries(limit=limit)

    def get_entry(self, entry_id: int) -> EntryRecord:
        return self.repo.get_entry(entry_id)

    def preview_entry(self, entry_id: int) -> PreviewArtifact:
        entry = self.get_entry(entry_id)
        preview = self.printer.build_preview(entry)
        return PreviewArtifact(
            scene=preview.scene,
            ascii_preview=preview.ascii_preview,
            preview_path=str(preview.preview_path),
        )

    def print_entry_now(self, entry_id: int, dry_run: bool = False) -> str:
        entry = self.get_entry(entry_id)
        preview_path = self.printer.print_entry(entry, dry_run=dry_run)
        self.repo.record_reprint(entry_id, str(preview_path))
        return str(preview_path)

    def process_due_entries(self, dry_run: bool = False) -> list[ProcessedEntry]:
        claimed = self.repo.claim_due_entries(now_local())
        processed: list[ProcessedEntry] = []
        for entry in claimed:
            preview_path = None
            try:
                preview_path = self.printer.print_entry(entry, dry_run=dry_run)
                self.repo.mark_done(entry.id, str(preview_path))
                processed.append(
                    ProcessedEntry(
                        entry_id=entry.id,
                        title=entry.title,
                        status="done",
                        detail=str(preview_path),
                    )
                )
            except Exception as exc:
                self.repo.mark_failed(
                    entry.id,
                    str(exc),
                    str(preview_path) if preview_path else None,
                )
                processed.append(
                    ProcessedEntry(
                        entry_id=entry.id,
                        title=entry.title,
                        status="failed",
                        detail=str(exc),
                    )
                )
        return processed
