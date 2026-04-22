from __future__ import annotations

from collections.abc import Callable, Sequence
from datetime import datetime, timedelta
import time as time_module

from alphaconsole.domain import ContentApp, PublicationSlot
from alphaconsole.printing import PrintService, PrinterAdapter
from alphaconsole.rendering import RenderProfile
from alphaconsole.scheduler import ScheduledOccurrence, compute_due_occurrences
from alphaconsole.services import IssueAssembler
from alphaconsole.state import SQLiteStateStore

from .runtime_result import RuntimeTickResult


class AutomationRuntimeService:
    def __init__(
        self,
        assembler: IssueAssembler | None = None,
        print_service: PrintService | None = None,
    ) -> None:
        self._assembler = assembler or IssueAssembler()
        self._print_service = print_service or PrintService()

    def run_once(
        self,
        slots: Sequence[PublicationSlot],
        apps: Sequence[ContentApp],
        adapter: PrinterAdapter,
        store: SQLiteStateStore,
        now: datetime,
        profile: RenderProfile,
        catchup_seconds: int = 60,
    ) -> RuntimeTickResult:
        store.init_schema()

        last_tick_at = store.get_last_tick_at()
        window_start = last_tick_at or (now - timedelta(seconds=catchup_seconds))
        due_occurrences = compute_due_occurrences(
            slots=slots,
            window_start=window_start,
            window_end=now,
        )

        slots_by_id = {slot.slot_id: slot for slot in slots}
        published_issue_ids: list[str] = []
        skipped_existing_occurrences: list[ScheduledOccurrence] = []

        for occurrence in due_occurrences:
            if store.has_publication_run(occurrence.slot_id, occurrence.occurrence_at):
                skipped_existing_occurrences.append(occurrence)
                continue

            slot = slots_by_id[occurrence.slot_id]
            sequence_of_day = store.allocate_sequence(occurrence.occurrence_at.date())
            slot_apps = tuple(
                app
                for app in apps
                if app.is_enabled and app.target_publication_slot_id == slot.slot_id
            )
            issue = self._assembler.assemble_scheduled_issue(
                slot=slot,
                apps=slot_apps,
                now=occurrence.occurrence_at,
                sequence_of_day=sequence_of_day,
            )
            receipt = self._print_service.render_issue_to_receipt(issue, profile)
            store.create_publication_run(
                issue_id=issue.issue_id,
                slot_id=slot.slot_id,
                occurrence_at=occurrence.occurrence_at,
                trigger_mode=issue.trigger_mode.value,
                sequence_of_day=issue.sequence_of_day,
                profile_name=receipt.profile_name,
                adapter_name=adapter.name,
                status="assembled",
                created_at=now,
            )

            try:
                adapter.deliver(receipt)
            except Exception as exc:
                store.record_delivery_attempt(
                    issue_id=issue.issue_id,
                    adapter_name=adapter.name,
                    attempted_at=now,
                    succeeded=False,
                    error_text=str(exc),
                )
                store.mark_publication_delivery_failed(issue.issue_id)
                raise

            store.record_delivery_attempt(
                issue_id=issue.issue_id,
                adapter_name=adapter.name,
                attempted_at=now,
                succeeded=True,
                error_text=None,
            )
            store.mark_publication_delivered(issue.issue_id, delivered_at=now)
            published_issue_ids.append(issue.issue_id)

        store.set_last_tick_at(now)
        return RuntimeTickResult(
            ticked_at=now,
            window_start=window_start,
            window_end=now,
            due_occurrences=tuple(due_occurrences),
            published_issue_ids=tuple(published_issue_ids),
            skipped_existing_occurrences=tuple(skipped_existing_occurrences),
        )

    def run_loop(
        self,
        slots: Sequence[PublicationSlot],
        apps: Sequence[ContentApp],
        adapter: PrinterAdapter,
        store: SQLiteStateStore,
        profile: RenderProfile,
        poll_interval_seconds: float = 30.0,
        catchup_seconds: int = 60,
        iterations: int | None = None,
        now_fn: Callable[[], datetime] = datetime.now,
        sleep_fn: Callable[[float], None] = time_module.sleep,
    ) -> None:
        completed_iterations = 0
        while iterations is None or completed_iterations < iterations:
            self.run_once(
                slots=slots,
                apps=apps,
                adapter=adapter,
                store=store,
                now=now_fn(),
                profile=profile,
                catchup_seconds=catchup_seconds,
            )
            completed_iterations += 1
            if iterations is not None and completed_iterations >= iterations:
                break
            sleep_fn(poll_interval_seconds)
