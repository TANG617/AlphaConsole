from __future__ import annotations

from .profiles import PrinterProfile


def build_calibration_receipt_text(
    *,
    target_id: str,
    printer_profile: PrinterProfile,
    render_profile_name: str,
) -> str:
    line_width = _resolve_line_width(render_profile_name)
    ruler = _repeat_to_width("1234567890", line_width)
    boundary = _build_boundary(line_width)

    lines = [
        "ALPHACONSOLE CALIBRATION",
        f"TARGET: {target_id}",
        f"PRINTER: {printer_profile.profile_id}",
        f"RENDER: {render_profile_name}",
        f"PAPER: {printer_profile.paper_width_mm}mm",
        f"WIDTH: {printer_profile.printable_width_dots} dots",
        "RULER:",
        ruler,
        "BOUNDARY:",
        boundary,
        "ASCII:",
        "THE QUICK BROWN FOX",
        "0123456789 ABC xyz",
        "CJK:",
        "你好，打印。校准测试。",
        "CHECKLIST:",
        "[ ] Left edge",
        "[ ] Right edge",
        "[ ] Line spacing",
        "CUT/FEED:",
        "Check top margin and cut gap.",
    ]
    return "\n".join(lines)


def _resolve_line_width(render_profile_name: str) -> int:
    normalized = render_profile_name.strip().lower().replace("-", "_")
    if normalized in {"receipt32", "receipt_32"}:
        return 32
    if normalized in {"receipt42", "receipt_42"}:
        return 42
    return 42


def _repeat_to_width(token: str, width: int) -> str:
    repeated = (token * ((width // len(token)) + 1))[:width]
    return repeated


def _build_boundary(width: int) -> str:
    if width <= 1:
        return "|"
    if width == 2:
        return "||"
    return "|" + ("-" * (width - 2)) + "|"
