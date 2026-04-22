from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


SUPPORTED_PRINTER_TARGET_KINDS = frozenset(
    {"stdout", "file", "memory", "escpos_socket", "escpos_bytes_file"}
)
SUPPORTED_HARDWARE_PRINT_MODES = frozenset({"raster"})


def normalize_printer_target_kind(kind: str) -> str:
    normalized = kind.strip().lower()
    if normalized not in SUPPORTED_PRINTER_TARGET_KINDS:
        raise ValueError(f"Unsupported printer target kind: {kind!r}.")
    return normalized


def normalize_hardware_print_mode(mode: str) -> str:
    normalized = mode.strip().lower()
    if normalized not in SUPPORTED_HARDWARE_PRINT_MODES:
        raise ValueError(f"Unsupported hardware print mode: {mode!r}.")
    return normalized


@dataclass(slots=True, frozen=True)
class HardwarePrintOptions:
    mode: str = "raster"
    font_path: Path | None = None
    font_size: int = 18
    line_spacing: int = 4
    cut: bool = True


@dataclass(slots=True, frozen=True)
class PrinterTargetConfig:
    target_id: str
    kind: str
    profile_name: str | None = None
    hardware_options: HardwarePrintOptions = field(
        default_factory=HardwarePrintOptions
    )
    host: str | None = None
    port: int | None = None
    timeout_seconds: float = 5.0
    output_dir: Path | None = None
