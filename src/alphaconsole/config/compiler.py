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
from alphaconsole.printing import (
    HardwarePrintOptions,
    PrinterTargetConfig,
    normalize_hardware_print_mode,
    normalize_printer_target_kind,
    resolve_printer_profile,
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
    printer_targets_by_id: dict[str, PrinterTargetConfig]
    default_profile: RenderProfile
    default_adapter_kind: str
    default_printer_target_id: str | None
    file_output_dir: Path | None
    runtime_catchup_seconds: int
    runtime_poll_interval_seconds: float


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
    file_output_dir = _resolve_output_dir(
        config.delivery.file.output_dir,
        base_dir=config.source_path.parent,
    )
    if default_adapter_kind == "file" and file_output_dir is None:
        raise RuntimeConfigError(
            "delivery.file.output_dir is required when default_adapter is 'file'."
        )

    printer_targets_by_id = _compile_printer_targets(
        config,
        base_dir=config.source_path.parent,
    )
    default_printer_target_id = config.printing.default_target
    if (
        default_printer_target_id is not None
        and default_printer_target_id not in printer_targets_by_id
    ):
        raise RuntimeConfigError(
            "printing.default_target references unknown target "
            f"{default_printer_target_id!r}."
        )

    slots_by_id: dict[str, PublicationSlot] = {}
    for configured_slot in config.publication_slots:
        if configured_slot.slot_id in slots_by_id:
            raise RuntimeConfigError(
                f"Duplicate publication slot id: {configured_slot.slot_id!r}."
            )
        if configured_slot.recurrence_rule not in (None, "daily"):
            raise RuntimeConfigError(
                "Unsupported recurrence_rule for publication slot "
                f"{configured_slot.slot_id!r}: {configured_slot.recurrence_rule!r}."
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
        printer_targets_by_id=printer_targets_by_id,
        default_profile=default_profile,
        default_adapter_kind=default_adapter_kind,
        default_printer_target_id=default_printer_target_id,
        file_output_dir=file_output_dir,
        runtime_catchup_seconds=config.runtime.catchup_seconds,
        runtime_poll_interval_seconds=config.runtime.poll_interval_seconds,
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


def _resolve_optional_path(value: str | None, *, base_dir: Path) -> Path | None:
    if value is None:
        return None

    path = Path(value)
    if not path.is_absolute():
        path = base_dir / path
    return path


def _compile_printer_targets(
    config: RuntimeConfig,
    *,
    base_dir: Path,
) -> dict[str, PrinterTargetConfig]:
    printer_targets_by_id: dict[str, PrinterTargetConfig] = {}
    for configured_target in config.printer_targets:
        if configured_target.target_id in printer_targets_by_id:
            raise RuntimeConfigError(
                f"Duplicate printer target id: {configured_target.target_id!r}."
            )

        kind = _normalize_target_kind(configured_target.kind)
        resolved_printer_profile = (
            _resolve_printer_profile(configured_target.printer_profile)
            if configured_target.printer_profile is not None
            else None
        )
        render_profile_name = (
            resolve_render_profile(configured_target.render_profile).name
            if configured_target.render_profile is not None
            else (
                resolved_printer_profile.recommended_render_profile_name
                if resolved_printer_profile is not None
                else None
            )
        )
        mode = _normalize_target_mode(configured_target.mode)
        output_dir = _resolve_output_dir(configured_target.output_dir, base_dir=base_dir)
        font_path = _resolve_optional_path(configured_target.font_path, base_dir=base_dir)

        if kind == "escpos_socket":
            if configured_target.host is None:
                raise RuntimeConfigError(
                    "printer target "
                    f"{configured_target.target_id!r} requires host for escpos_socket."
                )
            if configured_target.port is None:
                raise RuntimeConfigError(
                    "printer target "
                    f"{configured_target.target_id!r} requires port for escpos_socket."
                )
        if kind in {"escpos_socket", "escpos_bytes_file"} and resolved_printer_profile is None:
            raise RuntimeConfigError(
                "printer target "
                f"{configured_target.target_id!r} requires printer_profile for {kind}."
            )
        if kind in {"file", "escpos_bytes_file"} and output_dir is None:
            raise RuntimeConfigError(
                "printer target "
                f"{configured_target.target_id!r} requires output_dir for {kind}."
            )
        if (
            resolved_printer_profile is not None
            and configured_target.cut is True
            and not resolved_printer_profile.supports_cut
        ):
            raise RuntimeConfigError(
                "printer target "
                f"{configured_target.target_id!r} enables cut for a profile that does not support cut."
            )

        printer_targets_by_id[configured_target.target_id] = PrinterTargetConfig(
            target_id=configured_target.target_id,
            kind=kind,
            printer_profile_name=(
                resolved_printer_profile.profile_id
                if resolved_printer_profile is not None
                else None
            ),
            render_profile_name=render_profile_name,
            hardware_options=HardwarePrintOptions(
                mode=mode,
                font_path=font_path,
                font_size=(
                    configured_target.font_size
                    if configured_target.font_size is not None
                    else (
                        resolved_printer_profile.default_font_size
                        if resolved_printer_profile is not None
                        else 18
                    )
                ),
                line_spacing=(
                    configured_target.line_spacing
                    if configured_target.line_spacing is not None
                    else (
                        resolved_printer_profile.default_line_spacing
                        if resolved_printer_profile is not None
                        else 4
                    )
                ),
                cut=(
                    configured_target.cut
                    if configured_target.cut is not None
                    else (
                        resolved_printer_profile.default_cut
                        if resolved_printer_profile is not None
                        else True
                    )
                ),
                feed_lines=(
                    configured_target.feed_lines
                    if configured_target.feed_lines is not None
                    else (
                        resolved_printer_profile.line_feed_after_print
                        if resolved_printer_profile is not None
                        else 4
                    )
                ),
            ),
            host=configured_target.host,
            port=configured_target.port,
            timeout_seconds=configured_target.timeout_seconds,
            output_dir=output_dir,
        )

    return printer_targets_by_id


def _normalize_target_kind(kind: str) -> str:
    try:
        return normalize_printer_target_kind(kind)
    except ValueError as exc:
        raise RuntimeConfigError(str(exc)) from exc


def _normalize_target_mode(mode: str | None) -> str:
    normalized_mode = mode or "raster"
    try:
        return normalize_hardware_print_mode(normalized_mode)
    except ValueError as exc:
        raise RuntimeConfigError(str(exc)) from exc


def _resolve_printer_profile(profile_id: str):
    try:
        return resolve_printer_profile(profile_id)
    except ValueError as exc:
        raise RuntimeConfigError(str(exc)) from exc
