from __future__ import annotations

from datetime import date, datetime

from alphaconsole.domain import (
    Issue,
    IssueHeader,
    MergePolicy,
    SceneBlock,
    TriggerMode,
)
from alphaconsole.rendering import render_issue_header, render_issue_text


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

    assert render_issue_header(issue.header) == "\n".join(
        [
            "================================",
            "DATE: 2026-04-20",
            "PRINTED: 12:00",
            "ISSUE NO: 2",
            "TRIGGER: scheduled",
            "--------------------------------",
        ]
    )


def test_render_issue_text_with_multiple_scene_blocks() -> None:
    issue = make_issue(
        blocks=(
            make_scene_block(
                block_id="scene-1",
                title="Lunch",
                scene_note="Eat more vegetables",
            ),
            make_scene_block(
                block_id="scene-2",
                title="Evening",
                checklist_items=("Train", "Stop at 21:00"),
            ),
        )
    )

    assert render_issue_text(issue) == "\n".join(
        [
            "================================",
            "DATE: 2026-04-20",
            "PRINTED: 12:00",
            "ISSUE NO: 2",
            "TRIGGER: scheduled",
            "--------------------------------",
            "",
            "[Lunch]",
            "Eat more vegetables",
            "",
            "--------------------------------",
            "",
            "[Evening]",
            "[ ] Train",
            "[ ] Stop at 21:00",
        ]
    )


def test_render_issue_text_without_blocks_returns_header_only() -> None:
    issue = make_issue(blocks=())

    assert render_issue_text(issue) == render_issue_header(issue.header)
