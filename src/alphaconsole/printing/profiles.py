from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class PrinterCapability:
    supports_cut: bool
    transport: str = "escpos_raster"


@dataclass(slots=True, frozen=True)
class PrinterProfile:
    profile_id: str
    paper_width_mm: int
    printable_width_dots: int
    horizontal_padding_dots: int
    line_feed_after_print: int
    supports_cut: bool
    default_cut: bool
    default_font_size: int
    default_line_spacing: int
    recommended_render_profile_name: str

    @property
    def capability(self) -> PrinterCapability:
        return PrinterCapability(supports_cut=self.supports_cut)


GENERIC_58MM = PrinterProfile(
    profile_id="generic_58mm",
    paper_width_mm=58,
    printable_width_dots=384,
    horizontal_padding_dots=8,
    line_feed_after_print=4,
    supports_cut=True,
    default_cut=True,
    default_font_size=18,
    default_line_spacing=4,
    recommended_render_profile_name="receipt_32",
)

GENERIC_80MM = PrinterProfile(
    profile_id="generic_80mm",
    paper_width_mm=80,
    printable_width_dots=576,
    horizontal_padding_dots=12,
    line_feed_after_print=4,
    supports_cut=True,
    default_cut=True,
    default_font_size=18,
    default_line_spacing=4,
    recommended_render_profile_name="receipt_42",
)

_BUILTIN_PRINTER_PROFILES = {
    GENERIC_58MM.profile_id: GENERIC_58MM,
    GENERIC_80MM.profile_id: GENERIC_80MM,
}


def resolve_printer_profile(profile_id: str) -> PrinterProfile:
    normalized = profile_id.strip().lower()
    try:
        return _BUILTIN_PRINTER_PROFILES[normalized]
    except KeyError as exc:
        raise ValueError(f"Unsupported printer profile: {profile_id!r}.") from exc


def list_printer_profiles() -> tuple[PrinterProfile, ...]:
    return tuple(_BUILTIN_PRINTER_PROFILES.values())
