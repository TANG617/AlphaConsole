from __future__ import annotations

from datetime import datetime

from alphaconsole.domain import TriggerMode
from alphaconsole.printing import FilePrinterAdapter, RenderedReceipt


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


def test_file_adapter_creates_text_file(tmp_path) -> None:
    output_dir = tmp_path / "nested" / "receipts"
    adapter = FilePrinterAdapter(output_dir=output_dir)
    receipt = make_receipt()

    adapter.deliver(receipt)

    assert (output_dir / "issue-1__receipt_42.txt").exists()


def test_file_adapter_writes_receipt_text_exactly(tmp_path) -> None:
    adapter = FilePrinterAdapter(output_dir=tmp_path)
    receipt = make_receipt(text="rendered 午餐 receipt")

    adapter.deliver(receipt)

    assert (tmp_path / "issue-1__receipt_42.txt").read_text(encoding="utf-8") == (
        "rendered 午餐 receipt"
    )


def test_file_adapter_uses_stable_file_name_rule(tmp_path) -> None:
    adapter = FilePrinterAdapter(output_dir=tmp_path)
    receipt = make_receipt(issue_id="issue-alpha", profile_name="receipt_32")

    adapter.deliver(receipt)

    assert (tmp_path / "issue-alpha__receipt_32.txt").exists()


def test_file_adapter_overwrites_same_named_file(tmp_path) -> None:
    adapter = FilePrinterAdapter(output_dir=tmp_path)
    first = make_receipt(text="first version")
    second = make_receipt(text="second version")

    adapter.deliver(first)
    adapter.deliver(second)

    assert (tmp_path / "issue-1__receipt_42.txt").read_text(encoding="utf-8") == (
        "second version"
    )


def test_file_adapter_writes_header_only_receipt_text(tmp_path) -> None:
    adapter = FilePrinterAdapter(output_dir=tmp_path)
    receipt = make_receipt(text="=" * 42 + "\nDATE: 2026-04-21")

    adapter.deliver(receipt)

    assert (tmp_path / "issue-1__receipt_42.txt").read_text(encoding="utf-8") == (
        "=" * 42 + "\nDATE: 2026-04-21"
    )
