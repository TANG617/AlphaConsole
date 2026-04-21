from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from alphaconsole.domain import (
    ContentApp,
    MergePolicy,
    PublicationSlot,
    SceneApp,
    TriggerMode,
)
from alphaconsole.rendering import RECEIPT_32, RECEIPT_42, RenderProfile

from .models import RuntimeConfig, RuntimeConfigError

_PROFILE_ALIASES = {
    "receipt32": RECEIPT_32,
    "receipt_32": RECEIPT_32,
    "receipt42": RECEIPT_42,
    "receipt_42": RECEIPT_42,
}
_SUPPORTED_ADAPTER_KINDS = {"stdout", "file", "memory"}


@dataclass(slots=True, frozen=True)
class CompiledRuntimeConfig:
    slots_by_id: dict[str, PublicationSlot]
    apps_by_id: dict[str, ContentApp]
    default_profile: RenderProfile
    default_adapter_kind: str
    default_output_dir: Path | None


def resolve_render_profile(name: str) -> RenderProfile:
    normalized = _normalize_profile_name(name)
    try:
        return _PROFILE_ALIASES[normalized]
    except KeyError as exc:
        raise RuntimeConfigError(f"Unsupported render profile: {name!r}.") from exc


def normalize_adapter_kind(kind: str) -> str:
    normalized = kind.strip().lower()
    if normalized not in _SUPPORTED_ADAPTER_KINDS:
        raise RuntimeConfigError(f"Unsupported adapter kind: {kind!r}.")
    return normalized


def compile_runtime_config(
    config: RuntimeConfig,
    *,
    compiled_at: datetime | None = None,
) -> CompiledRuntimeConfig:
    resolved_at = compiled_at or datetime.now()
    default_profile = resolve_render_profile(config.rendering.default_profile)
    default_adapter_kind = normalize_adapter_kind(config.delivery.default_adapter)
    default_output_dir = _resolve_output_dir(
        config.delivery.output_dir,
        base_dir=config.source_path.parent,
    )

    slots_by_id: dict[str, PublicationSlot] = {}
    for configured_slot in config.publication_slots:
        if configured_slot.slot_id in slots_by_id:
            raise RuntimeConfigError(
                f"Duplicate publication slot id: {configured_slot.slot_id!r}."
            )
        slots_by_id[configured_slot.slot_id] = PublicationSlot(
            slot_id=configured_slot.slot_id,
            name=configured_slot.name,
            description=configured_slot.description,
            publish_time=configured_slot.publish_time,
            recurrence_rule=configured_slot.recurrence_rule,
            is_enabled=configured_slot.is_enabled,
            created_at=resolved_at,
            updated_at=resolved_at,
        )

    apps_by_id: dict[str, ContentApp] = {}
    for configured_app in config.scene_apps:
        if configured_app.app_id in apps_by_id:
            raise RuntimeConfigError(
                f"Duplicate scene app id: {configured_app.app_id!r}."
            )
        if configured_app.target_publication_slot_id not in slots_by_id:
            raise RuntimeConfigError(
                "Scene app "
                f"{configured_app.app_id!r} references unknown slot "
                f"{configured_app.target_publication_slot_id!r}."
            )

        apps_by_id[configured_app.app_id] = SceneApp(
            app_id=configured_app.app_id,
            app_type="scene",
            name=configured_app.name,
            description=configured_app.description,
            target_publication_slot_id=configured_app.target_publication_slot_id,
            prepare_at=None,
            default_trigger_mode=TriggerMode.SCHEDULED,
            default_merge_policy=MergePolicy.MERGEABLE,
            default_template_type="scene.default",
            expiration_policy=None,
            is_enabled=configured_app.is_enabled,
            created_at=resolved_at,
            updated_at=resolved_at,
            scene_note=configured_app.scene_note,
            checklist_items=configured_app.checklist_items,
            scene_description=configured_app.scene_description,
            recurrence_rule=configured_app.recurrence_rule,
        )

    return CompiledRuntimeConfig(
        slots_by_id=slots_by_id,
        apps_by_id=apps_by_id,
        default_profile=default_profile,
        default_adapter_kind=default_adapter_kind,
        default_output_dir=default_output_dir,
    )


def build_runtime_config_objects(
    config: RuntimeConfig,
    *,
    compiled_at: datetime | None = None,
) -> CompiledRuntimeConfig:
    return compile_runtime_config(config, compiled_at=compiled_at)


def _normalize_profile_name(name: str) -> str:
    return name.strip().lower().replace("-", "").replace(" ", "")


def _resolve_output_dir(value: str | None, *, base_dir: Path) -> Path | None:
    if value is None:
        return None

    path = Path(value)
    if not path.is_absolute():
        path = base_dir / path
    return path
