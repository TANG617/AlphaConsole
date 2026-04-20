from __future__ import annotations

from datetime import datetime, time, timedelta

from alphaconsole.domain import (
    IssueBuildContext,
    MergePolicy,
    PublicationSlot,
    SceneApp,
    SceneBlock,
    TriggerMode,
)
from alphaconsole.services import IssueAssembler


class CountingSceneApp(SceneApp):
    def publish(self, ctx: IssueBuildContext) -> SceneBlock | None:
        self.publish_calls = getattr(self, "publish_calls", 0) + 1
        return super().publish(ctx)


class ExpiredSceneApp(SceneApp):
    def publish(self, ctx: IssueBuildContext) -> SceneBlock | None:
        block = super().publish(ctx)
        if block is None:
            return None

        block.expires_at = ctx.issued_at - timedelta(minutes=1)
        return block


def make_slot(slot_id: str = "lunch-slot") -> PublicationSlot:
    now = datetime(2026, 4, 20, 12, 0, 0)
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
    app_cls: type[SceneApp] = SceneApp,
    app_id: str,
    name: str,
    slot_id: str = "lunch-slot",
    scene_note: str | None = "Default note",
    checklist_items: tuple[str, ...] = (),
    trigger_mode: TriggerMode = TriggerMode.SCHEDULED,
    merge_policy: MergePolicy = MergePolicy.MERGEABLE,
) -> SceneApp:
    now = datetime(2026, 4, 20, 11, 0, 0)
    return app_cls(
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


def test_scheduled_issue_merges_multiple_blocks_in_fifo_order() -> None:
    assembler = IssueAssembler()
    slot = make_slot()
    apps = [
        make_scene_app(app_id="scene-1", name="Breakfast", scene_note="Protein first"),
        make_scene_app(
            app_id="scene-2",
            name="Lunch",
            checklist_items=("Vegetables", "Walk 10 min"),
        ),
    ]

    issue = assembler.assemble_scheduled_issue(
        slot=slot,
        apps=apps,
        now=datetime(2026, 4, 20, 12, 0, 0),
        sequence_of_day=2,
    )

    assert issue.trigger_mode is TriggerMode.SCHEDULED
    assert issue.publication_slot_id == "lunch-slot"
    assert [block.title for block in issue.blocks] == ["Breakfast", "Lunch"]


def test_expired_block_is_filtered_out() -> None:
    assembler = IssueAssembler()
    slot = make_slot()
    apps = [
        make_scene_app(app_cls=ExpiredSceneApp, app_id="expired", name="Expired scene"),
        make_scene_app(app_id="active", name="Active scene", scene_note="Still valid"),
    ]

    issue = assembler.assemble_scheduled_issue(
        slot=slot,
        apps=apps,
        now=datetime(2026, 4, 20, 12, 0, 0),
        sequence_of_day=3,
    )

    assert [block.title for block in issue.blocks] == ["Active scene"]


def test_immediate_trigger_creates_standalone_issue() -> None:
    assembler = IssueAssembler()
    app = make_scene_app(
        app_id="scene-now",
        name="Urgent",
        scene_note="Print now",
        trigger_mode=TriggerMode.IMMEDIATE,
        merge_policy=MergePolicy.STANDALONE,
    )

    issue = assembler.assemble_immediate_issue(
        app=app,
        now=datetime(2026, 4, 20, 12, 5, 0),
        sequence_of_day=4,
    )

    assert issue.trigger_mode is TriggerMode.IMMEDIATE
    assert issue.publication_slot_id is None
    assert len(issue.blocks) == 1
    assert issue.blocks[0].trigger_mode is TriggerMode.IMMEDIATE


def test_one_app_is_published_once_per_issue() -> None:
    assembler = IssueAssembler()
    slot = make_slot()
    app = make_scene_app(
        app_cls=CountingSceneApp,
        app_id="counted",
        name="Counted scene",
        scene_note="Only once",
    )

    issue = assembler.assemble_scheduled_issue(
        slot=slot,
        apps=[app],
        now=datetime(2026, 4, 20, 12, 0, 0),
        sequence_of_day=5,
    )

    assert len(issue.blocks) == 1
    assert app.publish_calls == 1
