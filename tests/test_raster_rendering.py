from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from alphaconsole.domain import TriggerMode
from alphaconsole.printing import RenderedReceipt, rasterize_receipt


def make_receipt(text: str) -> RenderedReceipt:
    return RenderedReceipt(
        issue_id="receipt-1",
        publication_slot_id="noon",
        trigger_mode=TriggerMode.SCHEDULED,
        profile_name="receipt_42",
        text=text,
        rendered_at=datetime(2026, 4, 22, 12, 0, 0),
    )


def test_rasterize_receipt_creates_non_empty_image() -> None:
    rasterized = rasterize_receipt(make_receipt("ALPHACONSOLE\nTEST PAGE"))

    assert rasterized.width_px > 0
    assert rasterized.height_px > 0
    assert rasterized.image.size == (rasterized.width_px, rasterized.height_px)


def test_rasterize_receipt_dimensions_are_stable_for_same_input() -> None:
    receipt = make_receipt("ALPHACONSOLE\nTEST PAGE")

    first = rasterize_receipt(receipt)
    second = rasterize_receipt(receipt)

    assert (first.width_px, first.height_px) == (second.width_px, second.height_px)


def test_rasterize_receipt_longer_text_increases_height() -> None:
    short_receipt = make_receipt("short line")
    long_receipt = make_receipt("line one\nline two\nline three\nline four")

    short_raster = rasterize_receipt(short_receipt)
    long_raster = rasterize_receipt(long_receipt)

    assert long_raster.height_px > short_raster.height_px


def test_rasterize_receipt_supports_default_font_for_ascii() -> None:
    rasterized = rasterize_receipt(make_receipt("ASCII ONLY PATH"))

    assert rasterized.width_px >= 1
    assert rasterized.height_px >= 1


def test_rasterize_receipt_raises_clear_error_for_missing_font_file() -> None:
    with pytest.raises(FileNotFoundError, match="Font file not found"):
        rasterize_receipt(
            make_receipt("font path"),
            font_path=Path("/does/not/exist.ttf"),
        )
