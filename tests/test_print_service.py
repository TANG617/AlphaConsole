from __future__ import annotations

from datetime import date, datetime

import pytest

from alphaconsole.domain import (
    Issue,
    IssueHeader,
    MergePolicy,
    SceneBlock,
    TriggerMode,
)
from alphaconsole.printing import MemoryPrinterAdapter, PrintService, PrinterAdapter
from alphaconsole.rendering import RECEIPT_32, RECEIPT_42, render_issue


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


class RaisingPrinterAdapter(PrinterAdapter):
    name = "raising"

    def deliver(self, receipt) -> None:
        raise RuntimeError("delivery failed")


def test_render_issue_to_receipt_creates_rendered_receipt() -> None:
    service = PrintService()
    issue = make_issue(
        blocks=(make_scene_block(block_id="scene-1", title="Lunch", scene_note="Soup"),)
    )

    receipt = service.render_issue_to_receipt(issue, RECEIPT_42)

    assert receipt.issue_id == "issue-1"
    assert receipt.publication_slot_id == "lunch-slot"
    assert receipt.trigger_mode is TriggerMode.SCHEDULED
    assert receipt.profile_name == "receipt_42"
    assert receipt.text == render_issue(issue, RECEIPT_42)


def test_print_issue_delivers_same_receipt_instance_to_adapter() -> None:
    service = PrintService()
    adapter = MemoryPrinterAdapter()
    issue = make_issue(
        blocks=(make_scene_block(block_id="scene-1", title="Lunch", scene_note="Soup"),)
    )

    receipt = service.print_issue(issue, adapter, RECEIPT_42)

    assert adapter.receipts[0] is receipt


def test_rendered_receipt_changes_with_profile() -> None:
    service = PrintService()
    issue = make_issue(
        blocks=(
            make_scene_block(
                block_id="scene-1",
                title="Lunch",
                scene_note="Remember vegetables and soup tonight",
            ),
        )
    )

    receipt_32 = service.render_issue_to_receipt(issue, RECEIPT_32)
    receipt_42 = service.render_issue_to_receipt(issue, RECEIPT_42)

    assert receipt_32.profile_name == "receipt_32"
    assert receipt_42.profile_name == "receipt_42"
    assert receipt_32.text != receipt_42.text


def test_print_service_bubbles_up_adapter_exception() -> None:
    service = PrintService()
    issue = make_issue(
        blocks=(make_scene_block(block_id="scene-1", title="Lunch", scene_note="Soup"),)
    )

    with pytest.raises(RuntimeError, match="delivery failed"):
        service.print_issue(issue, RaisingPrinterAdapter(), RECEIPT_42)
