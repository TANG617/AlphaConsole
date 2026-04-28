from __future__ import annotations

from alphaconsole.printing import GENERIC_58MM, build_calibration_receipt_text


def test_build_calibration_receipt_text_contains_core_sections() -> None:
    text = build_calibration_receipt_text(
        target_id="receipt_printer",
        printer_profile=GENERIC_58MM,
        render_profile_name="receipt_32",
    )

    assert "ALPHACONSOLE CALIBRATION" in text
    assert "TARGET: receipt_printer" in text
    assert "PRINTER: generic_58mm" in text
    assert "RENDER: receipt_32" in text
    assert "RULER:" in text
    assert "BOUNDARY:" in text
    assert "THE QUICK BROWN FOX" in text
    assert "你好，打印。校准测试。" in text
    assert "[ ] Left edge" in text


def test_build_calibration_receipt_text_is_stable_for_same_input() -> None:
    first = build_calibration_receipt_text(
        target_id="receipt_printer",
        printer_profile=GENERIC_58MM,
        render_profile_name="receipt_32",
    )
    second = build_calibration_receipt_text(
        target_id="receipt_printer",
        printer_profile=GENERIC_58MM,
        render_profile_name="receipt_32",
    )

    assert first == second
