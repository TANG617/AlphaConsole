from __future__ import annotations

from datetime import datetime

from alphaconsole.domain import MergePolicy, SceneBlock, TriggerMode
from alphaconsole.rendering import RECEIPT_32, RenderProfile, render_scene_block


def make_scene_block(
    *,
    title: str = "Lunch",
    scene_note: str | None = "Eat more vegetables",
    checklist_items: tuple[str, ...] = ("Healthy meal",),
) -> SceneBlock:
    now = datetime(2026, 4, 20, 12, 0, 0)
    return SceneBlock(
        block_id="block-1",
        block_type="scene",
        title=title,
        body="unused fallback",
        source_app_id="scene-lunch",
        source_app_type="scene",
        publication_slot_id="lunch-slot",
        trigger_mode=TriggerMode.SCHEDULED,
        merge_policy=MergePolicy.MERGEABLE,
        expires_at=None,
        template_type="scene.default",
        created_at=now,
        scene_note=scene_note,
        checklist_items=checklist_items,
    )


def test_render_scene_block_note_only() -> None:
    text = render_scene_block(
        make_scene_block(scene_note="No soda today", checklist_items=()),
        RECEIPT_32,
    )

    assert text == "[Lunch]\nNo soda today"


def test_render_scene_block_checklist_only() -> None:
    text = render_scene_block(
        make_scene_block(scene_note=None, checklist_items=("Train", "Stop at 21:00")),
        RECEIPT_32,
    )

    assert text == "[Lunch]\n[ ] Train\n[ ] Stop at 21:00"


def test_render_scene_block_note_and_checklist() -> None:
    text = render_scene_block(
        make_scene_block(
            scene_note="No soda today",
            checklist_items=("Train", "Stop at 21:00"),
        ),
        RECEIPT_32,
    )

    assert text == "[Lunch]\nNo soda today\n[ ] Train\n[ ] Stop at 21:00"


def test_render_scene_block_wraps_long_note() -> None:
    profile = RenderProfile(name="test_16", line_width=16)
    text = render_scene_block(
        make_scene_block(
            scene_note="Bring vegetables and soup",
            checklist_items=(),
        ),
        profile,
    )

    assert text == "[Lunch]\nBring vegetables\nand soup"


def test_render_scene_block_wraps_long_checklist_item_with_indent() -> None:
    profile = RenderProfile(name="test_20", line_width=20)
    text = render_scene_block(
        make_scene_block(
            scene_note=None,
            checklist_items=("Bring vegetables and soup",),
        ),
        profile,
    )

    assert text == "[Lunch]\n[ ] Bring vegetables\n    and soup"


def test_render_scene_block_folds_empty_string_note() -> None:
    text = render_scene_block(
        make_scene_block(scene_note="", checklist_items=("Train",)),
        RECEIPT_32,
    )

    assert text == "[Lunch]\n[ ] Train"
