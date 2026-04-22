from __future__ import annotations

from dataclasses import dataclass, field
from datetime import time
from pathlib import Path


class RuntimeConfigError(ValueError):
    """Raised when the current-phase runtime config is invalid."""


@dataclass(slots=True, frozen=True)
class RenderingConfig:
    default_profile: str = "receipt42"


@dataclass(slots=True, frozen=True)
class RuntimeOptionsConfig:
    catchup_seconds: int = 60
    poll_interval_seconds: float = 30.0


@dataclass(slots=True, frozen=True)
class DeliveryFileConfig:
    output_dir: str | None = None


@dataclass(slots=True, frozen=True)
class DeliveryConfig:
    default_adapter: str = "stdout"
    file: DeliveryFileConfig = field(default_factory=DeliveryFileConfig)


@dataclass(slots=True, frozen=True)
class PrintingConfig:
    default_target: str | None = None


@dataclass(slots=True, frozen=True)
class ConfiguredPublicationSlot:
    slot_id: str
    name: str
    publish_time: time
    is_enabled: bool
    description: str | None = None
    recurrence_rule: str | None = None


@dataclass(slots=True, frozen=True)
class ConfiguredSceneApp:
    app_id: str
    name: str
    target_publication_slot_id: str
    scene_note: str | None
    checklist_items: tuple[str, ...]
    is_enabled: bool
    description: str | None = None
    scene_description: str | None = None
    recurrence_rule: str | None = None


@dataclass(slots=True, frozen=True)
class ConfiguredPrinterTarget:
    target_id: str
    kind: str
    profile: str | None = None
    mode: str | None = None
    font_path: str | None = None
    font_size: int = 18
    line_spacing: int = 4
    cut: bool = True
    host: str | None = None
    port: int | None = None
    timeout_seconds: float = 5.0
    output_dir: str | None = None


@dataclass(slots=True, frozen=True)
class RuntimeConfig:
    source_path: Path
    rendering: RenderingConfig
    runtime: RuntimeOptionsConfig
    delivery: DeliveryConfig
    printing: PrintingConfig
    publication_slots: tuple[ConfiguredPublicationSlot, ...]
    scene_apps: tuple[ConfiguredSceneApp, ...]
    printer_targets: tuple[ConfiguredPrinterTarget, ...]
