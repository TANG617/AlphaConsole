from __future__ import annotations

from datetime import datetime

from alphaconsole.domain import TriggerMode
from alphaconsole.printing import MemoryPrinterAdapter, RenderedReceipt


def make_receipt(
    *,
    issue_id: str = "issue-1",
    profile_name: str = "receipt_42",
    text: str = "sample text",
) -> RenderedReceipt:
    return RenderedReceipt(
        issue_id=issue_id,
        publication_slot_id="lunch-slot",
        trigger_mode=TriggerMode.SCHEDULED,
        profile_name=profile_name,
        text=text,
        rendered_at=datetime(2026, 4, 20, 12, 0, 0),
    )


def test_memory_adapter_appends_receipt() -> None:
    adapter = MemoryPrinterAdapter()

    adapter.deliver(make_receipt())

    assert len(adapter.receipts) == 1


def test_memory_adapter_preserves_receipt_content() -> None:
    adapter = MemoryPrinterAdapter()
    receipt = make_receipt(text="rendered receipt text")

    adapter.deliver(receipt)

    assert adapter.receipts[0] is receipt
    assert adapter.receipts[0].text == "rendered receipt text"


def test_memory_adapter_preserves_delivery_order() -> None:
    adapter = MemoryPrinterAdapter()
    first = make_receipt(issue_id="issue-1")
    second = make_receipt(issue_id="issue-2")

    adapter.deliver(first)
    adapter.deliver(second)

    assert [receipt.issue_id for receipt in adapter.receipts] == ["issue-1", "issue-2"]
