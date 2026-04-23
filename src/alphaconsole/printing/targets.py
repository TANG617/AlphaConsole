from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .profiles import PrinterProfile
from alphaconsole.rendering import RenderProfile


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
    feed_lines: int = 4


@dataclass(slots=True, frozen=True)
class PrinterTargetConfig:
    target_id: str
    kind: str
    printer_profile_name: str | None = None
    render_profile_name: str | None = None
    hardware_options: HardwarePrintOptions = field(
        default_factory=HardwarePrintOptions
    )
    host: str | None = None
    port: int | None = None
    timeout_seconds: float = 5.0
    output_dir: Path | None = None

    @property
    def profile_name(self) -> str | None:
        return self.render_profile_name


@dataclass(slots=True, frozen=True)
class PrinterTargetInspection:
    target_id: str
    kind: str
    printer_profile_name: str | None
    render_profile_name: str | None
    mode: str
    font_path: Path | None
    font_size: int
    line_spacing: int
    cut: bool
    feed_lines: int
    host: str | None
    port: int | None
    timeout_seconds: float | None
    output_dir: Path | None


@dataclass(slots=True, frozen=True)
class ResolvedPrinterTarget:
    config: PrinterTargetConfig
    printer_profile: PrinterProfile | None
    render_profile: RenderProfile
    inspection: PrinterTargetInspection


def inspect_printer_target(
    target: PrinterTargetConfig,
    *,
    render_profile_name: str,
) -> PrinterTargetInspection:
    return PrinterTargetInspection(
        target_id=target.target_id,
        kind=target.kind,
        printer_profile_name=target.printer_profile_name,
        render_profile_name=render_profile_name,
        mode=target.hardware_options.mode,
        font_path=target.hardware_options.font_path,
        font_size=target.hardware_options.font_size,
        line_spacing=target.hardware_options.line_spacing,
        cut=target.hardware_options.cut,
        feed_lines=target.hardware_options.feed_lines,
        host=target.host,
        port=target.port,
        timeout_seconds=target.timeout_seconds,
        output_dir=target.output_dir,
    )
