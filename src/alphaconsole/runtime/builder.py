from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from alphaconsole.application import PublicationService
from alphaconsole.config import (
    RuntimeConfigError,
    build_runtime_config_objects,
    load_runtime_config,
    normalize_adapter_kind,
)
from alphaconsole.domain import ContentApp, PublicationSlot
from alphaconsole.printing import (
    EscposTcpPrinterAdapter,
    FilePrinterAdapter,
    MemoryPrinterAdapter,
    PrintService,
    PrinterAdapter,
    StdoutPrinterAdapter,
)
from alphaconsole.rendering import RenderProfile
from alphaconsole.services import IssueAssembler


@dataclass(slots=True)
class AdapterFactory:
    file_output_dir: Path | None = None
    escpos_tcp_host: str | None = None
    escpos_tcp_port: int = 9100
    escpos_tcp_timeout_seconds: float = 5.0
    escpos_tcp_encoding: str = "gb18030"
    escpos_tcp_cut: bool = True
    escpos_tcp_feed_lines: int = 3

    def create(
        self,
        kind: str,
        *,
        output_dir: Path | None = None,
        printer_host: str | None = None,
        printer_port: int | None = None,
        printer_timeout_seconds: float | None = None,
        printer_encoding: str | None = None,
        printer_cut: bool | None = None,
        printer_feed_lines: int | None = None,
    ) -> PrinterAdapter:
        normalized_kind = normalize_adapter_kind(kind)
        if normalized_kind == "stdout":
            return StdoutPrinterAdapter()
        if normalized_kind == "memory":
            return MemoryPrinterAdapter()
        if normalized_kind == "file":
            resolved_output_dir = output_dir or self.file_output_dir
            if resolved_output_dir is None:
                raise RuntimeConfigError(
                    "File adapter requires an output directory."
                )
            return FilePrinterAdapter(output_dir=resolved_output_dir)
        if normalized_kind == "escpos_tcp":
            resolved_host = printer_host or self.escpos_tcp_host
            if resolved_host is None:
                raise RuntimeConfigError(
                    "ESC/POS TCP adapter requires --printer-host or "
                    "delivery.escpos_tcp.host."
                )
            return EscposTcpPrinterAdapter(
                host=resolved_host,
                port=(
                    self.escpos_tcp_port
                    if printer_port is None
                    else printer_port
                ),
                timeout_seconds=(
                    self.escpos_tcp_timeout_seconds
                    if printer_timeout_seconds is None
                    else printer_timeout_seconds
                ),
                encoding=printer_encoding or self.escpos_tcp_encoding,
                cut=(
                    self.escpos_tcp_cut
                    if printer_cut is None
                    else printer_cut
                ),
                feed_lines=(
                    self.escpos_tcp_feed_lines
                    if printer_feed_lines is None
                    else printer_feed_lines
                ),
            )

        raise RuntimeConfigError(f"Unsupported adapter kind: {kind!r}.")


@dataclass(slots=True)
class RuntimeBundle:
    issue_assembler: IssueAssembler
    print_service: PrintService
    publication_service: PublicationService
    slots_by_id: dict[str, PublicationSlot]
    apps_by_id: dict[str, ContentApp]
    default_profile: RenderProfile
    default_adapter_kind: str
    runtime_catchup_seconds: int
    runtime_poll_interval_seconds: float
    file_output_dir: Path | None
    escpos_tcp_host: str | None
    escpos_tcp_port: int
    escpos_tcp_timeout_seconds: float
    escpos_tcp_encoding: str
    escpos_tcp_cut: bool
    escpos_tcp_feed_lines: int
    adapter_factory: AdapterFactory


def build_runtime_from_config(path: Path) -> RuntimeBundle:
    runtime_config = load_runtime_config(path)
    compiled = build_runtime_config_objects(runtime_config)

    issue_assembler = IssueAssembler()
    print_service = PrintService()
    publication_service = PublicationService(
        assembler=issue_assembler,
        print_service=print_service,
    )
    adapter_factory = AdapterFactory(
        file_output_dir=compiled.file_output_dir,
        escpos_tcp_host=compiled.escpos_tcp_host,
        escpos_tcp_port=compiled.escpos_tcp_port,
        escpos_tcp_timeout_seconds=compiled.escpos_tcp_timeout_seconds,
        escpos_tcp_encoding=compiled.escpos_tcp_encoding,
        escpos_tcp_cut=compiled.escpos_tcp_cut,
        escpos_tcp_feed_lines=compiled.escpos_tcp_feed_lines,
    )

    return RuntimeBundle(
        issue_assembler=issue_assembler,
        print_service=print_service,
        publication_service=publication_service,
        slots_by_id=compiled.slots_by_id,
        apps_by_id=compiled.apps_by_id,
        default_profile=compiled.default_profile,
        default_adapter_kind=compiled.default_adapter_kind,
        runtime_catchup_seconds=compiled.runtime_catchup_seconds,
        runtime_poll_interval_seconds=compiled.runtime_poll_interval_seconds,
        file_output_dir=compiled.file_output_dir,
        escpos_tcp_host=compiled.escpos_tcp_host,
        escpos_tcp_port=compiled.escpos_tcp_port,
        escpos_tcp_timeout_seconds=compiled.escpos_tcp_timeout_seconds,
        escpos_tcp_encoding=compiled.escpos_tcp_encoding,
        escpos_tcp_cut=compiled.escpos_tcp_cut,
        escpos_tcp_feed_lines=compiled.escpos_tcp_feed_lines,
        adapter_factory=adapter_factory,
    )
