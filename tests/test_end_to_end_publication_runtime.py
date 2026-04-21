from __future__ import annotations

from datetime import datetime, time

from alphaconsole.application import PublicationResult, PublicationService
from alphaconsole.domain import MergePolicy, PublicationSlot, SceneApp, TriggerMode
from alphaconsole.printing import MemoryPrinterAdapter, RenderedReceipt


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
    checklist_items: tuple[str, ...] = (),
    trigger_mode: TriggerMode = TriggerMode.SCHEDULED,
    merge_policy: MergePolicy = MergePolicy.MERGEABLE,
) -> SceneApp:
    now = datetime(2026, 4, 21, 11, 0, 0)
    return SceneApp(
        app_id=app_id,
        app_type="scene",
        name=name,
        description=None,
        target_publication_slot_id=slot_id,
        prepare_at=time(11, 30),
        default_trigger_mode=trigger_mode,
        default_merge_policy=merge_policy,
        default_template_type="scene.default",
        expiration_policy=None,
        is_enabled=True,
        created_at=now,
        updated_at=now,
        scene_note=scene_note,
        checklist_items=checklist_items,
        scene_description=None,
        recurrence_rule=None,
    )


def test_publish_scheduled_runs_dry_run_end_to_end() -> None:
    slot = make_slot()
    apps = [
        make_scene_app(app_id="scene-1", name="Breakfast", scene_note="Protein first"),
        make_scene_app(
            app_id="scene-2",
            name="Evening",
            checklist_items=("Stretch", "Review notes"),
        ),
    ]
    adapter = MemoryPrinterAdapter()
    service = PublicationService()

    result = service.publish_scheduled(
        slot=slot,
        apps=apps,
        adapter=adapter,
        now=datetime(2026, 4, 21, 12, 0, 0),
        sequence_of_day=2,
    )

    assert isinstance(result, PublicationResult)
    assert result.issue.trigger_mode is TriggerMode.SCHEDULED
    assert isinstance(result.receipt, RenderedReceipt)
    assert result.receipt is adapter.receipts[0]
    assert len(result.issue.blocks) == 2
    assert result.receipt.text.index("[Breakfast]") < result.receipt.text.index("[Evening]")
    assert result.issue.printed_at is None


def test_publish_immediate_runs_dry_run_end_to_end() -> None:
    app = make_scene_app(
        app_id="scene-now",
        name="Urgent",
        scene_note="Print now",
        trigger_mode=TriggerMode.IMMEDIATE,
        merge_policy=MergePolicy.STANDALONE,
    )
    adapter = MemoryPrinterAdapter()
    service = PublicationService()

    result = service.publish_immediate(
        app=app,
        adapter=adapter,
        now=datetime(2026, 4, 21, 12, 5, 0),
        sequence_of_day=3,
    )

    assert result.issue.trigger_mode is TriggerMode.IMMEDIATE
    assert result.issue.publication_slot_id is None
    assert len(result.issue.blocks) == 1
    assert result.receipt is adapter.receipts[0]
    assert result.receipt.trigger_mode is TriggerMode.IMMEDIATE
    assert result.issue.printed_at is None


def test_publish_scheduled_allows_header_only_empty_issue() -> None:
    slot = make_slot()
    app = make_scene_app(
        app_id="scene-empty",
        name="Empty",
        scene_note=None,
        checklist_items=(),
    )
    adapter = MemoryPrinterAdapter()
    service = PublicationService()

    result = service.publish_scheduled(
        slot=slot,
        apps=[app],
        adapter=adapter,
        now=datetime(2026, 4, 21, 12, 0, 0),
        sequence_of_day=4,
    )

    assert isinstance(result, PublicationResult)
    assert result.issue.blocks == ()
    assert result.receipt is adapter.receipts[0]
    assert "DATE: 2026-04-21" in result.receipt.text
    assert result.issue.printed_at is None
