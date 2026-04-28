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
class DeliveryEscposTcpConfig:
    host: str | None = None
    port: int = 9100
    timeout_seconds: float = 5.0
    encoding: str = "gb18030"
    cut: bool = True
    feed_lines: int = 3


@dataclass(slots=True, frozen=True)
class DeliveryConfig:
    default_adapter: str = "stdout"
    file: DeliveryFileConfig = field(default_factory=DeliveryFileConfig)
    escpos_tcp: DeliveryEscposTcpConfig = field(
        default_factory=DeliveryEscposTcpConfig
    )


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
class RuntimeConfig:
    source_path: Path
    rendering: RenderingConfig
    runtime: RuntimeOptionsConfig
    delivery: DeliveryConfig
    publication_slots: tuple[ConfiguredPublicationSlot, ...]
    scene_apps: tuple[ConfiguredSceneApp, ...]
