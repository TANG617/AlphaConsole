from __future__ import annotations

from datetime import datetime

from alphaconsole.printing import EscPosBytesFileAdapter
from alphaconsole.printing.test_page import build_test_receipt
from alphaconsole.rendering import RECEIPT_42


def test_bytes_file_adapter_creates_bin_file(tmp_path) -> None:
    adapter = EscPosBytesFileAdapter(
        target_id="bytes_debug",
        output_dir=tmp_path / "escpos",
    )

    adapter.deliver(
        build_test_receipt(
            RECEIPT_42,
            issue_id="issue-1",
            rendered_at=datetime(2026, 4, 22, 12, 0, 0),
        )
    )

    output_path = tmp_path / "escpos" / "issue-1__bytes_debug.bin"
    assert output_path.exists()
    assert output_path.read_bytes()


def test_bytes_file_adapter_overwrites_same_filename(tmp_path) -> None:
    output_dir = tmp_path / "escpos"
    adapter = EscPosBytesFileAdapter(
        target_id="bytes_debug",
        output_dir=output_dir,
    )
    output_path = output_dir / "issue-1__bytes_debug.bin"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(b"sentinel")

    adapter.deliver(build_test_receipt(RECEIPT_42, issue_id="issue-1"))

    assert output_path.read_bytes() != b"sentinel"


def test_bytes_file_adapter_auto_creates_output_dir(tmp_path) -> None:
    output_dir = tmp_path / "nested" / "escpos"
    adapter = EscPosBytesFileAdapter(
        target_id="bytes_debug",
        output_dir=output_dir,
    )

    adapter.deliver(build_test_receipt(RECEIPT_42, issue_id="issue-2"))

    assert (output_dir / "issue-2__bytes_debug.bin").exists()
