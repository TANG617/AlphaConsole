from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from datetime import time
import tomllib

from .models import (
    ConfiguredPublicationSlot,
    ConfiguredSceneApp,
    DeliveryConfig,
    RenderingConfig,
    RuntimeConfig,
    RuntimeConfigError,
)


def load_runtime_config(path: Path) -> RuntimeConfig:
    try:
        with path.open("rb") as stream:
            data = tomllib.load(stream)
    except FileNotFoundError as exc:
        raise RuntimeConfigError(f"Config file not found: {path}") from exc
    except tomllib.TOMLDecodeError as exc:
        raise RuntimeConfigError(f"Invalid TOML in {path}: {exc}") from exc

    rendering_data = _optional_table(data, "rendering")
    delivery_data = _optional_table(data, "delivery")
    publication_slots = _optional_array_of_tables(data, "publication_slots")
    scene_apps = _optional_array_of_tables(data, "scene_apps")

    rendering = RenderingConfig(
        default_profile=_optional_string(
            rendering_data,
            "default_profile",
            context="rendering.default_profile",
            default="receipt42",
        )
    )
    delivery = DeliveryConfig(
        default_adapter=_optional_string(
            delivery_data,
            "default_adapter",
            context="delivery.default_adapter",
            default="stdout",
        ),
        output_dir=_optional_string(
            delivery_data,
            "output_dir",
            context="delivery.output_dir",
            default=None,
        ),
    )

    return RuntimeConfig(
        source_path=path,
        rendering=rendering,
        delivery=delivery,
        publication_slots=tuple(
            _parse_publication_slot(item, index)
            for index, item in enumerate(publication_slots, start=1)
        ),
        scene_apps=tuple(
            _parse_scene_app(item, index)
            for index, item in enumerate(scene_apps, start=1)
        ),
    )


def _parse_publication_slot(
    data: Mapping[str, object], index: int
) -> ConfiguredPublicationSlot:
    context = f"publication_slots[{index}]"
    return ConfiguredPublicationSlot(
        slot_id=_required_string(data, "slot_id", context=context),
        name=_required_string(data, "name", context=context),
        publish_time=_required_time(data, "publish_time", context=context),
        is_enabled=_required_bool(data, "is_enabled", context=context),
        description=_optional_string(data, "description", context=f"{context}.description"),
        recurrence_rule=_optional_string(
            data,
            "recurrence_rule",
            context=f"{context}.recurrence_rule",
        ),
    )


def _parse_scene_app(data: Mapping[str, object], index: int) -> ConfiguredSceneApp:
    context = f"scene_apps[{index}]"
    scene_note = _optional_string(data, "scene_note", context=f"{context}.scene_note")
    checklist_items = _optional_string_list(
        data,
        "checklist_items",
        context=f"{context}.checklist_items",
    )
    if scene_note is None and not checklist_items:
        raise RuntimeConfigError(
            f"{context} requires scene_note or checklist_items."
        )

    return ConfiguredSceneApp(
        app_id=_required_string(data, "app_id", context=context),
        name=_required_string(data, "name", context=context),
        target_publication_slot_id=_required_string(
            data,
            "target_publication_slot_id",
            context=context,
        ),
        scene_note=scene_note,
        checklist_items=tuple(checklist_items),
        is_enabled=_required_bool(data, "is_enabled", context=context),
        description=_optional_string(data, "description", context=f"{context}.description"),
        scene_description=_optional_string(
            data,
            "scene_description",
            context=f"{context}.scene_description",
        ),
        recurrence_rule=_optional_string(
            data,
            "recurrence_rule",
            context=f"{context}.recurrence_rule",
        ),
    )


def _optional_table(data: Mapping[str, object], key: str) -> Mapping[str, object]:
    value = data.get(key, {})
    if not isinstance(value, Mapping):
        raise RuntimeConfigError(f"{key} must be a TOML table.")
    return value


def _optional_array_of_tables(
    data: Mapping[str, object], key: str
) -> Sequence[Mapping[str, object]]:
    value = data.get(key, [])
    if not isinstance(value, list):
        raise RuntimeConfigError(f"{key} must be an array of tables.")
    for index, item in enumerate(value, start=1):
        if not isinstance(item, Mapping):
            raise RuntimeConfigError(f"{key}[{index}] must be a TOML table.")
    return value


def _required_string(data: Mapping[str, object], key: str, *, context: str) -> str:
    value = data.get(key)
    if not isinstance(value, str):
        raise RuntimeConfigError(f"{context}.{key} must be a non-empty string.")
    normalized = value.strip()
    if not normalized:
        raise RuntimeConfigError(f"{context}.{key} must be a non-empty string.")
    return normalized


def _optional_string(
    data: Mapping[str, object],
    key: str,
    *,
    context: str,
    default: str | None = None,
) -> str | None:
    value = data.get(key, default)
    if value is None:
        return None
    if not isinstance(value, str):
        raise RuntimeConfigError(f"{context} must be a string.")
    normalized = value.strip()
    return normalized or None


def _required_bool(data: Mapping[str, object], key: str, *, context: str) -> bool:
    value = data.get(key)
    if not isinstance(value, bool):
        raise RuntimeConfigError(f"{context}.{key} must be a boolean.")
    return value


def _required_time(data: Mapping[str, object], key: str, *, context: str) -> time:
    value = data.get(key)
    if not isinstance(value, str):
        raise RuntimeConfigError(f"{context}.{key} must be an HH:MM string.")
    try:
        return time.fromisoformat(value)
    except ValueError as exc:
        raise RuntimeConfigError(
            f"{context}.{key} must be an HH:MM string."
        ) from exc


def _optional_string_list(
    data: Mapping[str, object],
    key: str,
    *,
    context: str,
) -> list[str]:
    value = data.get(key, [])
    if not isinstance(value, list):
        raise RuntimeConfigError(f"{context} must be a list of strings.")

    normalized: list[str] = []
    for index, item in enumerate(value, start=1):
        if not isinstance(item, str):
            raise RuntimeConfigError(f"{context}[{index}] must be a string.")
        stripped = item.strip()
        if not stripped:
            raise RuntimeConfigError(f"{context}[{index}] must not be empty.")
        normalized.append(stripped)
    return normalized
