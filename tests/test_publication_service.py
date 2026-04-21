from __future__ import annotations

from collections.abc import Sequence
from datetime import date, datetime, time

from alphaconsole.application import PublicationResult, PublicationService
from alphaconsole.domain import (
    ContentApp,
    Issue,
    IssueHeader,
    MergePolicy,
    PublicationSlot,
    SceneApp,
    TriggerMode,
)
from alphaconsole.printing import PrinterAdapter, RenderedReceipt
from alphaconsole.rendering import RECEIPT_32


def make_slot(slot_id: str = "lunch-slot") -> PublicationSlot:
    now = datetime(2026, 4, 21, 12, 0, 0)
    return PublicationSlot(
        slot_id=slot_id,
        name="Lunch",
        description=None,
        publish_time=time(12, 0),
        recurrence_rule=None,
        is_enabled=True,
        created_at=now,
        updated_at=now,
    )


def make_scene_app(
    *,
    app_id: str,
    name: str,
    slot_id: str = "lunch-slot",
    scene_note: str | None = "Default note",
) -> SceneApp:
    now = datetime(2026, 4, 21, 11, 0, 0)
    return SceneApp(
        app_id=app_id,
        app_type="scene",
        name=name,
        description=None,
        target_publication_slot_id=slot_id,
        prepare_at=time(11, 30),
        default_trigger_mode=TriggerMode.SCHEDULED,
        default_merge_policy=MergePolicy.MERGEABLE,
        default_template_type="scene.default",
        expiration_policy=None,
        is_enabled=True,
        created_at=now,
        updated_at=now,
        scene_note=scene_note,
        checklist_items=(),
        scene_description=None,
        recurrence_rule=None,
    )


def make_issue(*, trigger_mode: TriggerMode) -> Issue:
    issued_at = datetime(2026, 4, 21, 12, 0, 0)
    header = IssueHeader(
        issue_date=date(2026, 4, 21),
        printed_at=issued_at,
        sequence_of_day=3,
        trigger_mode=trigger_mode,
    )
    return Issue(
        issue_id="issue-1",
        issue_date=issued_at.date(),
        publication_slot_id="lunch-slot"
        if trigger_mode is TriggerMode.SCHEDULED
        else None,
        trigger_mode=trigger_mode,
        sequence_of_day=3,
        header=header,
        blocks=(),
        created_at=issued_at,
    )


def make_receipt(*, trigger_mode: TriggerMode) -> RenderedReceipt:
    return RenderedReceipt(
        issue_id="issue-1",
        publication_slot_id="lunch-slot"
        if trigger_mode is TriggerMode.SCHEDULED
        else None,
        trigger_mode=trigger_mode,
        profile_name="receipt_32",
        text="rendered receipt",
        rendered_at=datetime(2026, 4, 21, 12, 0, 0),
    )


class DummyAdapter(PrinterAdapter):
    name = "dummy"

    def deliver(self, receipt: RenderedReceipt) -> None:
        return None


class SpyIssueAssembler:
    def __init__(self, *, scheduled_issue: Issue, immediate_issue: Issue) -> None:
        self.scheduled_issue = scheduled_issue
        self.immediate_issue = immediate_issue
        self.scheduled_call: tuple[PublicationSlot, Sequence[ContentApp], datetime, int] | None = None
        self.immediate_call: tuple[ContentApp, datetime, int] | None = None

    def assemble_scheduled_issue(
        self,
        slot: PublicationSlot,
        apps: Sequence[ContentApp],
        now: datetime,
        sequence_of_day: int,
    ) -> Issue:
        self.scheduled_call = (slot, apps, now, sequence_of_day)
        return self.scheduled_issue

    def assemble_immediate_issue(
        self,
        app: ContentApp,
        now: datetime,
        sequence_of_day: int,
    ) -> Issue:
        self.immediate_call = (app, now, sequence_of_day)
        return self.immediate_issue


class SpyPrintService:
    def __init__(self, *, receipt: RenderedReceipt) -> None:
        self.receipt = receipt
        self.calls: list[tuple[Issue, PrinterAdapter, object]] = []

    def print_issue(
        self,
        issue: Issue,
        adapter: PrinterAdapter,
        profile,
    ) -> RenderedReceipt:
        self.calls.append((issue, adapter, profile))
        return self.receipt


def test_publication_service_publish_scheduled_orchestrates_dependencies() -> None:
    slot = make_slot()
    apps = (make_scene_app(app_id="scene-1", name="Lunch"),)
    issue = make_issue(trigger_mode=TriggerMode.SCHEDULED)
    receipt = make_receipt(trigger_mode=TriggerMode.SCHEDULED)
    assembler = SpyIssueAssembler(scheduled_issue=issue, immediate_issue=issue)
    print_service = SpyPrintService(receipt=receipt)
    service = PublicationService(assembler=assembler, print_service=print_service)
    adapter = DummyAdapter()
    now = datetime(2026, 4, 21, 12, 0, 0)

    result = service.publish_scheduled(
        slot=slot,
        apps=apps,
        adapter=adapter,
        now=now,
        sequence_of_day=3,
        profile=RECEIPT_32,
    )

    assert isinstance(result, PublicationResult)
    assert assembler.scheduled_call == (slot, apps, now, 3)
    assert print_service.calls == [(issue, adapter, RECEIPT_32)]
    assert result.issue is issue
    assert result.receipt is receipt
    assert result.adapter_name == "dummy"


def test_publication_service_publish_immediate_orchestrates_dependencies() -> None:
    app = make_scene_app(app_id="scene-now", name="Now")
    issue = make_issue(trigger_mode=TriggerMode.IMMEDIATE)
    receipt = make_receipt(trigger_mode=TriggerMode.IMMEDIATE)
    assembler = SpyIssueAssembler(
        scheduled_issue=make_issue(trigger_mode=TriggerMode.SCHEDULED),
        immediate_issue=issue,
    )
    print_service = SpyPrintService(receipt=receipt)
    service = PublicationService(assembler=assembler, print_service=print_service)
    adapter = DummyAdapter()
    now = datetime(2026, 4, 21, 12, 5, 0)

    result = service.publish_immediate(
        app=app,
        adapter=adapter,
        now=now,
        sequence_of_day=4,
        profile=RECEIPT_32,
    )

    assert assembler.immediate_call == (app, now, 4)
    assert print_service.calls == [(issue, adapter, RECEIPT_32)]
    assert result.issue is issue
    assert result.receipt is receipt
    assert result.adapter_name == "dummy"
