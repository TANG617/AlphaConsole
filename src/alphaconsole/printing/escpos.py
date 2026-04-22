from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from PIL import Image

from .raster import RasterizedReceipt


@dataclass(slots=True, frozen=True)
class EscPosPayload:
    issue_id: str
    data: bytes
    encoded_at: datetime


def build_escpos_payload(
    rasterized: RasterizedReceipt,
    *,
    cut: bool = True,
) -> EscPosPayload:
    return EscPosPayload(
        issue_id=rasterized.issue_id,
        data=encode_raster_receipt_to_escpos(rasterized.image, cut=cut),
        encoded_at=datetime.now(),
    )


def encode_raster_receipt_to_escpos(
    image: Image.Image,
    *,
    cut: bool = True,
) -> bytes:
    bitmap = image.convert("1")
    width_px, height_px = bitmap.size
    width_bytes = (width_px + 7) // 8
    data = bytearray()
    pixels = bitmap.load()

    for y in range(height_px):
        for byte_index in range(width_bytes):
            packed = 0
            for bit in range(8):
                x = byte_index * 8 + bit
                if x >= width_px:
                    continue
                if pixels[x, y] == 0:
                    packed |= 0x80 >> bit
            data.append(packed)

    payload = bytearray()
    payload.extend(b"\x1b@")
    payload.extend(
        b"\x1d\x76\x30\x00"
        + bytes(
            (
                width_bytes & 0xFF,
                (width_bytes >> 8) & 0xFF,
                height_px & 0xFF,
                (height_px >> 8) & 0xFF,
            )
        )
    )
    payload.extend(data)
    payload.extend(b"\n\n\n")
    if cut:
        payload.extend(b"\x1dV\x00")
    return bytes(payload)
