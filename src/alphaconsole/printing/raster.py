from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .artifact import RenderedReceipt


@dataclass(slots=True)
class RasterizedReceipt:
    issue_id: str
    image: Image.Image
    rendered_at: datetime
    width_px: int
    height_px: int


def rasterize_receipt(
    receipt: RenderedReceipt,
    *,
    font_path: Path | None = None,
    font_size: int = 18,
    line_spacing: int = 4,
    horizontal_padding: int = 8,
    vertical_padding: int = 8,
) -> RasterizedReceipt:
    font = load_receipt_font(font_path=font_path, font_size=font_size)
    lines = _split_lines(receipt.text)
    scratch = Image.new("L", (1, 1), color=255)
    scratch_draw = ImageDraw.Draw(scratch)
    line_height = _measure_line_height(scratch_draw, font)
    max_line_width = max(_measure_line_width(scratch_draw, font, line) for line in lines)

    width_px = max(1, max_line_width + horizontal_padding * 2)
    height_px = max(
        1,
        vertical_padding * 2
        + len(lines) * line_height
        + max(0, len(lines) - 1) * line_spacing,
    )

    image = Image.new("L", (width_px, height_px), color=255)
    draw = ImageDraw.Draw(image)
    current_y = vertical_padding
    for line in lines:
        draw.text((horizontal_padding, current_y), line, fill=0, font=font)
        current_y += line_height + line_spacing

    bitmap = image.point(lambda value: 0 if value < 128 else 255, mode="1")
    return RasterizedReceipt(
        issue_id=receipt.issue_id,
        image=bitmap,
        rendered_at=receipt.rendered_at,
        width_px=bitmap.width,
        height_px=bitmap.height,
    )


def load_receipt_font(*, font_path: Path | None, font_size: int):
    if font_path is not None:
        if not font_path.exists():
            raise FileNotFoundError(f"Font file not found: {font_path}")
        return ImageFont.truetype(str(font_path), font_size)

    try:
        return ImageFont.load_default(size=font_size)
    except TypeError:
        return ImageFont.load_default()


def _split_lines(text: str) -> list[str]:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = normalized.split("\n")
    return lines or [""]


def _measure_line_width(draw: ImageDraw.ImageDraw, font, line: str) -> int:
    bbox = draw.textbbox((0, 0), line or " ", font=font)
    return bbox[2] - bbox[0]


def _measure_line_height(draw: ImageDraw.ImageDraw, font) -> int:
    bbox = draw.textbbox((0, 0), "Ag", font=font)
    return max(1, bbox[3] - bbox[1])
