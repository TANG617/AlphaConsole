from __future__ import annotations

from dataclasses import dataclass
from datetime import time
from pathlib import Path


class RuntimeConfigError(ValueError):
    """Raised when the current-phase runtime config is invalid."""


@dataclass(slots=True, frozen=True)
class RenderingConfig:
    default_profile: str = "receipt42"


@dataclass(slots=True, frozen=True)
class DeliveryConfig:
    default_adapter: str = "stdout"
    output_dir: str | None = None


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
    delivery: DeliveryConfig
    publication_slots: tuple[ConfiguredPublicationSlot, ...]
    scene_apps: tuple[ConfiguredSceneApp, ...]
