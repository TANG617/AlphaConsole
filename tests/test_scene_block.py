from __future__ import annotations

from datetime import datetime, time

from alphaconsole.domain import (
    IssueBuildContext,
    MergePolicy,
    SceneApp,
    SceneBlock,
    TriggerMode,
)


def make_scene_app(
    *,
    name: str = "Lunch",
    scene_note: str | None = "Eat more vegetables",
    checklist_items: tuple[str, ...] = ("Healthy meal",),
) -> SceneApp:
    now = datetime(2026, 4, 20, 12, 0, 0)
    return SceneApp(
        app_id=f"scene-{name.lower()}",
        app_type="scene",
        name=name,
        description=None,
        target_publication_slot_id="lunch-slot",
        prepare_at=time(11, 30),
        default_trigger_mode=TriggerMode.SCHEDULED,
        default_merge_policy=MergePolicy.MERGEABLE,
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


def make_context() -> IssueBuildContext:
    issued_at = datetime(2026, 4, 20, 12, 0, 0)
    return IssueBuildContext(
        issue_id="issue-1",
        issue_date=issued_at.date(),
        issued_at=issued_at,
        publication_slot_id="lunch-slot",
        trigger_mode=TriggerMode.SCHEDULED,
        sequence_of_day=1,
    )


def test_scene_app_publishes_scene_block() -> None:
    block = make_scene_app().publish(make_context())

    assert isinstance(block, SceneBlock)
    assert block is not None
    assert block.title == "Lunch"
    assert block.scene_note == "Eat more vegetables"
    assert block.checklist_items == ("Healthy meal",)


def test_note_only_scene_can_publish() -> None:
    block = make_scene_app(scene_note="No soda today", checklist_items=()).publish(
        make_context()
    )

    assert block is not None
    assert block.scene_note == "No soda today"
    assert block.checklist_items == ()
    assert block.body == "No soda today"


def test_checklist_only_scene_can_publish() -> None:
    block = make_scene_app(scene_note=None, checklist_items=("Train", "Stop at 21:00")).publish(
        make_context()
    )

    assert block is not None
    assert block.scene_note is None
    assert block.checklist_items == ("Train", "Stop at 21:00")
    assert block.body == "[ ] Train\n[ ] Stop at 21:00"


def test_note_and_checklist_scene_can_publish() -> None:
    block = make_scene_app(
        scene_note="No soda today",
        checklist_items=("Train", "Stop at 21:00"),
    ).publish(make_context())

    assert block is not None
    assert block.body == "No soda today\n[ ] Train\n[ ] Stop at 21:00"
