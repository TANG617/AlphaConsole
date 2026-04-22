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
        adapter_factory=adapter_factory,
    )
