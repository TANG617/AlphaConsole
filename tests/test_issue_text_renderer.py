from __future__ import annotations

from datetime import date, datetime

from alphaconsole.domain import (
    Issue,
    IssueHeader,
    MergePolicy,
    SceneBlock,
    TriggerMode,
)
from alphaconsole.rendering import RECEIPT_32, RECEIPT_42, render_issue, render_issue_header
from alphaconsole.rendering.width import display_width


def make_scene_block(
    *,
    block_id: str,
    title: str,
    scene_note: str | None = None,
    checklist_items: tuple[str, ...] = (),
) -> SceneBlock:
    now = datetime(2026, 4, 20, 12, 0, 0)
    return SceneBlock(
        block_id=block_id,
        block_type="scene",
        title=title,
        body="unused fallback",
        source_app_id=f"scene-{block_id}",
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


def make_issue(*, blocks: tuple[SceneBlock, ...]) -> Issue:
    printed_at = datetime(2026, 4, 20, 12, 0, 0)
    header = IssueHeader(
        issue_date=date(2026, 4, 20),
        printed_at=printed_at,
        sequence_of_day=2,
        trigger_mode=TriggerMode.SCHEDULED,
    )
    return Issue(
        issue_id="issue-1",
        issue_date=printed_at.date(),
        publication_slot_id="lunch-slot",
        trigger_mode=TriggerMode.SCHEDULED,
        sequence_of_day=2,
        header=header,
        blocks=blocks,
        created_at=printed_at,
    )


def test_render_issue_header_text() -> None:
    issue = make_issue(blocks=())
    text = render_issue_header(issue.header, RECEIPT_32)
    lines = text.splitlines()

    assert text == "\n".join(
        [
            "=" * 32,
            "DATE: 2026-04-20",
            "PRINTED: 12:00",
            "ISSUE NO: 2",
            "TRIGGER: scheduled",
            "-" * 32,
        ]
    )
    assert all(display_width(line) <= RECEIPT_32.line_width for line in lines)
    assert display_width(lines[0]) == RECEIPT_32.line_width
    assert display_width(lines[-1]) == RECEIPT_32.line_width


def test_render_issue_text_with_multiple_scene_blocks() -> None:
    issue = make_issue(
        blocks=(
            make_scene_block(
                block_id="scene-1",
                title="Lunch",
                scene_note="Remember vegetables and soup tonight",
            ),
            make_scene_block(
                block_id="scene-2",
                title="Evening",
                checklist_items=("Stretch and review notes together",),
            ),
        )
    )

    text = render_issue(issue, RECEIPT_42)

    assert text == "\n".join(
        [
            "=" * 42,
            "DATE: 2026-04-20",
            "PRINTED: 12:00",
            "ISSUE NO: 2",
            "TRIGGER: scheduled",
            "-" * 42,
            "",
            "[Lunch]",
            "Remember vegetables and soup tonight",
            "",
            "-" * 42,
            "",
            "[Evening]",
            "[ ] Stretch and review notes together",
        ]
    )


def test_render_issue_text_without_blocks_returns_header_only() -> None:
    issue = make_issue(blocks=())

    assert render_issue(issue, RECEIPT_42) == render_issue_header(issue.header, RECEIPT_42)


def test_render_issue_preserves_block_order() -> None:
    issue = make_issue(
        blocks=(
            make_scene_block(block_id="scene-1", title="Breakfast", scene_note="First"),
            make_scene_block(block_id="scene-2", title="Dinner", scene_note="Second"),
        )
    )

    text = render_issue(issue, RECEIPT_42)

    assert text.index("[Breakfast]") < text.index("[Dinner]")


def test_render_issue_is_stable_for_receipt_32_profile() -> None:
    issue = make_issue(
        blocks=(
            make_scene_block(
                block_id="scene-1",
                title="Lunch",
                scene_note="Remember vegetables and soup tonight",
            ),
            make_scene_block(
                block_id="scene-2",
                title="Evening",
                checklist_items=("Stretch and review notes together",),
            ),
        )
    )

    assert render_issue(issue, RECEIPT_32) == "\n".join(
        [
            "=" * 32,
            "DATE: 2026-04-20",
            "PRINTED: 12:00",
            "ISSUE NO: 2",
            "TRIGGER: scheduled",
            "-" * 32,
            "",
            "[Lunch]",
            "Remember vegetables and soup",
            "tonight",
            "",
            "-" * 32,
            "",
            "[Evening]",
            "[ ] Stretch and review notes",
            "    together",
        ]
    )


def test_render_issue_is_stable_for_receipt_42_profile() -> None:
    issue = make_issue(
        blocks=(
            make_scene_block(
                block_id="scene-1",
                title="Lunch",
                scene_note="Remember vegetables and soup tonight",
            ),
            make_scene_block(
                block_id="scene-2",
                title="Evening",
                checklist_items=("Stretch and review notes together",),
            ),
        )
    )

    assert render_issue(issue, RECEIPT_42) == "\n".join(
        [
            "=" * 42,
            "DATE: 2026-04-20",
            "PRINTED: 12:00",
            "ISSUE NO: 2",
            "TRIGGER: scheduled",
            "-" * 42,
            "",
            "[Lunch]",
            "Remember vegetables and soup tonight",
            "",
            "-" * 42,
            "",
            "[Evening]",
            "[ ] Stretch and review notes together",
        ]
    )
