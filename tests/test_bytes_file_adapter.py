from __future__ import annotations

from datetime import datetime

from alphaconsole.printing import EscPosBytesFileAdapter, GENERIC_58MM
from alphaconsole.printing.test_page import build_test_receipt
from alphaconsole.rendering import RECEIPT_42


def test_bytes_file_adapter_creates_bin_file(tmp_path) -> None:
    adapter = EscPosBytesFileAdapter(
        target_id="bytes_debug",
        output_dir=tmp_path / "escpos",
        printer_profile=GENERIC_58MM,
        printer_profile_name=GENERIC_58MM.profile_id,
        render_profile_name=RECEIPT_42.name,
    )

    diagnostics = adapter.deliver(
        build_test_receipt(
            RECEIPT_42,
            issue_id="issue-1",
            rendered_at=datetime(2026, 4, 22, 12, 0, 0),
        )
    )

    output_path = tmp_path / "escpos" / "issue-1__bytes_debug.bin"
    assert output_path.exists()
    assert output_path.read_bytes()
    assert diagnostics.adapter_name == "escpos_bytes_file"
    assert diagnostics.target_id == "bytes_debug"
    assert diagnostics.bytes_length is not None
    assert diagnostics.bytes_length > 0


def test_bytes_file_adapter_overwrites_same_filename(tmp_path) -> None:
    output_dir = tmp_path / "escpos"
    adapter = EscPosBytesFileAdapter(
        target_id="bytes_debug",
        output_dir=output_dir,
        printer_profile=GENERIC_58MM,
        printer_profile_name=GENERIC_58MM.profile_id,
        render_profile_name=RECEIPT_42.name,
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
        printer_profile=GENERIC_58MM,
        printer_profile_name=GENERIC_58MM.profile_id,
        render_profile_name=RECEIPT_42.name,
    )

    adapter.deliver(build_test_receipt(RECEIPT_42, issue_id="issue-2"))

    assert (output_dir / "issue-2__bytes_debug.bin").exists()


def test_bytes_file_adapter_diagnostics_uses_receipt_profile_name(tmp_path) -> None:
    adapter = EscPosBytesFileAdapter(
        target_id="bytes_debug",
        output_dir=tmp_path / "escpos",
        printer_profile=GENERIC_58MM,
        printer_profile_name=GENERIC_58MM.profile_id,
        render_profile_name="receipt_32",
    )

    diagnostics = adapter.deliver(build_test_receipt(RECEIPT_42, issue_id="issue-3"))

    assert diagnostics.render_profile_name == RECEIPT_42.name
    assert diagnostics.render_profile_name != "receipt_32"
