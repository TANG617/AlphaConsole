from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from alphaconsole.application import PublicationService
from alphaconsole.config import (
    RuntimeConfigError,
    build_runtime_config_objects,
    load_runtime_config,
    normalize_adapter_kind,
    resolve_render_profile,
)
from alphaconsole.domain import ContentApp, PublicationSlot
from alphaconsole.printing import (
    EscPosBytesFileAdapter,
    EscPosSocketPrinterAdapter,
    FilePrinterAdapter,
    MemoryPrinterAdapter,
    PrintService,
    PrinterAdapter,
    PrinterProfile,
    PrinterTargetInspection,
    PrinterTargetConfig,
    ResolvedPrinterTarget,
    StdoutPrinterAdapter,
    inspect_printer_target,
    resolve_printer_profile,
)
from alphaconsole.rendering import RenderProfile
from alphaconsole.services import IssueAssembler


@dataclass(slots=True)
class AdapterFactory:
    file_output_dir: Path | None = None

    def create(
        self,
        kind: str,
        *,
        output_dir: Path | None = None,
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

        raise RuntimeConfigError(f"Unsupported adapter kind: {kind!r}.")

    def create_for_target(
        self,
        target: ResolvedPrinterTarget,
        *,
        output_dir: Path | None = None,
    ) -> PrinterAdapter:
        config = target.config
        kind = config.kind
        if kind == "stdout":
            return StdoutPrinterAdapter(
                target_id=config.target_id,
                printer_profile_name=(
                    target.printer_profile.profile_id
                    if target.printer_profile is not None
                    else None
                ),
                render_profile_name=target.render_profile.name,
            )
        if kind == "memory":
            return MemoryPrinterAdapter(
                target_id=config.target_id,
                printer_profile_name=(
                    target.printer_profile.profile_id
                    if target.printer_profile is not None
                    else None
                ),
                render_profile_name=target.render_profile.name,
            )
        if kind == "file":
            resolved_output_dir = output_dir or config.output_dir or self.file_output_dir
            if resolved_output_dir is None:
                raise RuntimeConfigError(
                    f"Printer target {config.target_id!r} requires output_dir."
                )
            return FilePrinterAdapter(
                output_dir=resolved_output_dir,
                target_id=config.target_id,
                printer_profile_name=(
                    target.printer_profile.profile_id
                    if target.printer_profile is not None
                    else None
                ),
                render_profile_name=target.render_profile.name,
            )
        if kind == "escpos_socket":
            if config.host is None or config.port is None:
                raise RuntimeConfigError(
                    f"Printer target {config.target_id!r} requires host and port."
                )
            if target.printer_profile is None:
                raise RuntimeConfigError(
                    f"Printer target {config.target_id!r} requires a printer profile."
                )
            return EscPosSocketPrinterAdapter(
                target_id=config.target_id,
                host=config.host,
                port=config.port,
                printer_profile=target.printer_profile,
                printer_profile_name=target.printer_profile.profile_id,
                render_profile_name=target.render_profile.name,
                timeout_seconds=config.timeout_seconds,
                hardware_options=config.hardware_options,
            )
        if kind == "escpos_bytes_file":
            resolved_output_dir = output_dir or config.output_dir
            if resolved_output_dir is None:
                raise RuntimeConfigError(
                    f"Printer target {config.target_id!r} requires output_dir."
                )
            if target.printer_profile is None:
                raise RuntimeConfigError(
                    f"Printer target {config.target_id!r} requires a printer profile."
                )
            return EscPosBytesFileAdapter(
                target_id=config.target_id,
                output_dir=resolved_output_dir,
                printer_profile=target.printer_profile,
                printer_profile_name=target.printer_profile.profile_id,
                render_profile_name=target.render_profile.name,
                hardware_options=config.hardware_options,
            )

        raise RuntimeConfigError(f"Unsupported printer target kind: {kind!r}.")


@dataclass(slots=True)
class TargetResolver:
    printer_targets_by_id: dict[str, PrinterTargetConfig]
    default_target_id: str | None
    default_render_profile: RenderProfile

    def resolve(self, target_id: str | None = None) -> ResolvedPrinterTarget | None:
        selected_target_id = target_id or self.default_target_id
        if selected_target_id is None:
            return None
        return self.require(selected_target_id)

    def require(self, target_id: str) -> ResolvedPrinterTarget:
        try:
            config = self.printer_targets_by_id[target_id]
        except KeyError as exc:
            raise RuntimeConfigError(f"Unknown target_id: {target_id!r}.") from exc

        printer_profile = (
            resolve_printer_profile(config.printer_profile_name)
            if config.printer_profile_name is not None
            else None
        )
        render_profile_name = (
            config.render_profile_name
            or (
                printer_profile.recommended_render_profile_name
                if printer_profile is not None
                else self.default_render_profile.name
            )
        )
        render_profile = resolve_render_profile(render_profile_name)
        inspection = inspect_printer_target(
            config,
            render_profile_name=render_profile.name,
        )
        return ResolvedPrinterTarget(
            config=config,
            printer_profile=printer_profile,
            render_profile=render_profile,
            inspection=inspection,
        )


@dataclass(slots=True)
class RuntimeBundle:
    issue_assembler: IssueAssembler
    print_service: PrintService
    publication_service: PublicationService
    slots_by_id: dict[str, PublicationSlot]
    apps_by_id: dict[str, ContentApp]
    printer_targets_by_id: dict[str, PrinterTargetConfig]
    target_resolver: TargetResolver
    default_profile: RenderProfile
    default_adapter_kind: str
    default_printer_target_id: str | None
    runtime_catchup_seconds: int
    runtime_poll_interval_seconds: float
    file_output_dir: Path | None
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
    adapter_factory = AdapterFactory(file_output_dir=compiled.file_output_dir)
    target_resolver = TargetResolver(
        printer_targets_by_id=compiled.printer_targets_by_id,
        default_target_id=compiled.default_printer_target_id,
        default_render_profile=compiled.default_profile,
    )

    return RuntimeBundle(
        issue_assembler=issue_assembler,
        print_service=print_service,
        publication_service=publication_service,
        slots_by_id=compiled.slots_by_id,
        apps_by_id=compiled.apps_by_id,
        printer_targets_by_id=compiled.printer_targets_by_id,
        target_resolver=target_resolver,
        default_profile=compiled.default_profile,
        default_adapter_kind=compiled.default_adapter_kind,
        default_printer_target_id=compiled.default_printer_target_id,
        runtime_catchup_seconds=compiled.runtime_catchup_seconds,
        runtime_poll_interval_seconds=compiled.runtime_poll_interval_seconds,
        file_output_dir=compiled.file_output_dir,
        adapter_factory=adapter_factory,
    )
