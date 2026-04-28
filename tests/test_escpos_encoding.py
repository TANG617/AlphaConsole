from __future__ import annotations

from PIL import Image

from alphaconsole.printing import encode_raster_receipt_to_escpos


def test_encode_raster_receipt_to_escpos_produces_non_empty_bytes() -> None:
    image = Image.new("L", (16, 16), color=255)

    payload = encode_raster_receipt_to_escpos(image)

    assert payload
    assert payload.startswith(b"\x1b@")


def test_encode_raster_receipt_to_escpos_differs_when_cut_disabled() -> None:
    image = Image.new("L", (16, 16), color=255)

    with_cut = encode_raster_receipt_to_escpos(image, cut=True)
    without_cut = encode_raster_receipt_to_escpos(image, cut=False)

    assert with_cut != without_cut


def test_encode_raster_receipt_to_escpos_is_stable_for_same_input() -> None:
    image = Image.new("L", (16, 16), color=255)

    first = encode_raster_receipt_to_escpos(image)
    second = encode_raster_receipt_to_escpos(image)

    assert first == second


def test_encode_raster_receipt_to_escpos_differs_when_feed_lines_change() -> None:
    image = Image.new("L", (16, 16), color=255)

    feed_2 = encode_raster_receipt_to_escpos(image, feed_lines=2)
    feed_6 = encode_raster_receipt_to_escpos(image, feed_lines=6)

    assert feed_2 != feed_6


def test_encode_raster_receipt_to_escpos_handles_blank_small_image() -> None:
    image = Image.new("L", (8, 8), color=255)

    payload = encode_raster_receipt_to_escpos(image)

    assert payload.startswith(b"\x1b@")
    assert len(payload) > 8
